# -*- coding: utf-8 -*-
"""
Intent Parser - 의도 파싱 엔진

LLM을 활용하여 사용자의 자연어 입력에서 진짜 의도를 파악합니다.
plainplan.md의 2.1-2.3 원리 기반
"""

import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from django.conf import settings

from llm_providers.router import get_router, TaskType

logger = logging.getLogger(__name__)


class IntentParseResult:
    """의도 파싱 결과를 담는 데이터 클래스"""
    
    def __init__(
        self,
        cognitive_goal: str,
        specificity: str,
        completeness: str,
        primary_entities: List[str],
        constraints: List[str],
        confidence: float,
        raw_response: Optional[Dict[str, Any]] = None
    ):
        self.cognitive_goal = cognitive_goal
        self.specificity = specificity
        self.completeness = completeness
        self.primary_entities = primary_entities
        self.constraints = constraints
        self.confidence = confidence
        self.raw_response = raw_response
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'cognitive_goal': self.cognitive_goal,
            'specificity': self.specificity,
            'completeness': self.completeness,
            'primary_entities': self.primary_entities,
            'constraints': self.constraints,
            'confidence': self.confidence,
        }
    
    def needs_clarification(self, threshold: float = 0.7) -> bool:
        """명확화가 필요한지 판단"""
        return self.confidence < threshold


