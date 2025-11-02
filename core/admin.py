# -*- coding: utf-8 -*-
"""
Django Admin 설정
"""

from django.contrib import admin
from .models import (
    SubscriptionPlan,
    UserSubscription,
    InviteCode,
    PaymentRequest,
    UsageRecord,
)


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    """구독 플랜 관리"""
    list_display = ['display_name', 'plan_type', 'price', 'monthly_limit', 'is_active']
    list_filter = ['plan_type', 'is_active']
    search_fields = ['name', 'display_name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    """사용자 구독 관리"""
    list_display = ['user', 'plan', 'is_active', 'current_usage', 'bonus_tokens', 'start_date']
    list_filter = ['is_active', 'plan']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['user']


@admin.register(InviteCode)
class InviteCodeAdmin(admin.ModelAdmin):
    """초대 코드 관리"""
    list_display = ['code', 'inviter', 'invitee', 'is_used', 'used_at', 'created_at']
    list_filter = ['is_used', 'created_at']
    search_fields = ['code', 'inviter__username', 'invitee__username']
    readonly_fields = ['id', 'created_at']
    raw_id_fields = ['inviter', 'invitee']


@admin.register(PaymentRequest)
class PaymentRequestAdmin(admin.ModelAdmin):
    """결제 요청 관리"""
    list_display = ['user', 'plan', 'status', 'deposit_confirmed', 'approved', 'requested_at']
    list_filter = ['status', 'deposit_confirmed', 'approved', 'requested_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['id', 'requested_at', 'created_at', 'updated_at']
    raw_id_fields = ['user', 'approved_by']
    actions = ['approve_selected', 'reject_selected']
    
    def approve_selected(self, request, queryset):
        """선택된 결제 요청 승인"""
        from django.utils import timezone
        from datetime import timedelta
        from .models import UserSubscription
        
        count = 0
        for payment_request in queryset.filter(status__in=['pending', 'deposit_confirmed']):
            payment_request.approved = True
            payment_request.approved_by = request.user
            payment_request.approved_at = timezone.now()
            payment_request.status = 'approved'
            payment_request.save()
            
            # UserSubscription 활성화
            subscription, _ = UserSubscription.objects.get_or_create(
                user=payment_request.user,
                defaults={'plan': payment_request.plan}
            )
            subscription.plan = payment_request.plan
            subscription.is_active = True
            subscription.start_date = timezone.now()
            subscription.end_date = timezone.now() + timedelta(days=30)
            subscription.current_usage = 0
            subscription.save()
            
            count += 1
        
        self.message_user(request, f'{count}개의 결제 요청이 승인되었습니다.')
    approve_selected.short_description = '선택된 결제 요청 승인'
    
    def reject_selected(self, request, queryset):
        """선택된 결제 요청 거부"""
        from django.utils import timezone
        
        count = 0
        for payment_request in queryset.filter(status__in=['pending', 'deposit_confirmed']):
            payment_request.approved = False
            payment_request.approved_by = request.user
            payment_request.status = 'rejected'
            payment_request.save()
            count += 1
        
        self.message_user(request, f'{count}개의 결제 요청이 거부되었습니다.')
    reject_selected.short_description = '선택된 결제 요청 거부'


@admin.register(UsageRecord)
class UsageRecordAdmin(admin.ModelAdmin):
    """사용량 기록 관리"""
    list_display = ['user', 'year', 'month', 'total_tokens', 'created_at']
    list_filter = ['year', 'month']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['user', 'subscription']
