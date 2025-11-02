# -*- coding: utf-8 -*-
"""
Session Manager - 세션 관리 및 상태 관리

Stateful Session을 관리하고, 컨텍스트 누적, 학습된 선호도를 처리합니다.
plainplan.md의 8.1 원리 기반
"""

import logging
from typing import Dict, Any, Optional, List
from django.core.cache import cache

from .models import (
    Session, Intent, Question, PromptHistory, Feedback,
    CustomUser, Conversation, Message, UserCustomInstructions
)
from .intent_parser import IntentParseResult, get_intent_parser
from .context_elicitor import QuestionItem, get_context_elicitor
from .prompt_synthesizer import get_prompt_synthesizer, SpecificityLevel
from .rag_manager import get_rag_manager

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Session Manager 클래스
    
    세션의 전체 생명주기를 관리합니다:
    - 세션 생성/조회/업데이트
    - 컨텍스트 누적 및 관리
    - 학습된 선호도 추적
    - 프롬프트 생성 및 이력 관리
    - RAG 기반 메모리 검색
    - 커스텀 지침 통합
    """
    
    def __init__(
        self,
        session_id: Optional[str] = None,
        user: Optional[CustomUser] = None,
        conversation: Optional[Conversation] = None
    ):
        """
        Session Manager 초기화
        
        Args:
            session_id: 기존 세션 ID (없으면 새로 생성)
            user: 사용자 객체
            conversation: 대화 객체
        """
        if session_id:
            try:
                self.session = Session.objects.get(id=session_id)
                logger.info(f"기존 세션 로드: {session_id}")
            except Session.DoesNotExist:
                logger.warning(f"세션 {session_id}를 찾을 수 없어 새로 생성")
                self.session = Session.objects.create(user=user, conversation=conversation)
        else:
            self.session = Session.objects.create(user=user, conversation=conversation)
            logger.info(f"새 세션 생성: {self.session.id}")
        
        self.user = user or self.session.user
        self.conversation = conversation or self.session.conversation
        
        self.intent_parser = get_intent_parser()
        self.context_elicitor = get_context_elicitor()
        self.prompt_synthesizer = get_prompt_synthesizer()
        self.rag_manager = get_rag_manager(user=self.user) if self.user else None
    
    @property
    def session_id(self) -> str:
        """세션 ID"""
        return str(self.session.id)
    
    def update_role(self, role: str):
        """역할 업데이트"""
        self.session.role = role
        self.session.save()
        logger.debug(f"세션 {self.session_id} 역할 업데이트")
    
    def update_task(self, task: str):
        """작업 업데이트"""
        self.session.task = task
        self.session.save()
        logger.debug(f"세션 {self.session_id} 작업 업데이트")
    
    def add_context(self, key: str, value: Any):
        """컨텍스트 추가"""
        self.session.context[key] = value
        self.session.save()
        logger.debug(f"세션 {self.session_id} 컨텍스트 추가: {key}")
    
    def update_context(self, context: Dict[str, Any]):
        """컨텍스트 업데이트 (병합)"""
        self.session.context.update(context)
        self.session.save()
        logger.debug(f"세션 {self.session_id} 컨텍스트 업데이트: {len(context)}개 항목")
    
    def add_constraint(self, constraint: str):
        """제약조건 추가"""
        if constraint not in self.session.constraints:
            self.session.constraints.append(constraint)
            self.session.save()
            logger.debug(f"세션 {self.session_id} 제약조건 추가: {constraint}")
    
    def learn_preference(self, key: str, value: Any):
        """사용자 선호도 학습"""
        self.session.user_preferences[key] = value
        self.session.save()
        logger.debug(f"세션 {self.session_id} 선호도 학습: {key}={value}")
    
    def parse_user_input(self, user_input: str) -> IntentParseResult:
        """
        사용자 입력 파싱
        
        Args:
            user_input: 사용자 입력
        
        Returns:
            IntentParseResult
        """
        logger.info(f"세션 {self.session_id}: 사용자 입력 파싱")
        
        # Intent 파싱
        intent_result = self.intent_parser.parse(user_input)
        
        # DB에 저장
        intent_model = Intent.objects.create(
            session=self.session,
            user_input=user_input,
            cognitive_goal=intent_result.cognitive_goal,
            specificity=intent_result.specificity,
            completeness=intent_result.completeness,
            primary_entities=intent_result.primary_entities,
            constraints=intent_result.constraints,
            confidence=intent_result.confidence
        )
        
        logger.info(f"Intent 저장 완료: {intent_model.id}")
        
        # 작업 자동 업데이트
        if not self.session.task:
            self.update_task(user_input)
        
        return intent_result
    
    def generate_questions(
        self,
        intent: Optional[IntentParseResult] = None
    ) -> List[QuestionItem]:
        """
        컨텍스트 질문 생성
        
        Args:
            intent: Intent (없으면 최근 Intent 사용)
        
        Returns:
            QuestionItem 리스트
        """
        logger.info(f"세션 {self.session_id}: 질문 생성")
        
        # Intent가 없으면 최근 것 사용
        if not intent:
            recent_intent = self.session.intents.first()
            if not recent_intent:
                raise ValueError("Intent가 없습니다. parse_user_input을 먼저 호출하세요.")
            
            intent = IntentParseResult(
                cognitive_goal=recent_intent.cognitive_goal,
                specificity=recent_intent.specificity,
                completeness=recent_intent.completeness,
                primary_entities=recent_intent.primary_entities,
                constraints=recent_intent.constraints,
                confidence=recent_intent.confidence
            )
        
        # 질문 생성
        questions = self.context_elicitor.generate_questions(
            intent=intent,
            existing_context=self.session.context
        )
        
        # DB에 저장
        recent_intent_model = self.session.intents.first()
        if recent_intent_model:
            for q_item in questions:
                Question.objects.create(
                    intent=recent_intent_model,
                    text=q_item.text,
                    priority=q_item.priority,
                    rationale=q_item.rationale,
                    options=q_item.options,
                    default_value=q_item.default or ""
                )
        
        logger.info(f"질문 {len(questions)}개 생성 및 저장 완료")
        
        return questions
    
    def answer_question(self, question_text: str, answer: str):
        """
        질문에 대한 답변 저장
        
        Args:
            question_text: 질문 텍스트
            answer: 답변
        """
        logger.info(f"세션 {self.session_id}: 질문 답변 저장")
        
        # DB에서 질문 찾기
        try:
            question = Question.objects.filter(
                intent__session=self.session,
                text=question_text
            ).first()
            
            if question:
                question.user_answer = answer
                from django.utils import timezone
                question.answered_at = timezone.now()
                question.save()
            
            # 컨텍스트에 추가
            self.add_context(question_text, answer)
            
        except Exception as e:
            logger.error(f"질문 답변 저장 실패: {e}")
    
    def synthesize_prompt(
        self,
        user_input: Optional[str] = None,
        intent: Optional[IntentParseResult] = None,
        output_format: Optional[str] = None,
        specificity_level: SpecificityLevel = SpecificityLevel.VERY_DETAILED,
        use_rag: bool = True
    ) -> str:
        """
        최적화된 프롬프트 합성 (RAG 및 커스텀 지침 통합)
        
        Args:
            user_input: 원본 사용자 입력 (없으면 세션의 task 사용)
            intent: Intent (없으면 최근 Intent 사용)
            output_format: 출력 형식
            specificity_level: 답변의 구체성 수준
            use_rag: RAG를 사용할지 여부
        
        Returns:
            합성된 프롬프트
        """
        logger.info(f"세션 {self.session_id}: 프롬프트 합성 (RAG={use_rag})")
        
        # 사용자 입력 확인 (None이거나 빈 문자열인 경우)
        if not user_input or (isinstance(user_input, str) and not user_input.strip()):
            user_input = self.session.task if self.session.task and self.session.task.strip() else None
        
        if not user_input or (isinstance(user_input, str) and not user_input.strip()):
            raise ValueError("user_input 또는 session.task가 필요합니다.")
        
        # Intent
        if not intent:
            recent_intent = self.session.intents.first()
            if not recent_intent:
                raise ValueError("Intent가 없습니다.")
            
            intent = IntentParseResult(
                cognitive_goal=recent_intent.cognitive_goal,
                specificity=recent_intent.specificity,
                completeness=recent_intent.completeness,
                primary_entities=recent_intent.primary_entities,
                constraints=recent_intent.constraints,
                confidence=recent_intent.confidence
            )
        
        # 기본 프롬프트 합성
        synthesized = self.prompt_synthesizer.synthesize(
            intent=intent,
            context=self.session.context,
            user_input=user_input,
            output_format=output_format,
            specificity_level=specificity_level
        )
        
        # 커스텀 지침 추가
        if self.user:
            try:
                custom_instructions = UserCustomInstructions.objects.get(
                    user=self.user,
                    is_active=True
                )
                synthesized = f"""[사용자 커스텀 지침]
{custom_instructions.instructions}

