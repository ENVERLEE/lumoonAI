# -*- coding: utf-8 -*-
"""
Core App URL Configuration
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    SessionViewSet,
    IntentViewSet,
    QuestionViewSet,
    PromptHistoryViewSet,
    FeedbackViewSet,
    IntentParseView,
    ContextQuestionsView,
    AnswerQuestionView,
    PromptSynthesizeView,
    LLMGenerateView,
    FeedbackCreateView,
    ConversationViewSet,
    MessageViewSet,
    UserCustomInstructionsViewSet,
)
from .auth_views import (
    register_view,
    login_view,
    logout_view,
    current_user_view,
    update_user_view,
    verify_email_view,
    resend_verification_view,
)
from .subscription_views import (
    SubscriptionPlanViewSet,
    UserSubscriptionViewSet,
)
from .payment_views import (
    get_account_info,
    create_payment_request,
    confirm_deposit,
    get_payment_status,
    approve_payment,
    list_pending_payments,
)
from .invite_views import (
    create_invite_code,
    list_invite_codes,
    use_invite_code,
    get_invite_stats,
)

# Router for ViewSets
router = DefaultRouter()
router.register(r'sessions', SessionViewSet, basename='session')
router.register(r'intents', IntentViewSet, basename='intent')
router.register(r'questions', QuestionViewSet, basename='question')
router.register(r'prompt-history', PromptHistoryViewSet, basename='prompthistory')
router.register(r'feedbacks', FeedbackViewSet, basename='feedback')
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'custom-instructions', UserCustomInstructionsViewSet, basename='custominstructions')
router.register(r'subscription-plans', SubscriptionPlanViewSet, basename='subscriptionplan')
router.register(r'subscriptions', UserSubscriptionViewSet, basename='subscription')

urlpatterns = [
    # ViewSets
    path('', include(router.urls)),
    
    # Authentication
    path('auth/register/', register_view, name='auth-register'),
    path('auth/login/', login_view, name='auth-login'),
    path('auth/logout/', logout_view, name='auth-logout'),
    path('auth/me/', current_user_view, name='auth-me'),
    path('auth/update/', update_user_view, name='auth-update'),
    path('auth/verify-email/', verify_email_view, name='auth-verify-email'),
    path('auth/resend-verification/', resend_verification_view, name='auth-resend-verification'),
    
    # Custom API Views
    path('intent/parse/', IntentParseView.as_view(), name='intent-parse'),
    path('context/questions/', ContextQuestionsView.as_view(), name='context-questions'),
    path('context/answer/', AnswerQuestionView.as_view(), name='context-answer'),
    path('prompt/synthesize/', PromptSynthesizeView.as_view(), name='prompt-synthesize'),
    path('llm/generate/', LLMGenerateView.as_view(), name='llm-generate'),
    path('feedback/', FeedbackCreateView.as_view(), name='feedback-create'),
    
    # Payment
    path('payment/account/', get_account_info, name='payment-account'),
    path('payment/request/', create_payment_request, name='payment-request'),
    path('payment/deposit/confirm/', confirm_deposit, name='payment-deposit-confirm'),
    path('payment/status/', get_payment_status, name='payment-status'),
    path('payment/admin/pending/', list_pending_payments, name='payment-admin-pending'),
    path('payment/admin/approve/', approve_payment, name='payment-admin-approve'),
    
    # Invite
    path('invite/create/', create_invite_code, name='invite-create'),
    path('invite/list/', list_invite_codes, name='invite-list'),
    path('invite/use/', use_invite_code, name='invite-use'),
    path('invite/stats/', get_invite_stats, name='invite-stats'),
]

