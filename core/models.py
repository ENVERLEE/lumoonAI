# -*- coding: utf-8 -*-
"""
Core Django Models

Session, Intent, PromptHistory 등 핵심 데이터 모델 정의
"""

import uuid
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    """
    커스텀 사용자 모델
    
    Django 기본 User를 확장하여 추가 필드를 제공합니다.
    """
    bio = models.TextField(
        blank=True,
        help_text="사용자 소개"
    )
    avatar = models.URLField(
        blank=True,
        help_text="프로필 이미지 URL"
    )
    preferences = models.JSONField(
        default=dict,
        help_text="사용자 설정"
    )
    email_verified = models.BooleanField(
        default=False,
        help_text="이메일 인증 완료 여부"
    )
    email_verification_token = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        help_text="이메일 인증 토큰"
    )
    verification_token_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="인증 토큰 만료 시각"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return f"{self.username} ({self.email})"


class Conversation(models.Model):
    """
    대화 모델
    
    사용자의 대화 세션을 관리합니다.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='conversations',
        help_text="대화 소유자"
    )
    title = models.CharField(
        max_length=255,
        default="새로운 대화",
        help_text="대화 제목"
    )
    last_message_at = models.DateTimeField(
        auto_now=True,
        help_text="마지막 메시지 시각"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'conversations'
        ordering = ['-last_message_at']
        indexes = [
            models.Index(fields=['user', '-last_message_at']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"


class Message(models.Model):
    """
    메시지 모델
    
    대화 내의 개별 메시지를 저장합니다.
    """
    ROLE_CHOICES = [
        ('user', '사용자'),
        ('assistant', 'AI 어시스턴트'),
        ('system', '시스템'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        help_text="소속 대화"
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        help_text="메시지 역할"
    )
    content = models.TextField(
        help_text="메시지 내용"
    )
    metadata = models.JSONField(
        default=dict,
        help_text="메타데이터 (토큰 수, 모델 등)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['role']),
        ]
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}"


class UserCustomInstructions(models.Model):
    """
    사용자 커스텀 지침 모델
    
    사용자별 AI 동작 지침을 저장합니다.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='custom_instructions',
        help_text="사용자"
    )
    instructions = models.TextField(
        help_text="커스텀 지침 내용"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="활성화 여부"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_custom_instructions'
        verbose_name_plural = 'User Custom Instructions'
    
    def __str__(self):
        return f"커스텀 지침 - {self.user.username}"


class ConversationMemory(models.Model):
    """
    대화 메모리 모델 (RAG용)
    
    대화의 임베딩 벡터를 저장하여 유사도 검색을 지원합니다.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='memories',
        help_text="사용자"
    )
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='memories',
        help_text="연관 대화"
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='memories',
        null=True,
        blank=True,
        help_text="연관 메시지"
    )
    content = models.TextField(
        help_text="임베딩할 내용"
    )
    embedding_vector = models.BinaryField(
        help_text="임베딩 벡터 (numpy array를 bytes로 저장)"
    )
    metadata = models.JSONField(
        default=dict,
        help_text="메타데이터 (토큰 수, 임베딩 모델 등)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'conversation_memories'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['conversation']),
        ]
    
    def __str__(self):
        return f"메모리 - {self.user.username} - {self.content[:30]}"


class Session(models.Model):
    """
    사용자 세션 모델
    
    대화 세션의 상태와 컨텍스트를 관리합니다.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='sessions',
        null=True,
        blank=True,
        help_text="세션 소유자 (익명 사용자는 null)"
    )
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='sessions',
        null=True,
        blank=True,
        help_text="연관 대화"
    )
    role = models.TextField(
        default="당신은 전문 AI 어시스턴트입니다.",
        help_text="AI의 역할 정의"
    )
    task = models.TextField(
        blank=True,
        help_text="수행할 작업 명세"
    )
    context = models.JSONField(
        default=dict,
        help_text="대화 컨텍스트 (딕셔너리)"
    )
    constraints = models.JSONField(
        default=list,
        help_text="제약 조건 (리스트)"
    )
    user_preferences = models.JSONField(
        default=dict,
        help_text="학습된 사용자 선호도"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'sessions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        return f"Session {str(self.id)[:8]} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class Intent(models.Model):
    """
    의도 분석 결과 모델
    
    사용자 입력에서 파싱된 의도를 저장합니다.
    """
    
    COGNITIVE_GOALS = [
        ('알기', '알기 - 정보 획득'),
        ('하기', '하기 - 문제 해결'),
        ('만들기', '만들기 - 생성/창작'),
        ('배우기', '배우기 - 학습'),
    ]
    
    SPECIFICITY_LEVELS = [
        ('LOW', '낮음 - 추상적'),
        ('MEDIUM', '중간 - 범주적'),
        ('HIGH', '높음 - 구체적'),
    ]
    
    COMPLETENESS_LEVELS = [
        ('INCOMPLETE', '불완전 - 정보 부족'),
        ('PARTIAL', '부분적 - 일부 정보만'),
        ('COMPLETE', '완전 - 충분한 정보'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name='intents',
        null=True,
        blank=True,
        help_text="연관된 세션"
    )
    user_input = models.TextField(
        help_text="원본 사용자 입력"
    )
    cognitive_goal = models.CharField(
        max_length=50,
        choices=COGNITIVE_GOALS,
        help_text="인지적 목표"
    )
    specificity = models.CharField(
        max_length=20,
        choices=SPECIFICITY_LEVELS,
        help_text="구체성 수준"
    )
    completeness = models.CharField(
        max_length=20,
        choices=COMPLETENESS_LEVELS,
        help_text="완결성"
    )
    primary_entities = models.JSONField(
        default=list,
        help_text="핵심 엔티티/키워드 (리스트)"
    )
    constraints = models.JSONField(
        default=list,
        help_text="제약조건 (리스트)"
    )
    confidence = models.FloatField(
        help_text="신뢰도 (0.0 - 1.0)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'intents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['session', '-created_at']),
            models.Index(fields=['confidence']),
        ]
    
    def __str__(self):
        return f"Intent: {self.cognitive_goal} ({self.confidence:.2f}) - {self.user_input[:50]}"


class Question(models.Model):
    """
    컨텍스트 질문 모델
    
    Intent에서 생성된 질문들을 저장합니다.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    intent = models.ForeignKey(
        Intent,
        on_delete=models.CASCADE,
        related_name='questions',
        help_text="연관된 Intent"
    )
    text = models.TextField(
        help_text="질문 내용"
    )
    priority = models.IntegerField(
        default=3,
        help_text="우선순위 (1=최고, 5=최저)"
    )
    rationale = models.TextField(
        help_text="왜 이 질문이 필요한가"
    )
    options = models.JSONField(
        default=list,
        blank=True,
        help_text="선택지 (리스트)"
    )
    default_value = models.TextField(
        blank=True,
        help_text="기본값"
    )
    user_answer = models.TextField(
        blank=True,
        help_text="사용자 답변"
    )
    answered_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="답변 시각"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'questions'
        ordering = ['priority', 'created_at']
        indexes = [
            models.Index(fields=['intent', 'priority']),
        ]
    
    def __str__(self):
        return f"Q (P{self.priority}): {self.text[:50]}"


class PromptHistory(models.Model):
    """
    프롬프트 이력 모델
    
    생성된 프롬프트와 LLM 응답을 추적하고 캐싱에 활용합니다.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name='prompt_history',
        null=True,
        blank=True,
        help_text="연관된 세션"
    )
    prompt_hash = models.CharField(
        max_length=64,
        db_index=True,
        help_text="프롬프트 SHA256 해시 (캐싱용)"
    )
    original_prompt = models.TextField(
        help_text="원본 프롬프트"
    )
    synthesized_prompt = models.TextField(
        help_text="합성/최적화된 프롬프트"
    )
    model_used = models.CharField(
        max_length=100,
        help_text="사용된 모델명"
    )
    provider = models.CharField(
        max_length=50,
        default='openai',
        help_text="LLM 제공자"
    )
    response = models.TextField(
        help_text="LLM 응답"
    )
    tokens_used = models.IntegerField(
        default=0,
        help_text="사용된 토큰 수"
    )
    temperature = models.FloatField(
        default=0.7,
        help_text="생성 온도"
    )
    quality_level = models.CharField(
        max_length=20,
        default='balanced',
        help_text="품질 수준 (low/balanced/high)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'prompt_history'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['prompt_hash']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['session', '-created_at']),
            models.Index(fields=['model_used']),
        ]
    
    def __str__(self):
        return f"Prompt ({self.model_used}) - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class Feedback(models.Model):
    """
    피드백 모델
    
    사용자 피드백을 수집하고 학습에 활용합니다.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name='feedbacks',
        help_text="연관된 세션"
    )
    prompt_history = models.ForeignKey(
        PromptHistory,
        on_delete=models.CASCADE,
        related_name='feedbacks',
        null=True,
        blank=True,
        help_text="연관된 프롬프트 이력"
    )
    feedback_text = models.TextField(
        help_text="피드백 내용"
    )
    sentiment = models.CharField(
        max_length=20,
        choices=[
            ('positive', '긍정'),
            ('neutral', '중립'),
            ('negative', '부정'),
        ],
        default='neutral',
        help_text="감정 분류"
    )
    applied_adjustments = models.JSONField(
        default=list,
        help_text="적용된 조정사항 (리스트)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'feedbacks'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['session', '-created_at']),
            models.Index(fields=['sentiment']),
        ]
    
    def __str__(self):
        return f"Feedback ({self.sentiment}) - {self.feedback_text[:50]}"


class SearchReference(models.Model):
    """
    검색 참고자료 모델
    
    인터넷 모드에서 참고한 자료들을 저장합니다.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prompt_history = models.ForeignKey(
        PromptHistory,
        on_delete=models.CASCADE,
        related_name='search_references',
        help_text="연관 프롬프트 이력"
    )
    url = models.URLField(
        max_length=500,
        help_text="참고자료 URL"
    )
    title = models.CharField(
        max_length=500,
        blank=True,
        help_text="참고자료 제목"
    )
    snippet = models.TextField(
        blank=True,
        help_text="참고자료 요약/발췌"
    )
    source = models.CharField(
        max_length=100,
        default='perplexity',
        help_text="검색 소스"
    )
    relevance_score = models.FloatField(
        default=0.0,
        help_text="관련성 점수"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'search_references'
        ordering = ['-relevance_score', '-created_at']
        indexes = [
            models.Index(fields=['prompt_history', '-relevance_score']),
        ]
    
    def __str__(self):
        return f"참고자료: {self.title or self.url[:50]}"


class SubscriptionPlan(models.Model):
    """
    구독 플랜 모델
    
    무료, Basic, Pro 등의 구독 플랜을 정의합니다.
    """
    PLAN_TYPES = [
        ('free', '무료'),
        ('basic', 'Basic'),
        ('pro', 'Pro'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=50,
        unique=True,
        help_text="플랜 이름 (free, basic, pro)"
    )
    display_name = models.CharField(
        max_length=100,
        help_text="플랜 표시 이름"
    )
    plan_type = models.CharField(
        max_length=20,
        choices=PLAN_TYPES,
        help_text="플랜 유형"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="월 가격 (USD)"
    )
    monthly_limit = models.BigIntegerField(
        help_text="월 사용량 제한 (토큰 수)"
    )
    allowed_models = models.JSONField(
        default=list,
        help_text="허용된 모델 리스트 (예: ['gpt-5-nano', 'gpt-5-mini'])"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="활성화 여부"
    )
    description = models.TextField(
        blank=True,
        help_text="플랜 설명"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'subscription_plans'
        ordering = ['price']
        indexes = [
            models.Index(fields=['plan_type']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.display_name} (${self.price}/월)"


class UserSubscription(models.Model):
    """
    사용자 구독 모델
    
    사용자별 구독 정보와 사용량을 추적합니다.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='subscription',
        help_text="구독 사용자"
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name='user_subscriptions',
        help_text="구독 플랜"
    )
    is_active = models.BooleanField(
        default=False,
        help_text="구독 활성화 여부"
    )
    current_usage = models.BigIntegerField(
        default=0,
        help_text="현재 월 사용량 (토큰 수)"
    )
    bonus_tokens = models.BigIntegerField(
        default=0,
        help_text="보너스 토큰 (친구 초대 등)"
    )
    start_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="구독 시작일"
    )
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="구독 종료일"
    )
    last_reset_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="마지막 사용량 리셋 일시"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_subscriptions'
        indexes = [
            models.Index(fields=['user', '-start_date']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        status = "활성" if self.is_active else "비활성"
        return f"{self.user.username} - {self.plan.display_name} ({status})"
    
    @property
    def total_available_tokens(self):
        """총 사용 가능 토큰 (제한량 + 보너스)"""
        return self.plan.monthly_limit + self.bonus_tokens
    
    @property
    def remaining_tokens(self):
        """남은 토큰"""
        return max(0, self.total_available_tokens - self.current_usage)


class InviteCode(models.Model):
    """
    친구 초대 코드 모델
    
    사용자가 친구를 초대할 때 생성하는 코드를 관리합니다.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text="초대 코드"
    )
    inviter = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='invite_codes',
        help_text="초대한 사용자"
    )
    invitee = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        related_name='used_invite_code',
        null=True,
        blank=True,
        help_text="초대받은 사용자"
    )
    is_used = models.BooleanField(
        default=False,
        help_text="사용 여부"
    )
    used_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="사용 일시"
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="만료일 (선택적)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'invite_codes'
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['inviter', '-created_at']),
            models.Index(fields=['is_used']),
        ]
    
    def __str__(self):
        status = "사용됨" if self.is_used else "사용 가능"
        return f"{self.code} - {self.inviter.username} ({status})"


