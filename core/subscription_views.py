# -*- coding: utf-8 -*-
"""
구독 관리 API Views

구독 플랜 조회, 구독 변경, 사용량 조회 등
"""

import logging
from datetime import timedelta
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import SubscriptionPlan, UserSubscription
from .serializers import (
    SubscriptionPlanSerializer,
    UserSubscriptionSerializer,
    SubscriptionChangeRequestSerializer,
    UsageStatsResponseSerializer,
    ModelAvailabilityResponseSerializer
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


class SubscriptionPlanViewSet(viewsets.ReadOnlyModelViewSet):
    """구독 플랜 조회 API"""
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = []  # 모든 사용자가 조회 가능


class UserSubscriptionViewSet(viewsets.ModelViewSet):
    """사용자 구독 관리 API"""
    serializer_class = UserSubscriptionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """현재 사용자의 구독만 조회"""
        return UserSubscription.objects.filter(user=self.request.user)
    
    def get_object(self):
        """사용자의 현재 구독 가져오기"""
        subscription, _ = UserSubscription.objects.get_or_create(
            user=self.request.user,
            defaults={'plan': get_or_create_free_plan()}
        )
        return subscription
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """현재 사용자의 구독 정보 조회"""
        subscription, created = UserSubscription.objects.get_or_create(
            user=request.user,
            defaults={'plan': get_or_create_free_plan()}
        )
        serializer = self.get_serializer(subscription)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def change(self, request):
        """구독 플랜 변경"""
        serializer = SubscriptionChangeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        plan_id = serializer.validated_data['plan_id']
        
        try:
            new_plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return Response(
                {'error': '존재하지 않거나 비활성화된 플랜입니다.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 현재 구독 가져오기 또는 생성
        subscription, created = UserSubscription.objects.get_or_create(
            user=request.user,
            defaults={'plan': get_or_create_free_plan()}
        )
        
        # 무료 플랜으로 변경 시 즉시 활성화, 유료 플랜은 결제 필요
        if new_plan.plan_type == 'free':
            subscription.plan = new_plan
            subscription.is_active = True
            subscription.start_date = timezone.now()
            subscription.end_date = None
            subscription.current_usage = 0
            subscription.bonus_tokens = 0
            subscription.save()
            
            logger.info(f"사용자 {request.user.username} 구독을 {new_plan.display_name}으로 변경")
            
            return Response({
                'message': f'구독이 {new_plan.display_name}으로 변경되었습니다.',
                'subscription': UserSubscriptionSerializer(subscription).data
            })
        else:
            # 유료 플랜은 결제 요청 필요
            return Response(
                {'error': '유료 플랜은 결제가 필요합니다. 결제 페이지로 이동하세요.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def usage(self, request):
        """사용량 통계 조회"""
        subscription, _ = UserSubscription.objects.get_or_create(
            user=request.user,
            defaults={'plan': get_or_create_free_plan()}
        )
        
        total_available = subscription.total_available_tokens
        remaining = subscription.remaining_tokens
        usage_percentage = (subscription.current_usage / total_available * 100) if total_available > 0 else 0
        
        stats = {
            'current_usage': subscription.current_usage,
            'monthly_limit': subscription.plan.monthly_limit,
            'bonus_tokens': subscription.bonus_tokens,
            'total_available': total_available,
            'remaining': remaining,
            'usage_percentage': round(usage_percentage, 2)
        }
        
        serializer = UsageStatsResponseSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def available_models(self, request):
        """사용 가능한 모델 목록 조회"""
        subscription, _ = UserSubscription.objects.get_or_create(
            user=request.user,
            defaults={'plan': get_or_create_free_plan()}
        )
        
        allowed_models = subscription.plan.allowed_models
        available_models = []
        
        # 모든 모델 목록 (현재 지원하는 모델들)
        all_models = [
            'gpt-5-nano',
            'gpt-5-mini',
            'gpt-5',
            'gpt-4.1',
            'gpt-4.1-mini'
        ]
        
        for model in all_models:
            is_available = model in allowed_models
            reason = None
            if not is_available:
                reason = f'현재 {subscription.plan.display_name} 플랜에서는 사용할 수 없는 모델입니다.'
            
            available_models.append({
                'model_name': model,
                'is_available': is_available,
                'reason': reason
            })
        
        serializer = ModelAvailabilityResponseSerializer(available_models, many=True)
        return Response(serializer.data)

