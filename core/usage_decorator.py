# -*- coding: utf-8 -*-
"""
사용량 확인 데코레이터 및 유틸리티 함수

LLM 호출 전 사용량 확인 및 모델 권한 확인
"""

import logging
from functools import wraps
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from .models import UserSubscription, SubscriptionPlan

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


class UsageLimitExceeded(Exception):
    """사용량 제한 초과 예외"""
    pass


class ModelNotAllowed(Exception):
    """모델 사용 권한 없음 예외"""
    pass


def get_user_subscription(user):
    """사용자의 구독 정보 가져오기"""
    if not user or not user.is_authenticated:
        # 익명 사용자는 무료 플랜
        free_plan = get_or_create_free_plan()
        return None, free_plan
    
    subscription, created = UserSubscription.objects.get_or_create(
        user=user,
        defaults={'plan': get_or_create_free_plan()}
    )
    return subscription, subscription.plan


def get_monthly_usage(user):
    """사용자의 현재 월 사용량 조회"""
    subscription, plan = get_user_subscription(user)
    if subscription:
        return subscription.current_usage
    return 0


def check_usage_limit(user, tokens_needed):
    """
    사용량 제한 확인
    
    Args:
        user: 사용자 객체
        tokens_needed: 필요한 토큰 수
    
    Raises:
        UsageLimitExceeded: 사용량 초과 시
    """
    subscription, plan = get_user_subscription(user)
    
    if not plan:
        raise UsageLimitExceeded("구독 플랜을 찾을 수 없습니다.")
    
    # 익명 사용자도 무료 플랜으로 처리
    if subscription:
        monthly_limit = subscription.plan.monthly_limit
        bonus_tokens = subscription.bonus_tokens
        current_usage = subscription.current_usage
    else:
        # 익명 사용자는 무료 플랜 기준
        monthly_limit = plan.monthly_limit
        bonus_tokens = 0
        current_usage = 0
    
    total_available = monthly_limit + bonus_tokens
    
    if current_usage + tokens_needed > total_available:
        remaining = max(0, total_available - current_usage)
        raise UsageLimitExceeded(
            f"사용량 제한을 초과했습니다. "
            f"남은 토큰: {remaining:,} / 필요 토큰: {tokens_needed:,}"
        )


def can_use_model(user, model_name):
    """
    모델 사용 권한 확인
    
    Args:
        user: 사용자 객체
        model_name: 모델 이름 (예: 'gpt-5-nano')
    
    Returns:
        bool: 사용 가능 여부
    """
    subscription, plan = get_user_subscription(user)
    
    if not plan:
        return False
    
    # 무료 플랜은 gpt-5-nano만 사용 가능
    if plan.plan_type == 'free':
        return model_name == 'gpt-5-nano'
    
    # 허용된 모델 리스트 확인
    allowed_models = plan.allowed_models
    return model_name in allowed_models


def require_usage_limit(view_func):
    """
    사용량 제한 확인 데코레이터
    
    뷰 함수에서 tokens_needed 파라미터를 사용하여 사용량 확인
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # tokens_needed가 kwargs에 있는 경우 확인
        tokens_needed = kwargs.get('tokens_needed', 0)
        
        if tokens_needed > 0 and request.user.is_authenticated:
            try:
                check_usage_limit(request.user, tokens_needed)
            except UsageLimitExceeded as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        return view_func(request, *args, **kwargs)
    return wrapper


def require_model_permission(model_name):
    """
    모델 사용 권한 확인 데코레이터 팩토리
    
    사용법:
    @require_model_permission('gpt-5-mini')
    def my_view(request):
        ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not can_use_model(request.user, model_name):
                return Response(
                    {
                        'error': f'{model_name} 모델을 사용할 권한이 없습니다. '
                                f'구독 플랜을 확인해주세요.'
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def update_usage(user, tokens_used, model_name=None):
    """
    사용량 업데이트
    
    Args:
        user: 사용자 객체
        tokens_used: 사용한 토큰 수
        model_name: 사용한 모델 이름 (선택적, 통계용)
    """
    if not user or not user.is_authenticated:
        # 익명 사용자는 사용량 추적하지 않음
        return
    
    subscription, plan = get_user_subscription(user)
    if not subscription:
        return
    
    # 사용량 업데이트
    subscription.current_usage += tokens_used
    subscription.save()
    
    # UsageRecord 업데이트 (통계용)
    if model_name:
        from .models import UsageRecord
        now = timezone.now()
        usage_record, _ = UsageRecord.objects.get_or_create(
            user=user,
            subscription=subscription,
            year=now.year,
            month=now.month,
            defaults={'total_tokens': 0, 'tokens_by_model': {}}
        )
        
        usage_record.total_tokens += tokens_used
        tokens_by_model = usage_record.tokens_by_model or {}
        tokens_by_model[model_name] = tokens_by_model.get(model_name, 0) + tokens_used
        usage_record.tokens_by_model = tokens_by_model
        usage_record.save()
    
    logger.debug(
        f"사용량 업데이트: {user.username} - "
        f"{tokens_used:,} 토큰 사용 (총 {subscription.current_usage:,}/{subscription.total_available_tokens:,})"
    )

