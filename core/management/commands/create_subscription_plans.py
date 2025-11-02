# -*- coding: utf-8 -*-
"""
구독 플랜 초기 데이터 생성 명령어

사용법: python manage.py create_subscription_plans
"""

from django.core.management.base import BaseCommand
from core.models import SubscriptionPlan


class Command(BaseCommand):
    help = '구독 플랜 초기 데이터 생성'

    def handle(self, *args, **options):
        plans = [
            {
                'name': 'free',
                'display_name': '무료 플랜',
                'plan_type': 'free',
                'price': 0.00,
                'monthly_limit': 300000,  # 30만 토큰
                'allowed_models': ['gpt-5-nano'],
                'is_active': True,
                'description': '무료로 제공되는 기본 플랜입니다. gpt-5-nano 모델만 사용 가능합니다.'
            },
            {
                'name': 'basic',
                'display_name': 'Basic 플랜',
                'plan_type': 'basic',
                'price': 9.99,
                'monthly_limit': 2000000,  # 200만 토큰
                'allowed_models': ['gpt-5-nano', 'gpt-5-mini'],
                'is_active': True,
                'description': '기본 유료 플랜입니다. gpt-5-nano와 gpt-5-mini 모델을 사용할 수 있습니다.'
            },
            {
                'name': 'pro',
                'display_name': 'Pro 플랜',
                'plan_type': 'pro',
                'price': 39.99,
                'monthly_limit': 10000000,  # 1000만 토큰
                'allowed_models': ['gpt-5-nano', 'gpt-5-mini', 'gpt-5', 'gpt-4.1', 'gpt-4.1-mini'],
                'is_active': True,
                'description': '프로 플랜입니다. 모든 모델을 사용할 수 있습니다.'
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for plan_data in plans:
            plan, created = SubscriptionPlan.objects.update_or_create(
                name=plan_data['name'],
                defaults=plan_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ 플랜 생성: {plan.display_name}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ 플랜 업데이트: {plan.display_name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n완료! 생성: {created_count}개, 업데이트: {updated_count}개'
            )
        )