class IntentParser:
    """
    Intent Parser 클래스
    
    LLM을 사용하여 사용자 입력에서 의도를 파싱합니다.
    """
    
    # 시스템 프롬프트 템플릿
    SYSTEM_PROMPT = """당신은 사용자의 자연어 입력에서 진짜 의도를 파악하는 전문가입니다.

사용자의 입력을 다음 3가지 차원으로 분석하세요:

1. **인지적 목표 (Cognitive Goal)**:
   - "알기": 정보 획득, 이해, 비교, 설명 요청
   - "하기": 문제 해결, 실행, 변환, 디버깅
   - "만들기": 생성, 작성, 디자인, 창작
   - "배우기": 학습, 연습, 숙달, 가이드 요청

2. **구체성 수준 (Specificity Level)**:
   - "LOW": 추상적, 모호함 ("행복", "성공" 등)
   - "MEDIUM": 범주적 ("파이썬", "마케팅" 등)
   - "HIGH": 구체적, 명확함 ("Flask 에러 500", "인스타 광고 CTR 개선" 등)

3. **완결성 (Completeness)**:
   - "INCOMPLETE": 필수 정보 크게 부족
   - "PARTIAL": 일부 정보만 있음
   - "COMPLETE": 충분한 정보 포함

또한 다음을 추출하세요:
- **primary_entities**: 핵심 키워드, 엔티티, 기술명, 도메인 용어 (배열)
- **constraints**: 명시된 제약조건 (시간, 비용, 형식, 길이 등) (배열)
- **confidence**: 분석의 신뢰도 (0.0-1.0)

반드시 다음 JSON 형식으로만 응답하세요:
```json
{
  "cognitive_goal": "알기|하기|만들기|배우기",
  "specificity": "LOW|MEDIUM|HIGH",
  "completeness": "INCOMPLETE|PARTIAL|COMPLETE",
  "primary_entities": ["키워드1", "키워드2"],
  "constraints": ["제약1", "제약2"],
  "confidence": 0.85
}
```"""
    
    def __init__(self):
        """Intent Parser 초기화"""
        self.router = get_router()
        self.model_config = settings.PROMPT_MATE.get('INTENT_PARSER_MODEL', 'gpt-4o-mini')
    
    def parse(
        self,
        user_input: str,
        history: Optional[List[str]] = None
    ) -> IntentParseResult:
        """
        사용자 입력을 파싱하여 의도 추출
        
        Args:
            user_input: 사용자의 자연어 입력
            history: 대화 히스토리 (선택적)
        
        Returns:
            IntentParseResult 객체
        
        Raises:
            Exception: 파싱 실패 시
        """
        logger.info(f"Intent 파싱 시작: {user_input[:50]}...")
        
        # 프롬프트 구성
        prompt = self._build_prompt(user_input, history)
        
        # LLM 호출
        try:
            provider, model, temperature = self.router.get_provider(TaskType.INTENT_PARSING)
            
            logger.debug(f"Intent 파싱에 사용: {provider.__class__.__name__}, {model}")
            
            # JSON 모드로 생성
            response_json = provider.generate_json(
                prompt=prompt,
                model=model,
                temperature=temperature,
                system_prompt=self.SYSTEM_PROMPT
            )
            
            # 결과 파싱
            result = self._parse_response(response_json, user_input)
            
            logger.info(f"Intent 파싱 완료: {result.cognitive_goal} (신뢰도: {result.confidence:.2f})")
            
            return result
        
        except Exception as e:
            logger.error(f"Intent 파싱 실패: {e}")
            # 폴백: 기본 Intent 반환
            return self._create_fallback_intent(user_input)
    
    def _build_prompt(self, user_input: str, history: Optional[List[str]] = None) -> str:
        """프롬프트 구성"""
        prompt_parts = [f"사용자 입력: {user_input}"]
        
        if history:
            history_text = "\n".join([f"- {h}" for h in history[-3:]])  # 최근 3개만
            prompt_parts.append(f"\n대화 히스토리:\n{history_text}")
        
        prompt_parts.append("\n위 입력을 분석하여 JSON 형식으로 응답하세요.")
        
        return "\n".join(prompt_parts)
    
    def _parse_response(self, response_json: Dict[str, Any], user_input: str) -> IntentParseResult:
        """LLM 응답을 IntentParseResult로 변환"""
        try:
            # 필수 필드 검증
            cognitive_goal = response_json.get('cognitive_goal', '알기')
            specificity = response_json.get('specificity', 'MEDIUM')
            completeness = response_json.get('completeness', 'PARTIAL')
            primary_entities = response_json.get('primary_entities', [])
            constraints = response_json.get('constraints', [])
            confidence = float(response_json.get('confidence', 0.5))
            
            # 유효성 검사
            if cognitive_goal not in ['알기', '하기', '만들기', '배우기']:
                logger.warning(f"잘못된 cognitive_goal: {cognitive_goal}, 기본값 사용")
                cognitive_goal = '알기'
            
            if specificity not in ['LOW', 'MEDIUM', 'HIGH']:
                logger.warning(f"잘못된 specificity: {specificity}, 기본값 사용")
                specificity = 'MEDIUM'
            
            if completeness not in ['INCOMPLETE', 'PARTIAL', 'COMPLETE']:
                logger.warning(f"잘못된 completeness: {completeness}, 기본값 사용")
                completeness = 'PARTIAL'
            
            # 신뢰도 범위 검증
            confidence = max(0.0, min(1.0, confidence))
            
            return IntentParseResult(
                cognitive_goal=cognitive_goal,
                specificity=specificity,
                completeness=completeness,
                primary_entities=primary_entities,
                constraints=constraints,
                confidence=confidence,
                raw_response=response_json
            )
        
        except Exception as e:
            logger.error(f"응답 파싱 실패: {e}, 원본 응답: {response_json}")
            return self._create_fallback_intent(user_input)
    
    def _create_fallback_intent(self, user_input: str) -> IntentParseResult:
        """폴백 Intent 생성 (LLM 실패 시)"""
        logger.warning("폴백 Intent 생성")
        
        # 간단한 휴리스틱 분석
        text_lower = user_input.lower()
        
        # 인지적 목표 추정
        if any(word in text_lower for word in ['만들', 'create', 'generate', '생성', '작성']):
            cognitive_goal = '만들기'
        elif any(word in text_lower for word in ['해결', 'fix', 'debug', '고치', '수정']):
            cognitive_goal = '하기'
        elif any(word in text_lower for word in ['배우', 'learn', '공부', '연습']):
            cognitive_goal = '배우기'
        else:
            cognitive_goal = '알기'
        
        # 구체성 추정
        word_count = len(user_input.split())
        if word_count > 15 or any(c.isdigit() for c in user_input):
            specificity = 'HIGH'
        elif word_count > 5:
            specificity = 'MEDIUM'
        else:
            specificity = 'LOW'
        
        # 완결성 추정
        if word_count < 5:
            completeness = 'INCOMPLETE'
        elif word_count < 10:
            completeness = 'PARTIAL'
        else:
            completeness = 'COMPLETE'
        
        return IntentParseResult(
            cognitive_goal=cognitive_goal,
            specificity=specificity,
            completeness=completeness,
            primary_entities=[],
            constraints=[],
            confidence=0.3,  # 낮은 신뢰도
            raw_response=None
        )
    
    def batch_parse(self, user_inputs: List[str]) -> List[IntentParseResult]:
        """
        여러 입력을 일괄 파싱
        
        Args:
            user_inputs: 사용자 입력 리스트
        
        Returns:
            IntentParseResult 리스트
        """
        results = []
        for user_input in user_inputs:
            try:
                result = self.parse(user_input)
                results.append(result)
            except Exception as e:
                logger.error(f"일괄 파싱 중 오류: {e}")
                results.append(self._create_fallback_intent(user_input))
        
        return results


# 전역 Parser 인스턴스
_parser_instance: Optional[IntentParser] = None


def get_intent_parser() -> IntentParser:
    """전역 Intent Parser 인스턴스 가져오기 (싱글톤)"""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = IntentParser()
    return _parser_instance

