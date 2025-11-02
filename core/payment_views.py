# -*- coding: utf-8 -*-
"""
결제 관련 API Views

수동 승인 방식의 결제 요청 관리
"""

import logging
import os
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from .models import SubscriptionPlan, UserSubscription, PaymentRequest
from .serializers import (
    PaymentRequestSerializer,
    PaymentRequestCreateSerializer,
    PaymentDepositConfirmSerializer,
    PaymentApprovalSerializer
)

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_account_info(request):
    """
    계좌 정보 조회 API
    
    GET /api/payment/account/
    """
    # .env 파일에서 계좌 정보 가져오기
    account_info = {
        'bank_name': os.getenv('PAYMENT_BANK_NAME', '은행명'),
        'account_number': os.getenv('PAYMENT_ACCOUNT_NUMBER', '계좌번호'),
        'account_holder': os.getenv('PAYMENT_ACCOUNT_HOLDER', '예금주명'),
    }
    
    return Response(account_info)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_payment_request(request):
    """
    결제 요청 생성 API
    
    POST /api/payment/request/
    {
        "plan_id": "uuid"
    }
    """
    serializer = PaymentRequestCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    plan_id = serializer.validated_data['plan_id']
    
    try:
        plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
    except SubscriptionPlan.DoesNotExist:
        return Response(
            {'error': '존재하지 않거나 비활성화된 플랜입니다.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # 무료 플랜은 결제 불필요
    if plan.plan_type == 'free':
        return Response(
            {'error': '무료 플랜은 결제가 필요하지 않습니다.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # 이미 진행 중인 결제 요청이 있는지 확인
    existing_request = PaymentRequest.objects.filter(
        user=request.user,
        plan=plan,
        status__in=['pending', 'deposit_confirmed']
    ).first()
    
    if existing_request:
        return Response(
            {'error': '이미 진행 중인 결제 요청이 있습니다.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # 결제 요청 생성
    payment_request = PaymentRequest.objects.create(
        user=request.user,
        plan=plan,
        status='pending'
    )
    
    logger.info(f"결제 요청 생성: {request.user.username} - {plan.display_name}")
    
    serializer = PaymentRequestSerializer(payment_request)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_deposit(request):
    """
    입금 완료 신청 API
    
    POST /api/payment/deposit/confirm/
    {
        "payment_request_id": "uuid"
    }
    """
    serializer = PaymentDepositConfirmSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    payment_request_id = serializer.validated_data['payment_request_id']
    
    try:
        payment_request = PaymentRequest.objects.get(
            id=payment_request_id,
            user=request.user
        )
    except PaymentRequest.DoesNotExist:
        return Response(
            {'error': '결제 요청을 찾을 수 없습니다.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # 이미 승인되었거나 거부된 경우
    if payment_request.status == 'approved':
        return Response(
            {'error': '이미 승인된 결제 요청입니다.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    if payment_request.status == 'rejected':
        return Response(
            {'error': '거부된 결제 요청입니다.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # 입금 완료 처리
    payment_request.deposit_confirmed = True
    payment_request.deposit_confirmed_at = timezone.now()
    payment_request.status = 'deposit_confirmed'
    payment_request.save()
    
    logger.info(f"입금 완료 신청: {request.user.username} - {payment_request.plan.display_name}")
    
    serializer = PaymentRequestSerializer(payment_request)
    return Response({
        'message': '입금 완료 신청이 처리되었습니다. 관리자 승인을 기다려주세요.',
        'payment_request': serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_payment_status(request):
    """
    현재 사용자의 결제 요청 상태 조회
    
    GET /api/payment/status/
    """
    payment_requests = PaymentRequest.objects.filter(
        user=request.user
    ).order_by('-requested_at')[:5]  # 최근 5개만
    
    serializer = PaymentRequestSerializer(payment_requests, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def approve_payment(request):
    """
    관리자 결제 승인 API
    
    POST /api/payment/admin/approve/
    {
        "payment_request_id": "uuid",
        "approve": true/false,
        "notes": "메모 (선택)"
    }
    """
    serializer = PaymentApprovalSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    payment_request_id = serializer.validated_data['payment_request_id']
    approve = serializer.validated_data['approve']
    notes = serializer.validated_data.get('notes', '')
    
    try:
        payment_request = PaymentRequest.objects.get(id=payment_request_id)
    except PaymentRequest.DoesNotExist:
        return Response(
            {'error': '결제 요청을 찾을 수 없습니다.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # 이미 처리된 경우
    if payment_request.status in ['approved', 'rejected']:
        return Response(
            {'error': f'이미 {payment_request.get_status_display()} 처리된 결제 요청입니다.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if approve:
        # 승인 처리
        payment_request.approved = True
        payment_request.approved_by = request.user
        payment_request.approved_at = timezone.now()
        payment_request.status = 'approved'
        payment_request.notes = notes
        payment_request.save()
        
        # UserSubscription 활성화
        subscription, created = UserSubscription.objects.get_or_create(
            user=payment_request.user,
            defaults={'plan': payment_request.plan}
        )
        
        subscription.plan = payment_request.plan
        subscription.is_active = True
        subscription.start_date = timezone.now()
        subscription.end_date = timezone.now() + timedelta(days=30)
        subscription.current_usage = 0
        subscription.last_reset_date = timezone.now()
        subscription.save()
        
        logger.info(
            f"결제 승인: {payment_request.user.username} - "
            f"{payment_request.plan.display_name} by {request.user.username}"
        )
        
        return Response({
            'message': '결제가 승인되었고 구독이 활성화되었습니다.',
            'payment_request': PaymentRequestSerializer(payment_request).data,
            'subscription': {
                'is_active': subscription.is_active,
                'plan': payment_request.plan.display_name,
                'end_date': subscription.end_date.isoformat() if subscription.end_date else None
            }
        })
    else:
        # 거부 처리
        payment_request.approved = False
        payment_request.approved_by = request.user
        payment_request.status = 'rejected'
        payment_request.notes = notes
        payment_request.save()
        
        logger.info(
            f"결제 거부: {payment_request.user.username} - "
            f"{payment_request.plan.display_name} by {request.user.username}"
        )
        
        return Response({
            'message': '결제 요청이 거부되었습니다.',
            'payment_request': PaymentRequestSerializer(payment_request).data
        })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_pending_payments(request):
    """
    관리자용 결제 대기 목록 조회
    
    GET /api/payment/admin/pending/
    """
    pending_requests = PaymentRequest.objects.filter(
        status__in=['pending', 'deposit_confirmed']
    ).order_by('-requested_at')
    
    serializer = PaymentRequestSerializer(pending_requests, many=True)
    return Response(serializer.data)

