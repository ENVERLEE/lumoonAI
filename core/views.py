# -*- coding: utf-8 -*-
"""
Django REST Framework Views

API 엔드포인트를 구현합니다.
"""

import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from .models import (
    Session, Intent, Question, PromptHistory, Feedback,
    Conversation, Message, UserCustomInstructions, SearchReference
)
from .serializers import (
    SessionSerializer, IntentSerializer, QuestionSerializer,
    PromptHistorySerializer, FeedbackSerializer,
    IntentParseRequestSerializer, IntentParseResponseSerializer,
    ContextQuestionsRequestSerializer, ContextQuestionsResponseSerializer,
    AnswerQuestionRequestSerializer,
    PromptSynthesizeRequestSerializer, PromptSynthesizeResponseSerializer,
    LLMGenerateRequestSerializer, LLMGenerateResponseSerializer,
    FeedbackRequestSerializer, SessionSummarySerializer,
    QuestionItemSerializer,
    ConversationSerializer, MessageSerializer, UserCustomInstructionsSerializer,
    SearchReferenceSerializer
)
from .session_manager import SessionManager
from .intent_parser import get_intent_parser
from .prompt_synthesizer import SpecificityLevel
from .usage_decorator import check_usage_limit, update_usage, UsageLimitExceeded, can_use_model
from llm_providers.router import get_router, TaskType, QualityLevel

logger = logging.getLogger(__name__)


class ConversationViewSet(viewsets.ModelViewSet):
    """Conversation CRUD API"""
    serializer_class = ConversationSerializer
    
    def get_queryset(self):
        """현재 사용자의 대화만 조회"""
        if self.request.user.is_authenticated:
            return Conversation.objects.filter(user=self.request.user)
        return Conversation.objects.none()
    
    def perform_create(self, serializer):
        """대화 생성 시 현재 사용자 설정"""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """특정 대화의 메시지 목록"""
        conversation = self.get_object()
        messages = conversation.messages.all()
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def rename(self, request, pk=None):
        """대화 제목 변경"""
        conversation = self.get_object()
        title = request.data.get('title')
        if title:
            conversation.title = title
            conversation.save()
            serializer = self.get_serializer(conversation)
            return Response(serializer.data)
        return Response(
            {'error': '제목을 입력해주세요.'},
            status=status.HTTP_400_BAD_REQUEST
        )


class MessageViewSet(viewsets.ModelViewSet):
    """Message CRUD API"""
    serializer_class = MessageSerializer
    
    def get_queryset(self):
        """현재 사용자의 대화 메시지만 조회"""
        if self.request.user.is_authenticated:
            return Message.objects.filter(conversation__user=self.request.user)
        return Message.objects.none()
    
    def perform_create(self, serializer):
        """메시지 생성 시 대화 연결"""
        conversation_id = self.request.data.get('conversation_id')
        if conversation_id:
            try:
                conversation = Conversation.objects.get(
                    id=conversation_id,
                    user=self.request.user
                )
                serializer.save(conversation=conversation)
            except Conversation.DoesNotExist:
                raise ValidationError('대화를 찾을 수 없습니다.')
        else:
            serializer.save()


class UserCustomInstructionsViewSet(viewsets.ModelViewSet):
    """UserCustomInstructions CRUD API"""
    serializer_class = UserCustomInstructionsSerializer
    
    def get_queryset(self):
        """현재 사용자의 커스텀 지침만 조회"""
        if self.request.user.is_authenticated:
            return UserCustomInstructions.objects.filter(user=self.request.user)
        return UserCustomInstructions.objects.none()
    
    def perform_create(self, serializer):
        """커스텀 지침 생성 시 현재 사용자 설정"""
        # 기존 지침이 있으면 업데이트, 없으면 생성
        existing = UserCustomInstructions.objects.filter(user=self.request.user).first()
        if existing:
            existing.instructions = serializer.validated_data['instructions']
            existing.is_active = serializer.validated_data.get('is_active', existing.is_active)
            existing.save()
            return existing
        else:
            serializer.save(user=self.request.user)