[사용자 요청]
{synthesized}

위 커스텀 지침을 반드시 따르면서 답변해주세요."""
                logger.info("커스텀 지침 추가됨")
            except UserCustomInstructions.DoesNotExist:
                pass
        
        # RAG 컨텍스트 추가
        if use_rag and self.rag_manager:
            rag_context = self.rag_manager.get_relevant_context(
                query=user_input,
                top_k=3,
                min_similarity=0.7
            )
            if rag_context:
                synthesized = f"""{rag_context}

[현재 질문]
{synthesized}

위 관련 대화 기록을 참고하여 답변해주세요. 이전 대화의 맥락을 이어가되, 현재 질문에 정확히 답변하세요."""
                logger.info(f"RAG 컨텍스트 추가: {len(rag_context)} 문자")
        
        logger.info(f"프롬프트 합성 완료: {len(synthesized)} 문자")
        
        return synthesized
    
    def save_prompt_history(
        self,
        original_prompt: str,
        synthesized_prompt: str,
        model_used: str,
        provider: str,
        response: str,
        tokens_used: int = 0,
        temperature: float = 0.7,
        quality_level: str = 'balanced'
    ) -> PromptHistory:
        """
        프롬프트 이력 저장 (대화 기록에도 저장 및 RAG 메모리 추가)
        
        Args:
            original_prompt: 원본 프롬프트
            synthesized_prompt: 합성된 프롬프트
            model_used: 사용된 모델
            provider: 제공자
            response: LLM 응답
            tokens_used: 사용된 토큰 수
            temperature: 온도
            quality_level: 품질 수준
        
        Returns:
            PromptHistory 객체
        """
        import hashlib
        
        # 프롬프트 해시
        prompt_hash = hashlib.sha256(synthesized_prompt.encode('utf-8')).hexdigest()
        
        history = PromptHistory.objects.create(
            session=self.session,
            prompt_hash=prompt_hash,
            original_prompt=original_prompt,
            synthesized_prompt=synthesized_prompt,
            model_used=model_used,
            provider=provider,
            response=response,
            tokens_used=tokens_used,
            temperature=temperature,
            quality_level=quality_level
        )
        
        logger.info(f"프롬프트 이력 저장: {history.id}")
        
        # 대화 메시지로 저장
        if self.conversation and self.user:
            # 사용자 메시지
            user_message = Message.objects.create(
                conversation=self.conversation,
                role='user',
                content=original_prompt,
                metadata={'tokens': tokens_used // 2}  # 대략적인 추정
            )
            
            # AI 응답 메시지
            assistant_message = Message.objects.create(
                conversation=self.conversation,
                role='assistant',
                content=response,
                metadata={
                    'model': model_used,
                    'provider': provider,
                    'tokens': tokens_used // 2,
                    'temperature': temperature
                }
            )
            
            # RAG 메모리에 추가
            if self.rag_manager:
                self.rag_manager.add_conversation_to_memory(
                    conversation=self.conversation,
                    message=assistant_message
                )
                logger.info("RAG 메모리에 대화 추가")
        
        return history
    
    def add_feedback(
        self,
        feedback_text: str,
        sentiment: str = 'neutral',
        prompt_history_id: Optional[str] = None
    ) -> Feedback:
        """
        피드백 저장
        
        Args:
            feedback_text: 피드백 내용
            sentiment: 감정 (positive/neutral/negative)
            prompt_history_id: 관련 프롬프트 이력 ID
        
        Returns:
            Feedback 객체
        """
        prompt_history = None
        if prompt_history_id:
            try:
                prompt_history = PromptHistory.objects.get(id=prompt_history_id)
            except PromptHistory.DoesNotExist:
                logger.warning(f"프롬프트 이력 {prompt_history_id}를 찾을 수 없음")
        
        feedback = Feedback.objects.create(
            session=self.session,
            prompt_history=prompt_history,
            feedback_text=feedback_text,
            sentiment=sentiment
        )
        
        # 감정 기반 학습
        if sentiment == 'positive':
            self.learn_preference('positive_feedback_count', 
                                  self.session.user_preferences.get('positive_feedback_count', 0) + 1)
        elif sentiment == 'negative':
            self.learn_preference('negative_feedback_count',
                                  self.session.user_preferences.get('negative_feedback_count', 0) + 1)
        
        logger.info(f"피드백 저장: {feedback.id} ({sentiment})")
        
        return feedback
    
    def get_session_summary(self) -> Dict[str, Any]:
        """세션 요약 정보 반환"""
        return {
            'session_id': self.session_id,
            'created_at': self.session.created_at.isoformat(),
            'updated_at': self.session.updated_at.isoformat(),
            'role': self.session.role,
            'task': self.session.task,
            'context_size': len(self.session.context),
            'constraints_count': len(self.session.constraints),
            'intents_count': self.session.intents.count(),
            'prompt_history_count': self.session.prompt_history.count(),
            'feedbacks_count': self.session.feedbacks.count(),
            'user_preferences': self.session.user_preferences,
        }

