# -*- coding: utf-8 -*-
"""
Context Elicitation System - 컨텍스트 도출 시스템

LLM을 활용하여 AI가 최고의 답변을 하기 위해 필요한 정보를 파악하고 질문을 생성합니다.
plainplan.md의 3.1-3.4 원리 기반
"""

import json
import logging
from typing import Dict, Any, Optional, List
from django.conf import settings

from llm_providers.router import get_router, TaskType
from .intent_parser import IntentParseResult

logger = logging.getLogger(__name__)


class QuestionItem:
    """생성된 질문을 담는 데이터 클래스"""
    
    def __init__(
        self,
        text: str,
        priority: int,
        rationale: str,
        options: Optional[List[str]] = None,
        default: Optional[str] = None
    ):
        self.text = text
        self.priority = priority  # 1=최고, 5=최저
        self.rationale = rationale
        self.options = options or []
        self.default = default
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'text': self.text,
            'priority': self.priority,
            'rationale': self.rationale,
            'options': self.options,
            'default': self.default,
        }


class ContextElicitor:
    """
    Context Elicitation 클래스
    
    LLM을 사용하여 Intent를 분석하고 필요한 질문을 생성합니다.
    """
    
    # 시스템 프롬프트 템플릿
    SYSTEM_PROMPT = """당신은 AI가 최고의 답변을 하기 위해 필요한 정보를 파악하는 전문가입니다.

당신의 목표는 **정보 엔트로피를 최대한 줄일 수 있는** 최소한의 핵심 질문을 생성하는 것입니다.

질문 생성 원칙:
1. **정보 이득 최대화**: 각 질문은 답변의 불확실성을 크게 줄여야 함
2. **최소 질문 집합**: 3-4개 이하의 질문으로 핵심 정보 수집
3. **위계적 구조**: Universal → Intent-Specific → Domain-Specific 순서
4. **선택지 우선**: 가능하면 선택지를 제공하여 빠른 답변 유도
5. **디폴트 제공**: 합리적인 기본값 설정으로 friction 최소화

질문 유형:
- **Level 0 (Universal)**: 모든 의도에 필요 (숙련도, 목적, 제약)
- **Level 1 (Intent-Specific)**: 특정 인지적 목표에 필요
- **Level 2 (Domain-Specific)**: 특정 도메인에만 의미 있는 정보

반드시 다음 JSON 형식으로만 응답하세요:
```json
{
  "questions": [
    {
      "text": "질문 내용",
      "priority": 1,
      "rationale": "왜 이 질문이 필요한가",
      "options": ["선택1", "선택2", "선택3"],
      "default": "선택1"
    }
  ]
}
```

priority는 1(최고 우선순위) ~ 5(최저 우선순위)입니다.
options는 선택지가 있을 경우에만 제공하세요."""
    
    def __init__(self):
        """Context Elicitor 초기화"""
        self.router = get_router()
        self.model_config = settings.PROMPT_MATE.get('CONTEXT_ELICITOR_MODEL', 'gpt-4o-mini')
        self.max_questions = settings.PROMPT_MATE.get('MAX_CONTEXT_QUESTIONS', 4)
    
    def generate_questions(
        self,
        intent: IntentParseResult,
        existing_context: Optional[Dict[str, Any]] = None,
        previous_answers: Optional[List[Dict[str, str]]] = None
    ) -> List[QuestionItem]:
        """
        Intent 기반 질문 생성
        
        Args:
            intent: 파싱된 Intent
            existing_context: 이미 수집된 컨텍스트 (선택적)
            previous_answers: 이전 답변들 (선택적, 적응적 질문용)
        
        Returns:
            QuestionItem 리스트
        
        Raises:
            Exception: 질문 생성 실패 시
        """
        logger.info(f"컨텍스트 질문 생성 시작: {intent.cognitive_goal}")
        
        # 프롬프트 구성
        prompt = self._build_prompt(intent, existing_context, previous_answers)
        
        # LLM 호출
        try:
            provider, model, temperature = self.router.get_provider(TaskType.CONTEXT_QUESTIONS)
            
            logger.debug(f"질문 생성에 사용: {provider.__class__.__name__}, {model}")
            
            # JSON 모드로 생성
            response_json = provider.generate_json(
                prompt=prompt,
                model=model,
                temperature=temperature,
                system_prompt=self.SYSTEM_PROMPT
            )
            
            # 결과 파싱
            questions = self._parse_response(response_json)
            
            # 최대 개수로 제한
            questions = questions[:self.max_questions]
            
            logger.info(f"질문 생성 완료: {len(questions)}개")
            
            return questions
        
        except Exception as e:
            logger.error(f"질문 생성 실패: {e}")
            # 폴백: 기본 질문 반환
            return self._create_fallback_questions(intent)
    
    def _build_prompt(
        self,
        intent: IntentParseResult,
        existing_context: Optional[Dict[str, Any]] = None,
        previous_answers: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """프롬프트 구성"""
        prompt_parts = []
        
        # Intent 정보
        intent_info = f"""**사용자의 의도:**
- 인지적 목표: {intent.cognitive_goal}
- 구체성: {intent.specificity}
- 완결성: {intent.completeness}
- 핵심 엔티티: {', '.join(intent.primary_entities) if intent.primary_entities else '없음'}
- 제약조건: {', '.join(intent.constraints) if intent.constraints else '없음'}
- 신뢰도: {intent.confidence:.2f}"""
        
        prompt_parts.append(intent_info)
        
        # 이미 수집된 컨텍스트
        if existing_context:
            context_info = "\n**이미 수집된 정보:**\n"
            for key, value in existing_context.items():
                context_info += f"- {key}: {value}\n"
            prompt_parts.append(context_info)
        
        # 이전 답변들
        if previous_answers:
            answers_info = "\n**이전 답변:**\n"
            for answer in previous_answers:
                answers_info += f"- Q: {answer.get('question', '')}\n"
                answers_info += f"  A: {answer.get('answer', '')}\n"
            prompt_parts.append(answers_info)
        
        # 지시사항
        instruction = f"""
위 정보를 바탕으로, AI가 최고의 답변을 하기 위해 **반드시 필요한 정보**를 수집하는 질문을 생성하세요.

- 최대 {self.max_questions}개의 질문만 생성
- 정보 이득이 높은 순서로 우선순위 설정
- 가능하면 선택지와 기본값 제공
- 이미 수집된 정보는 다시 묻지 마세요

JSON 형식으로 응답하세요."""
        
        prompt_parts.append(instruction)
        
        return "\n".join(prompt_parts)
    
    def _parse_response(self, response_json: Dict[str, Any]) -> List[QuestionItem]:
        """LLM 응답을 QuestionItem 리스트로 변환"""
        questions = []
        
        try:
            questions_data = response_json.get('questions', [])
            
            for q_data in questions_data:
                text = q_data.get('text', '')
                priority = int(q_data.get('priority', 3))
                rationale = q_data.get('rationale', '')
                options = q_data.get('options', [])
                default = q_data.get('default')
                
                # 유효성 검사
                if not text or not rationale:
                    logger.warning(f"불완전한 질문 데이터: {q_data}")
                    continue
                
                # priority 범위 제한
                priority = max(1, min(5, priority))
                
                question = QuestionItem(
                    text=text,
                    priority=priority,
                    rationale=rationale,
                    options=options if isinstance(options, list) else [],
                    default=default
                )
                
                questions.append(question)
            
            # 우선순위 순으로 정렬
            questions.sort(key=lambda q: q.priority)
            
            return questions
        
        except Exception as e:
            logger.error(f"질문 응답 파싱 실패: {e}, 원본: {response_json}")
            return []
    
    def _create_fallback_questions(self, intent: IntentParseResult) -> List[QuestionItem]:
        """폴백 질문 생성 (LLM 실패 시)"""
        logger.warning("폴백 질문 생성")
        
        questions = []
        
        # Universal 질문
        if intent.completeness != 'COMPLETE':
            questions.append(QuestionItem(
                text="최종 산출물의 사용 목적과 대상 사용자는 누구인가요?",
                priority=1,
                rationale="목적과 대상을 알아야 적절한 수준과 형식으로 답변 가능",
                options=["개인 학습용", "업무용", "발표/공유용", "기타"],
                default="개인 학습용"
            ))
            
            questions.append(QuestionItem(
                text="당신의 경험 수준은 어느 정도인가요?",
                priority=2,
                rationale="경험 수준에 따라 설명의 깊이와 전문 용어 사용 조절",
                options=["초보", "중급", "고급"],
                default="중급"
            ))
        
        # Intent-specific 질문
        if intent.cognitive_goal == '만들기':
            questions.append(QuestionItem(
                text="선호하는 출력 형식이 있나요?",
                priority=2,
                rationale="형식을 미리 알면 재작업 시간 절약",
                options=["Markdown", "JSON", "일반 텍스트", "HTML"],
                default="Markdown"
            ))
        elif intent.cognitive_goal == '하기':
            questions.append(QuestionItem(
                text="이미 시도해본 방법이 있나요?",
                priority=1,
                rationale="시도한 방법을 알면 중복을 피하고 더 나은 해결책 제시 가능",
                options=[],
                default=None
            ))
        
        # 최대 개수로 제한
        return questions[:self.max_questions]
    
    def adaptive_follow_up(
        self,
        original_questions: List[QuestionItem],
        answers: Dict[str, str],
        intent: IntentParseResult
    ) -> List[QuestionItem]:
        """
        답변 기반 적응적 후속 질문 생성
        
        Args:
            original_questions: 원래 질문들
            answers: 답변 딕셔너리 {question_text: answer}
            intent: Intent
        
        Returns:
            후속 질문 리스트
        """
        logger.info("적응적 후속 질문 생성")
        
        # 답변을 리스트 형식으로 변환
        previous_answers = [
            {'question': q, 'answer': a}
            for q, a in answers.items()
        ]
        
        # 새로운 질문 생성
        try:
            return self.generate_questions(
                intent=intent,
                existing_context=answers,
                previous_answers=previous_answers
            )
        except Exception as e:
            logger.error(f"적응적 질문 생성 실패: {e}")
            return []


# 전역 Elicitor 인스턴스
_elicitor_instance: Optional[ContextElicitor] = None


def get_context_elicitor() -> ContextElicitor:
    """전역 Context Elicitor 인스턴스 가져오기 (싱글톤)"""
    global _elicitor_instance
    if _elicitor_instance is None:
        _elicitor_instance = ContextElicitor()
    return _elicitor_instance