class SessionViewSet(viewsets.ModelViewSet):
    """Session CRUD API"""
    queryset = Session.objects.all()
    serializer_class = SessionSerializer
    
    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """세션 요약 정보"""
        session_manager = SessionManager(session_id=str(pk))
        summary = session_manager.get_session_summary()
        serializer = SessionSummarySerializer(summary)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def set_goal(self, request, pk=None):
        """온보딩 목표 설정"""
        try:
            session = self.get_object()
            goal = request.data.get('goal')
            
            if not goal:
                return Response(
                    {'error': '목표를 지정해주세요.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # user_preferences에 저장
            session.user_preferences['initial_goal'] = goal
            session.user_preferences['goal_set_at'] = str(session.updated_at)
            session.save()
            
            logger.info(f"세션 {pk} 목표 설정: {goal}")
            
            return Response({
                'session_id': str(session.id),
                'goal': goal,
                'message': f'목표가 "{goal}"(으)로 설정되었습니다.'
            })
            
        except Exception as e:
            logger.error(f"목표 설정 실패: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class IntentViewSet(viewsets.ReadOnlyModelViewSet):
    """Intent 조회 API"""
    queryset = Intent.objects.all()
    serializer_class = IntentSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        session_id = self.request.query_params.get('session_id')
        if session_id:
            queryset = queryset.filter(session_id=session_id)
        return queryset


class QuestionViewSet(viewsets.ReadOnlyModelViewSet):
    """Question 조회 API"""
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        intent_id = self.request.query_params.get('intent_id')
        session_id = self.request.query_params.get('session_id')
        
        if intent_id:
            queryset = queryset.filter(intent_id=intent_id)
        elif session_id:
            queryset = queryset.filter(intent__session_id=session_id)
        
        return queryset


class PromptHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """PromptHistory 조회 API"""
    queryset = PromptHistory.objects.all()
    serializer_class = PromptHistorySerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        session_id = self.request.query_params.get('session_id')
        if session_id:
            queryset = queryset.filter(session_id=session_id)
        return queryset


class FeedbackViewSet(viewsets.ModelViewSet):
    """Feedback CRUD API"""
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        session_id = self.request.query_params.get('session_id')
        if session_id:
            queryset = queryset.filter(session_id=session_id)
        return queryset


class IntentParseView(APIView):
    """
    Intent 파싱 API
    
    POST /api/intent/parse
    """
    permission_classes = [AllowAny]  # 익명 사용자도 사용 가능
    
    def post(self, request):
        """사용자 입력에서 의도 파싱"""
        serializer = IntentParseRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        user_input = data['user_input']
        session_id = data.get('session_id')
        history = data.get('history', [])
        
        try:
            # 사용자 정보 가져오기
            user = request.user if request.user.is_authenticated else None
            
            # Session Manager
            session_manager = SessionManager(
                session_id=str(session_id) if session_id else None,
                user=user
            )
            
            # Intent 파싱
            intent_result = session_manager.parse_user_input(user_input)
            
            # Intent 모델 가져오기
            intent_model = session_manager.session.intents.first()
            
            # 응답 직접 구성
            response_data = {
                'intent': {
                    'id': str(intent_model.id),
                    'session': str(intent_model.session.id) if intent_model.session else None,
                    'user_input': intent_model.user_input,
                    'cognitive_goal': intent_model.cognitive_goal,
                    'specificity': intent_model.specificity,
                    'completeness': intent_model.completeness,
                    'primary_entities': intent_model.primary_entities,
                    'constraints': intent_model.constraints,
                    'confidence': intent_model.confidence,
                    'created_at': intent_model.created_at.isoformat(),
                },
                'session_id': session_manager.session_id,
                'needs_clarification': intent_result.needs_clarification()
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Intent 파싱 실패: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ContextQuestionsView(APIView):
    """
    컨텍스트 질문 생성 API
    
    POST /api/context/questions
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """필요한 컨텍스트 질문 생성"""
        serializer = ContextQuestionsRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        session_id = str(data['session_id'])
        intent_id = data.get('intent_id')
        
        try:
            # Session Manager
            session_manager = SessionManager(session_id=session_id)
            
            # Intent 가져오기
            intent = None
            if intent_id:
                try:
                    from core.models import Intent
                    intent_model = Intent.objects.get(id=intent_id, session_id=session_id)
                    from core.intent_parser import IntentParseResult
                    intent = IntentParseResult(
                        cognitive_goal=intent_model.cognitive_goal,
                        specificity=intent_model.specificity,
                        completeness=intent_model.completeness,
                        primary_entities=intent_model.primary_entities,
                        constraints=intent_model.constraints,
                        confidence=intent_model.confidence
                    )
                    logger.info(f"Intent ID로 Intent 로드: {intent_id}")
                except Intent.DoesNotExist:
                    logger.warning(f"Intent를 찾을 수 없음: {intent_id}, 최근 Intent 사용 시도")
            
            # 질문 생성
            questions = session_manager.generate_questions(intent=intent)
            
            # 응답
            question_items = [
                {
                    'text': q.text,
                    'priority': q.priority,
                    'rationale': q.rationale,
                    'options': q.options,
                    'default': q.default
                }
                for q in questions
            ]
            
            response_data = {
                'session_id': session_id,
                'questions': question_items
            }
            
            response_serializer = ContextQuestionsResponseSerializer(response_data)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        except ValueError as e:
            # Intent가 없는 경우 등
            logger.warning(f"질문 생성 실패 (ValueError): {e}")
            return Response(
                {'error': str(e), 'detail': 'Intent가 없거나 세션이 초기화되지 않았습니다. Intent 파싱을 먼저 수행하세요.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"질문 생성 실패: {e}", exc_info=True)
            return Response(
                {'error': str(e), 'detail': '질문 생성 중 오류가 발생했습니다.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AnswerQuestionView(APIView):
    """
    질문 답변 API
    
    POST /api/context/answer
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """질문에 답변"""
        serializer = AnswerQuestionRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        session_id = str(data['session_id'])
        question_text = data['question_text']
        answer = data['answer']
        
        try:
            # Session Manager
            session_manager = SessionManager(session_id=session_id)
            
            # 답변 저장
            session_manager.answer_question(question_text, answer)
            
            return Response(
                {'message': '답변이 저장되었습니다.'},
                status=status.HTTP_200_OK
            )
        
        except Exception as e:
            logger.error(f"답변 저장 실패: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PromptSynthesizeView(APIView):
    """
    프롬프트 합성 API
    
    POST /api/prompt/synthesize
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """프롬프트 합성"""
        serializer = PromptSynthesizeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        session_id = str(data['session_id'])
        user_input = data.get('user_input')
        output_format = data.get('output_format')
        
        try:
            # Session Manager
            session_manager = SessionManager(session_id=session_id)
            
            # 프롬프트 합성
            synthesized = session_manager.synthesize_prompt(
                user_input=user_input,
                output_format=output_format
            )
            
            # 토큰 추정
            estimated_tokens = session_manager.prompt_synthesizer.estimate_tokens(synthesized)
            
            response_data = {
                'session_id': session_id,
                'synthesized_prompt': synthesized,
                'estimated_tokens': estimated_tokens
            }
            
            response_serializer = PromptSynthesizeResponseSerializer(response_data)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"프롬프트 합성 실패: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LLMGenerateView(APIView):
    """
    LLM 생성 API
    
    POST /api/llm/generate
    """
    permission_classes = [AllowAny]  # 익명 사용자도 사용 가능
    
    def post(self, request):
        """LLM으로 응답 생성"""
        serializer = LLMGenerateRequestSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"LLM 생성 요청 검증 실패: {serializer.errors}, 요청 데이터: {request.data}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        session_id = str(data['session_id'])
        prompt = data.get('prompt')
        user_input = data.get('user_input')
        quality = data.get('quality', 'balanced')
        temperature = data.get('temperature')
        max_tokens = data.get('max_tokens')
        internet_mode = data.get('internet_mode', False)
        specificity_level_str = data.get('specificity_level', '매우 구체적')
        
        try:
            # 구체성 레벨 변환
            specificity_level = SpecificityLevel(specificity_level_str)
            
            # 사용자 정보 가져오기
            user = request.user if request.user.is_authenticated else None
            
            # 대화 생성 또는 기존 대화 가져오기
            conversation = None
            if user:
                # session_id가 있으면 해당 세션의 conversation 찾기
                if session_id:
                    try:
                        session = Session.objects.get(id=session_id)
                        conversation = session.conversation
                    except Session.DoesNotExist:
                        pass
                
                # conversation이 없으면 새로 생성
                if not conversation:
                    conversation = Conversation.objects.create(
                        user=user,
                        title=user_input[:50] if user_input else '새로운 대화'
                    )
            
            # Session Manager
            session_manager = SessionManager(
                session_id=session_id if session_id else None,
                user=user,
                conversation=conversation
            )
            
            # 프롬프트가 없으면 자동 합성 (구체성 레벨 적용)
            if not prompt:
                # user_input이 없으면 세션의 task 확인
                if not user_input or (isinstance(user_input, str) and not user_input.strip()):
                    if session_manager.session.task and session_manager.session.task.strip():
                        user_input = session_manager.session.task
                    else:
                        return Response(
                            {'error': 'user_input 또는 세션의 task가 필요합니다. 프롬프트를 직접 제공하거나 사용자 입력을 포함해주세요.'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                
                prompt = session_manager.synthesize_prompt(
                    user_input=user_input,
                    specificity_level=specificity_level,
                    use_rag=user is not None  # 로그인한 사용자만 RAG 사용
                )
            
            # 인터넷 모드 활성화 시 프롬프트 강화
            if internet_mode and user_input:
                router = get_router()
                logger.info("인터넷 모드 활성화: Perplexity Sonar로 검색 수행")
                prompt = router.enhance_prompt_with_internet(
                    prompt=prompt,
                    user_query=user_input
                )
            
            # Router로 제공자/모델 선택 (사용자 플랜 기반)
            router = get_router()
            quality_enum = QualityLevel(quality)
            
            # 사용자가 선택한 모델 확인 (request.data에서)
            preferred_model = request.data.get('preferred_model')
            
            provider, model, default_temp = router.get_provider(
                TaskType.FINAL_GENERATION,
                quality=quality_enum,
                user=user,
                preferred_model=preferred_model
            )
            
            # 사용량 확인 (예상 토큰 수 - 대략적으로 입력 토큰의 3배로 추정)
            estimated_input_tokens = len(prompt.split()) * 1.3  # 단어 수 대략 토큰 수
            estimated_output_tokens = estimated_input_tokens * 2  # output은 보통 더 많음
            estimated_total_tokens = int(estimated_input_tokens + estimated_output_tokens)
            
            if user:
                try:
                    check_usage_limit(user, estimated_total_tokens)
                except UsageLimitExceeded as e:
                    return Response(
                        {'error': str(e)},
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            # 온도 설정
            if temperature is None:
                temperature = default_temp
            
            # LLM 호출
            logger.info(f"LLM 생성: {provider.__class__.__name__}, {model}, 구체성={specificity_level_str}, 인터넷={internet_mode}")
            llm_response = provider.generate(
                prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # 이력 저장
            history = session_manager.save_prompt_history(
                original_prompt=user_input or prompt,
                synthesized_prompt=prompt,
                model_used=model,
                provider=provider.__class__.__name__,
                response=llm_response.content,
                tokens_used=llm_response.tokens_used,
                temperature=temperature,
                quality_level=quality
            )
            
            # 사용량 업데이트
            if user:
                update_usage(user, llm_response.tokens_used, model_name=model)
            
            # 인터넷 모드: 참고자료 저장
            references = []
            if internet_mode:
                # Perplexity 응답에서 citations 추출 시도
                raw_response = getattr(llm_response, 'raw_response', None)
                if raw_response and hasattr(raw_response, 'citations'):
                    citations = raw_response.citations
                    for i, citation in enumerate(citations[:10]):  # 최대 10개
                        # Citation은 URL 또는 텍스트일 수 있음
                        if isinstance(citation, str):
                            url = citation if citation.startswith('http') else ''
                            title = citation if not url else f"참고자료 {i+1}"
                        elif isinstance(citation, dict):
                            url = citation.get('url', '')
                            title = citation.get('title', f"참고자료 {i+1}")
                        else:
                            continue
                        
                        if url:
                            ref = SearchReference.objects.create(
                                prompt_history=history,
                                url=url,
                                title=title,
                                source='perplexity',
                                relevance_score=1.0 - (i * 0.1)  # 순서에 따라 점수
                            )
                            references.append({
                                'id': str(ref.id),
                                'url': ref.url,
                                'title': ref.title,
                                'source': ref.source
                            })
                    
                    logger.info(f"참고자료 {len(references)}개 저장됨")
            
            response_data = {
                'session_id': session_id,
                'prompt_history_id': str(history.id),
                'model_used': model,
                'provider': provider.__class__.__name__,
                'response': llm_response.content,
                'tokens_used': llm_response.tokens_used,
                'quality_level': quality,
                'references': references if internet_mode else []
            }
            
            response_serializer = LLMGenerateResponseSerializer(response_data)
            return Response(response_data, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"LLM 생성 실패: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FeedbackCreateView(APIView):
    """
    피드백 생성 API
    
    POST /api/feedback
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """피드백 저장"""
        serializer = FeedbackRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        session_id = str(data['session_id'])
        feedback_text = data['feedback_text']
        sentiment = data.get('sentiment', 'neutral')
        prompt_history_id = data.get('prompt_history_id')
        
        try:
            # Session Manager
            session_manager = SessionManager(session_id=session_id)
            
            # 피드백 저장
            feedback = session_manager.add_feedback(
                feedback_text=feedback_text,
                sentiment=sentiment,
                prompt_history_id=str(prompt_history_id) if prompt_history_id else None
            )
            
            feedback_serializer = FeedbackSerializer(feedback)
            return Response(feedback_serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            logger.error(f"피드백 저장 실패: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
