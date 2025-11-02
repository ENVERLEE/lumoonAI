# -*- coding: utf-8 -*-
"""
Django REST Framework Serializers

API 요청/응답을 위한 직렬화 클래스들
"""

from rest_framework import serializers
from .models import (
    Session, Intent, Question, PromptHistory, Feedback,
    CustomUser, Conversation, Message, UserCustomInstructions, SearchReference,
    SubscriptionPlan, UserSubscription, InviteCode, PaymentRequest, UsageRecord
)


class CustomUserSerializer(serializers.ModelSerializer):
    """CustomUser 직렬화"""
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'bio', 'avatar',
            'preferences', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ConversationSerializer(serializers.ModelSerializer):
    """Conversation 직렬화"""
    user = serializers.StringRelatedField(read_only=True)
    message_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'user', 'title', 'last_message_at',
            'created_at', 'updated_at', 'message_count'
        ]
        read_only_fields = ['id', 'user', 'last_message_at', 'created_at', 'updated_at']
    
    def get_message_count(self, obj):
        return obj.messages.count()


class MessageSerializer(serializers.ModelSerializer):
    """Message 직렬화"""
    conversation_id = serializers.UUIDField(write_only=True, required=False)
    
    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'conversation_id', 'role', 
            'content', 'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'conversation', 'created_at']


