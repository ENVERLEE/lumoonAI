# -*- coding: utf-8 -*-
"""
친구 초대 관련 API Views

초대 코드 생성, 검증, 사용 및 보너스 적용
"""

import logging
import secrets
from datetime import timedelta
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import InviteCode, UserSubscription, SubscriptionPlan, CustomUser
from .serializers import (
    InviteCodeSerializer,
    InviteCodeCreateRequestSerializer,
    InviteCodeUseRequestSerializer,
    InviteCodeUseResponseSerializer
)

logger = logging.getLogger(__name__)


def get_or_create_free_plan():
    """무료 플랜 가져오기 또는 생성 (플랜이 없을 경우 자동 생성)"""
    return SubscriptionPlan.objects.get_or_create(
        name='free',
        defaults={
            'display_name': '무료 플랜',
            'plan_type': 'free',
            'price': 0.00,
            'monthly_limit': 300000,
            'allowed_models': ['gpt-5-nano'],
            'is_active': True,
            'description': '무료로 제공되는 기본 플랜입니다. gpt-5-nano 모델만 사용 가능합니다.'
        }
    )[0]


def generate_invite_code():
    """고유한 초대 코드 생성"""
    while True:
        code = secrets.token_urlsafe(12)[:12].upper().replace('-', '').replace('_', '')
        if not InviteCode.objects.filter(code=code).exists():
            return code


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_invite_code(request):
    """
    초대 코드 생성 API
    
    POST /api/invite/create/
    {
        "expires_in_days": 30 (선택)
    }
    """
    serializer = InviteCodeCreateRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    expires_in_days = serializer.validated_data.get('expires_in_days', 30)
    expires_at = None
    if expires_in_days:
        expires_at = timezone.now() + timedelta(days=expires_in_days)
    
    # 고유한 코드 생성
    code = generate_invite_code()
    
    # 초대 코드 생성
    invite_code = InviteCode.objects.create(
        code=code,
        inviter=request.user,
        expires_at=expires_at
    )
    
    logger.info(f"초대 코드 생성: {code} by {request.user.username}")
    
    serializer = InviteCodeSerializer(invite_code)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_invite_codes(request):
    """
    내가 생성한 초대 코드 목록 조회
    
    GET /api/invite/list/
    """
    invite_codes = InviteCode.objects.filter(
        inviter=request.user
    ).order_by('-created_at')
    
    serializer = InviteCodeSerializer(invite_codes, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def use_invite_code(request):
    """
    초대 코드 사용 API
    
    POST /api/invite/use/
    {
        "code": "ABC123XYZ"
    }
    """
    serializer = InviteCodeUseRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    code = serializer.validated_data['code'].upper().strip()
    
    try:
        invite_code = InviteCode.objects.get(code=code)
    except InviteCode.DoesNotExist:
        return Response(
            {'error': '유효하지 않은 초대 코드입니다.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # 이미 사용된 코드
    if invite_code.is_used:
        return Response(
            {'error': '이미 사용된 초대 코드입니다.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # 만료 확인
    if invite_code.expires_at and invite_code.expires_at < timezone.now():
        return Response(
            {'error': '만료된 초대 코드입니다.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # 자기 자신의 코드 사용 불가
    if invite_code.inviter == request.user:
        return Response(
            {'error': '자신이 생성한 초대 코드는 사용할 수 없습니다.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # 초대 코드 사용 처리
    invite_code.is_used = True
    invite_code.used_at = timezone.now()
    invite_code.invitee = request.user
    invite_code.save()
    
    # 보너스 적용
    # 1. 피초대자: 무료 플랜 기준으로 1개월치 토큰 제공 (30만 토큰)
    free_plan = get_or_create_free_plan()
    subscription, created = UserSubscription.objects.get_or_create(
        user=request.user,
        defaults={'plan': free_plan}
    )
    
    # 보너스 토큰 추가 (무료 플랜 월 한도)
    bonus_tokens = free_plan.monthly_limit  # 30만 토큰
    subscription.bonus_tokens += bonus_tokens
    subscription.save()
    
    # 2. 초대자: 현재 플랜의 월 한도만큼 보너스 토큰 추가
    inviter_subscription, _ = UserSubscription.objects.get_or_create(
        user=invite_code.inviter,
        defaults={'plan': free_plan}
    )
    inviter_bonus = inviter_subscription.plan.monthly_limit
    inviter_subscription.bonus_tokens += inviter_bonus
    inviter_subscription.save()
    
    logger.info(
        f"초대 코드 사용: {code} by {request.user.username}, "
        f"초대자: {invite_code.inviter.username}"
    )
    
    return Response({
        'success': True,
        'message': f'초대 코드가 사용되었습니다! 보너스 토큰 {bonus_tokens:,}개가 지급되었습니다.',
        'bonus_tokens': bonus_tokens
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_invite_stats(request):
    """
    초대 통계 조회
    
    GET /api/invite/stats/
    """
    total_invites = InviteCode.objects.filter(inviter=request.user).count()
    used_invites = InviteCode.objects.filter(
        inviter=request.user,
        is_used=True
    ).count()
    
    # 초대를 통해 받은 보너스 토큰 계산
    received_bonus = 0
    if hasattr(request.user, 'subscription'):
        # 실제로는 초대 시 추가된 보너스를 추적해야 하지만,
        # 간단하게 현재 보너스 토큰으로 표시
        received_bonus = request.user.subscription.bonus_tokens
    
    return Response({
        'total_invites': total_invites,
        'used_invites': used_invites,
        'pending_invites': total_invites - used_invites,
        'received_bonus_tokens': received_bonus
    })