class PaymentRequest(models.Model):
    """
    결제 요청 모델
    
    수동 승인 방식의 결제 요청을 관리합니다.
    """
    STATUS_CHOICES = [
        ('pending', '대기중'),
        ('deposit_confirmed', '입금 완료 신청'),
        ('approved', '승인됨'),
        ('rejected', '거부됨'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='payment_requests',
        help_text="결제 요청 사용자"
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name='payment_requests',
        help_text="구독 플랜"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="결제 상태"
    )
    requested_at = models.DateTimeField(
        auto_now_add=True,
        help_text="요청 일시"
    )
    deposit_confirmed = models.BooleanField(
        default=False,
        help_text="입금 완료 여부 (사용자가 체크)"
    )
    deposit_confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="입금 완료 신청 일시"
    )
    approved = models.BooleanField(
        default=False,
        help_text="관리자 승인 여부"
    )
    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        related_name='approved_payments',
        null=True,
        blank=True,
        help_text="승인한 관리자"
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="승인 일시"
    )
    notes = models.TextField(
        blank=True,
        help_text="관리자 메모"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payment_requests'
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['user', '-requested_at']),
            models.Index(fields=['status']),
            models.Index(fields=['-requested_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.plan.display_name} ({self.get_status_display()})"


class UsageRecord(models.Model):
    """
    사용량 기록 모델
    
    월별 토큰 사용량 통계를 기록합니다.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='usage_records',
        help_text="사용자"
    )
    subscription = models.ForeignKey(
        UserSubscription,
        on_delete=models.CASCADE,
        related_name='usage_records',
        null=True,
        blank=True,
        help_text="연관 구독"
    )
    year = models.IntegerField(
        help_text="연도"
    )
    month = models.IntegerField(
        help_text="월 (1-12)"
    )
    total_tokens = models.BigIntegerField(
        default=0,
        help_text="총 사용 토큰 수"
    )
    tokens_by_model = models.JSONField(
        default=dict,
        help_text="모델별 사용 토큰 수 (예: {'gpt-5-nano': 100000, 'gpt-5-mini': 50000})"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'usage_records'
        unique_together = ['user', 'year', 'month']
        ordering = ['-year', '-month']
        indexes = [
            models.Index(fields=['user', '-year', '-month']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.year}년 {self.month}월 ({self.total_tokens:,} 토큰)"