class UserCustomInstructionsSerializer(serializers.ModelSerializer):
    """UserCustomInstructions 직렬화"""
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = UserCustomInstructions
        fields = [
            'id', 'user', 'instructions', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class SearchReferenceSerializer(serializers.ModelSerializer):
    """SearchReference 직렬화"""
    
    class Meta:
        model = SearchReference
        fields = [
            'id', 'prompt_history', 'url', 'title', 'snippet',
            'source', 'relevance_score', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class SessionSerializer(serializers.ModelSerializer):
    """Session 직렬화"""
    
    class Meta:
        model = Session
        fields = [
            'id', 'role', 'task', 'context', 'constraints',
            'user_preferences', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class IntentSerializer(serializers.ModelSerializer):
    """Intent 직렬화"""
    session = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = Intent
        fields = [
            'id', 'session', 'user_input', 'cognitive_goal',
            'specificity', 'completeness', 'primary_entities',
            'constraints', 'confidence', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class QuestionSerializer(serializers.ModelSerializer):
    """Question 직렬화"""
    intent = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = Question
        fields = [
            'id', 'intent', 'text', 'priority', 'rationale',
            'options', 'default_value', 'user_answer',
            'answered_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class PromptHistorySerializer(serializers.ModelSerializer):
    """PromptHistory 직렬화"""
    session = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = PromptHistory
        fields = [
            'id', 'session', 'prompt_hash', 'original_prompt',
            'synthesized_prompt', 'model_used', 'provider',
            'response', 'tokens_used', 'temperature',
            'quality_level', 'created_at'
        ]
        read_only_fields = ['id', 'prompt_hash', 'created_at']


class FeedbackSerializer(serializers.ModelSerializer):
    """Feedback 직렬화"""
    session = serializers.PrimaryKeyRelatedField(read_only=True)
    prompt_history = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = Feedback
        fields = [
            'id', 'session', 'prompt_history', 'feedback_text',
            'sentiment', 'applied_adjustments', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


# API 요청/응답용 Serializers

class IntentParseRequestSerializer(serializers.Serializer):
    """Intent 파싱 요청"""
    user_input = serializers.CharField(required=True, help_text="사용자 입력")
    session_id = serializers.UUIDField(required=False, help_text="세션 ID (선택적)")
    history = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="대화 히스토리"
    )


class IntentParseResponseSerializer(serializers.Serializer):
    """Intent 파싱 응답"""
    intent = IntentSerializer()
    session_id = serializers.UUIDField()
    needs_clarification = serializers.BooleanField()


class ContextQuestionsRequestSerializer(serializers.Serializer):
    """컨텍스트 질문 요청"""
    session_id = serializers.UUIDField(required=True, help_text="세션 ID")
    intent_id = serializers.UUIDField(required=False, help_text="Intent ID (선택적)")


class QuestionItemSerializer(serializers.Serializer):
    """질문 아이템 (QuestionItem 클래스용)"""
    text = serializers.CharField()
    priority = serializers.IntegerField()
    rationale = serializers.CharField()
    options = serializers.ListField(child=serializers.CharField(), required=False)
    default = serializers.CharField(required=False, allow_null=True)


class ContextQuestionsResponseSerializer(serializers.Serializer):
    """컨텍스트 질문 응답"""
    session_id = serializers.UUIDField()
    questions = QuestionItemSerializer(many=True)


class AnswerQuestionRequestSerializer(serializers.Serializer):
    """질문 답변 요청"""
    session_id = serializers.UUIDField(required=True)
    question_text = serializers.CharField(required=True)
    answer = serializers.CharField(required=True)


class PromptSynthesizeRequestSerializer(serializers.Serializer):
    """프롬프트 합성 요청"""
    session_id = serializers.UUIDField(required=True)
    user_input = serializers.CharField(required=False, help_text="사용자 입력 (선택적)")
    output_format = serializers.CharField(required=False, help_text="출력 형식 (선택적)")


class PromptSynthesizeResponseSerializer(serializers.Serializer):
    """프롬프트 합성 응답"""
    session_id = serializers.UUIDField()
    synthesized_prompt = serializers.CharField()
    estimated_tokens = serializers.IntegerField()


class LLMGenerateRequestSerializer(serializers.Serializer):
    """LLM 생성 요청"""
    session_id = serializers.UUIDField(required=True)
    prompt = serializers.CharField(required=False, help_text="프롬프트 (없으면 자동 합성)")
    user_input = serializers.CharField(required=False, help_text="사용자 입력")
    quality = serializers.ChoiceField(
        choices=['low', 'balanced', 'high'],
        default='balanced',
        help_text="품질 수준"
    )
    temperature = serializers.FloatField(
        required=False,
        min_value=0.0,
        max_value=2.0,
        help_text="생성 온도"
    )
    max_tokens = serializers.IntegerField(required=False, help_text="최대 토큰 수")
    internet_mode = serializers.BooleanField(
        default=False,
        help_text="인터넷 검색 모드 (Perplexity Sonar 사용)"
    )
    specificity_level = serializers.ChoiceField(
        choices=['짧음', '간결', '보통', '구체적', '매우 구체적'],
        default='매우 구체적',
        help_text="답변의 구체성 수준"
    )


class LLMGenerateResponseSerializer(serializers.Serializer):
    """LLM 생성 응답"""
    session_id = serializers.UUIDField()
    prompt_history_id = serializers.UUIDField()
    model_used = serializers.CharField()
    provider = serializers.CharField()
    response = serializers.CharField()
    tokens_used = serializers.IntegerField()
    quality_level = serializers.CharField()
    references = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list,
        help_text="인터넷 모드 참고자료"
    )


class FeedbackRequestSerializer(serializers.Serializer):
    """피드백 요청"""
    session_id = serializers.UUIDField(required=True)
    feedback_text = serializers.CharField(required=True)
    sentiment = serializers.ChoiceField(
        choices=['positive', 'neutral', 'negative'],
        default='neutral'
    )
    prompt_history_id = serializers.UUIDField(required=False)


class SessionSummarySerializer(serializers.Serializer):
    """세션 요약"""
    session_id = serializers.UUIDField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    role = serializers.CharField()
    task = serializers.CharField()
    context_size = serializers.IntegerField()
    constraints_count = serializers.IntegerField()
    intents_count = serializers.IntegerField()
    prompt_history_count = serializers.IntegerField()
    feedbacks_count = serializers.IntegerField()
    user_preferences = serializers.JSONField()


# 구독 플랜 관련 Serializers

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """구독 플랜 직렬화"""
    
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name', 'display_name', 'plan_type', 'price',
            'monthly_limit', 'allowed_models', 'is_active', 'description',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserSubscriptionSerializer(serializers.ModelSerializer):
    """사용자 구독 직렬화"""
    plan = SubscriptionPlanSerializer(read_only=True)
    plan_id = serializers.UUIDField(write_only=True, required=False)
    total_available_tokens = serializers.IntegerField(read_only=True)
    remaining_tokens = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = UserSubscription
        fields = [
            'id', 'user', 'plan', 'plan_id', 'is_active',
            'current_usage', 'bonus_tokens', 'total_available_tokens',
            'remaining_tokens', 'start_date', 'end_date',
            'last_reset_date', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'current_usage', 'bonus_tokens',
            'total_available_tokens', 'remaining_tokens',
            'created_at', 'updated_at'
        ]


class InviteCodeSerializer(serializers.ModelSerializer):
    """초대 코드 직렬화"""
    inviter = serializers.StringRelatedField(read_only=True)
    invitee = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = InviteCode
        fields = [
            'id', 'code', 'inviter', 'invitee', 'is_used',
            'used_at', 'expires_at', 'created_at'
        ]
        read_only_fields = ['id', 'inviter', 'created_at']


class PaymentRequestSerializer(serializers.ModelSerializer):
    """결제 요청 직렬화"""
    user = serializers.StringRelatedField(read_only=True)
    plan = SubscriptionPlanSerializer(read_only=True)
    plan_id = serializers.UUIDField(write_only=True, required=False)
    approved_by = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = PaymentRequest
        fields = [
            'id', 'user', 'plan', 'plan_id', 'status',
            'requested_at', 'deposit_confirmed', 'deposit_confirmed_at',
            'approved', 'approved_by', 'approved_at', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'status', 'requested_at',
            'approved_by', 'approved_at', 'created_at', 'updated_at'
        ]


class UsageRecordSerializer(serializers.ModelSerializer):
    """사용량 기록 직렬화"""
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = UsageRecord
        fields = [
            'id', 'user', 'subscription', 'year', 'month',
            'total_tokens', 'tokens_by_model', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


# 구독 관련 API 요청/응답 Serializers

class SubscriptionChangeRequestSerializer(serializers.Serializer):
    """구독 변경 요청"""
    plan_id = serializers.UUIDField(required=True, help_text="변경할 플랜 ID")


class UsageStatsResponseSerializer(serializers.Serializer):
    """사용량 통계 응답"""
    current_usage = serializers.IntegerField()
    monthly_limit = serializers.IntegerField()
    bonus_tokens = serializers.IntegerField()
    total_available = serializers.IntegerField()
    remaining = serializers.IntegerField()
    usage_percentage = serializers.FloatField()


class ModelAvailabilityResponseSerializer(serializers.Serializer):
    """모델 선택 가능 여부 응답"""
    model_name = serializers.CharField()
    is_available = serializers.BooleanField()
    reason = serializers.CharField(required=False)


# 친구 초대 관련 API Serializers

class InviteCodeCreateRequestSerializer(serializers.Serializer):
    """초대 코드 생성 요청"""
    expires_in_days = serializers.IntegerField(
        required=False,
        default=30,
        help_text="만료일 (일 단위, 선택적)"
    )


class InviteCodeUseRequestSerializer(serializers.Serializer):
    """초대 코드 사용 요청"""
    code = serializers.CharField(required=True, max_length=20, help_text="초대 코드")


class InviteCodeUseResponseSerializer(serializers.Serializer):
    """초대 코드 사용 응답"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    bonus_tokens = serializers.IntegerField(required=False)


# 결제 관련 API Serializers

class PaymentRequestCreateSerializer(serializers.Serializer):
    """결제 요청 생성"""
    plan_id = serializers.UUIDField(required=True, help_text="구독 플랜 ID")


class PaymentDepositConfirmSerializer(serializers.Serializer):
    """입금 완료 신청"""
    payment_request_id = serializers.UUIDField(required=True)


class PaymentApprovalSerializer(serializers.Serializer):
    """결제 승인/거부"""
    payment_request_id = serializers.UUIDField(required=True)
    approve = serializers.BooleanField(required=True, help_text="True=승인, False=거부")
    notes = serializers.CharField(required=False, allow_blank=True, help_text="관리자 메모")

