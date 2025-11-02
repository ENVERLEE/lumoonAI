# -*- coding: utf-8 -*-
"""
월별 사용량 리셋 명령어

사용법: python manage.py reset_monthly_usage
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import UserSubscription


class Command(BaseCommand):
    help = '월별 사용량 리셋 (매월 1일에 실행 권장)'

    def handle(self, *args, **options):
        now = timezone.now()
        
        # 현재 월의 1일인지 확인 (선택적)
        # if now.day != 1:
        #     self.stdout.write(
        #         self.style.WARNING('월 1일이 아닙니다. 계속 진행하려면 주석을 해제하세요.')
        #     )
        #     return
        
        subscriptions = UserSubscription.objects.filter(is_active=True)
        reset_count = 0
        
        for subscription in subscriptions:
            # last_reset_date가 없거나 이번 달이 아니면 리셋
            should_reset = False
            if not subscription.last_reset_date:
                should_reset = True
            elif subscription.last_reset_date.year != now.year or \
                 subscription.last_reset_date.month != now.month:
                should_reset = True
            
            if should_reset:
                subscription.current_usage = 0
                subscription.last_reset_date = now
                subscription.save()
                reset_count += 1
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ {subscription.user.username}의 사용량 리셋 '
                        f'({subscription.current_usage:,} → 0)'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n완료! {reset_count}개의 구독 사용량이 리셋되었습니다.')
        )

