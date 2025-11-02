# -*- coding: utf-8 -*-
"""
Prompt Synthesis Engine - 프롬프트 합성 엔진

Intent와 Context를 최적화된 프롬프트로 합성합니다.
plainplan.md의 4.1-4.3 원리 기반
"""

import logging
import re
from typing import Dict, Any, Optional, List
from enum import Enum
from django.conf import settings

from .intent_parser import IntentParseResult

logger = logging.getLogger(__name__)


class SpecificityLevel(str, Enum):
    """답변 구체성 레벨"""
    SHORT = "짧음"
    CONCISE = "간결"
    NORMAL = "보통"
    DETAILED = "구체적"
    VERY_DETAILED = "매우 구체적"


class PromptSynthesizer:
    """
    Prompt Synthesis 클래스
    
    5요소 구조 (Role + Task + Context + Constraints + Format)로 
    최적화된 프롬프트를 생성합니다.
    """
    
    # 인지적 목표별 Role 템플릿
    ROLE_TEMPLATES = {
        '알기': "당신은 {domain} 전문가입니다. 정확하고 이해하기 쉬운 설명을 제공합니다.",
        '하기': "당신은 {domain} 문제 해결 전문가입니다. 실용적이고 검증된 해결책을 제시합니다.",
        '만들기': "당신은 {domain} 창작 전문가입니다. 창의적이면서도 구조화된 결과물을 생성합니다.",
        '배우기': "당신은 {domain} 교육 전문가입니다. 단계적이고 체계적인 학습 자료를 제공합니다.",
    }
    
    # 인지적 목표별 Format 지시
    FORMAT_TEMPLATES = {
        '알기': "설명은 핵심 개념 → 상세 내용 → 예시 순으로 구성하세요.",
        '하기': "해결책은 문제 분석 → 해결 방법 → 구현 단계 → 검증 방법 순으로 작성하세요.",
        '만들기': "결과물은 구조화되고 완성도가 높아야 하며, 필요시 여러 버전을 제시하세요.",
        '배우기': "학습 자료는 1) 개념 소개 2) 예시 3) 연습 문제 4) 요약 순으로 구성하세요.",
    }
    
    def __init__(self):
        """Prompt Synthesizer 초기화"""
        self.token_budget = settings.PROMPT_MATE.get('TOKEN_BUDGET', 1500)
    
    def synthesize(
        self,
        intent: IntentParseResult,
        context: Dict[str, Any],
        user_input: str,
        output_format: Optional[str] = None,
        specificity_level: SpecificityLevel = SpecificityLevel.VERY_DETAILED
    ) -> str:
        """
        프롬프트 합성
        
        Args:
            intent: 파싱된 Intent
            context: 수집된 컨텍스트
            user_input: 원본 사용자 입력
            output_format: 출력 형식 (선택적)
            specificity_level: 답변의 구체성 수준
        
        Returns:
            합성된 프롬프트
        """
        logger.info(f"프롬프트 합성 시작: {intent.cognitive_goal}")
        
        # 1. Role 생성
        role = self._generate_role(intent, context)
        
        # 2. Task 생성
        task = self._generate_task(intent, user_input, context)
        
        # 3. Context 구조화
        context_section = self._structure_context(intent, context)
        
        # 4. Constraints 추출
        constraints_section = self._extract_constraints(intent, context)
        
        # 5. Format 지시
        format_section = output_format or self._select_format(intent)
        
        # 5.5. 구체성 레벨 적용
        specificity_instruction = self._apply_specificity_level(specificity_level)
        
        # 6. 프롬프트 조립
        prompt = self._assemble_prompt(
            role=role,
            task=task,
            context=context_section,
            constraints=constraints_section,
            format_spec=format_section,
            specificity=specificity_instruction
        )
        
        # 7. 최적화
        optimized_prompt = self.optimize(prompt)
        
        logger.info(f"프롬프트 합성 완료: {len(optimized_prompt)} 문자")
        
        return optimized_prompt
    
    def _generate_role(self, intent: IntentParseResult, context: Dict[str, Any]) -> str:
        """Role 생성"""
        template = self.ROLE_TEMPLATES.get(intent.cognitive_goal, self.ROLE_TEMPLATES['알기'])
        
        # 도메인 추출
        domain = "전문"
        if intent.primary_entities:
            domain = intent.primary_entities[0]
        elif context.get('domain'):
            domain = context['domain']
        
        return template.format(domain=domain)
    
    def _generate_task(
        self,
        intent: IntentParseResult,
        user_input: str,
        context: Dict[str, Any]
    ) -> str:
        """Task 명세 생성"""
        # 동사 선택
        task_verbs = {
            '알기': '설명하고 분석하세요',
            '하기': '해결하고 구현하세요',
            '만들기': '생성하고 작성하세요',
            '배우기': '가르치고 안내하세요',
        }
        
        verb = task_verbs.get(intent.cognitive_goal, '처리하세요')
        
        # 사용자 입력을 명확한 작업으로 변환
        task = f"다음 요청을 {verb}:\n{user_input}"
        
        return task
    
    def _structure_context(self, intent: IntentParseResult, context: Dict[str, Any]) -> str:
        """Context 구조화"""
        context_lines = []
        
        # Intent 정보
        if intent.specificity == 'LOW':
            context_lines.append(f"- 요청이 추상적이므로 구체적인 예시를 포함하세요")
        
        # 사용자 컨텍스트
        if context.get('expertise_level'):
            expertise_map = {
                '초보': '초보자를 위해 전문 용어를 최소화하고 기본 개념부터 설명하세요',
                '중급': '중급 수준으로 적절한 깊이와 실용적인 예시를 제공하세요',
                '고급': '고급 사용자를 위해 심화 내용과 최적화 기법을 포함하세요',
            }
            if context['expertise_level'] in expertise_map:
                context_lines.append(f"- {expertise_map[context['expertise_level']]}")
        
        if context.get('purpose'):
            purpose_map = {
                '개인 학습용': '개인 학습에 적합하도록 이해 중심으로 작성하세요',
                '업무용': '업무에 바로 적용 가능하도록 실용적으로 작성하세요',
                '발표/공유용': '발표나 공유를 고려하여 형식을 갖추어 작성하세요',
            }
            if context['purpose'] in purpose_map:
                context_lines.append(f"- {purpose_map[context['purpose']]}")
        
        # 도메인별 컨텍스트
        for key, value in context.items():
            if key not in ['expertise_level', 'purpose', 'domain'] and value:
                context_lines.append(f"- {key}: {value}")
        
        if not context_lines:
            return ""
        
        return "[맥락]\n" + "\n".join(context_lines)
    
    def _extract_constraints(self, intent: IntentParseResult, context: Dict[str, Any]) -> str:
        """Constraints 추출"""
        constraints = []
        
        # Intent의 제약조건
        if intent.constraints:
            constraints.extend(intent.constraints)
        
        # Context의 제약조건
        if context.get('length'):
            constraints.append(f"길이: {context['length']}")
        
        if context.get('time_limit'):
            constraints.append(f"시간 제한: {context['time_limit']}")
        
        if context.get('format_preference'):
            constraints.append(f"형식: {context['format_preference']}")
        
        if not constraints:
            return ""
        
        return "[제약조건]\n" + "\n".join([f"- {c}" for c in constraints])
    
    def _select_format(self, intent: IntentParseResult) -> str:
        """Format 지시 선택"""
        template = self.FORMAT_TEMPLATES.get(intent.cognitive_goal, "")
        
        if template:
            return f"[출력 형식]\n{template}"
        
        return ""
    
    def _apply_specificity_level(self, level: SpecificityLevel) -> str:
        """
        구체성 레벨에 따른 지시사항 생성
        
        Args:
            level: 구체성 레벨
        
        Returns:
            구체성 지시사항
        """
        instructions = {
            SpecificityLevel.SHORT: """1-2문장으로 핵심만 간단히 답변하세요.
- 불필요한 설명 제거
- 가장 중요한 정보만 포함""",
            
            SpecificityLevel.CONCISE: """3-5문장으로 요약하여 답변하세요.
- 핵심 내용 중심
- 간단한 예시 1개 포함 (필요시)
- 군더더기 없이 명확하게""",
            
            SpecificityLevel.NORMAL: """적당한 설명과 예시를 포함하여 답변하세요.
- 주요 개념 설명
- 실용적인 예시 1-2개
- 이해하기 쉬운 구조""",
            
            SpecificityLevel.DETAILED: """상세한 설명과 여러 예시를 포함하여 답변하세요.
- 깊이 있는 설명
- 다양한 예시 3개 이상
- 단계별 설명 (필요시)
- 배경 정보와 맥락 포함""",
            
            SpecificityLevel.VERY_DETAILED: """매우 깊이 있고 포괄적으로 답변하세요.
- 철저하고 상세한 분석
- 다양한 관점과 접근법
- 풍부한 예시 5개 이상
- 모든 관련 세부사항 포함
- 장단점, 고려사항, 주의점 등 포함
- 추가 학습 자료나 참고사항 언급"""
        }
        
        instruction = instructions.get(level, instructions[SpecificityLevel.VERY_DETAILED])
        return f"[답변 구체성]\n{instruction}"
    
    def _assemble_prompt(
        self,
        role: str,
        task: str,
        context: str,
        constraints: str,
        format_spec: str,
        specificity: str = ""
    ) -> str:
        """프롬프트 조립"""
        sections = []
        
        if role:
            sections.append(f"[역할]\n{role}")
        
        if task:
            sections.append(f"[작업]\n{task}")
        
        if context:
            sections.append(context)
        
        if constraints:
            sections.append(constraints)
        
        if specificity:
            sections.append(specificity)
        
        if format_spec:
            sections.append(format_spec)
        
        return "\n\n".join(sections)
    
    def optimize(self, prompt: str) -> str:
        """
        프롬프트 최적화
        
        Args:
            prompt: 원본 프롬프트
        
        Returns:
            최적화된 프롬프트
        """
        logger.debug("프롬프트 최적화 시작")
        
        optimized = prompt
        
        # 1. 불필요한 공백 제거
        optimized = re.sub(r'\n{3,}', '\n\n', optimized)  # 3개 이상 개행 → 2개로
        optimized = re.sub(r' +', ' ', optimized)  # 연속 공백 → 단일 공백
        
        # 2. 중복 라인 제거
        lines = optimized.split('\n')
        seen = set()
        unique_lines = []
        for line in lines:
            normalized = line.strip().lower()
            if normalized and normalized not in seen:
                unique_lines.append(line)
                seen.add(normalized)
            elif not normalized:  # 빈 줄은 유지
                unique_lines.append(line)
        
        optimized = '\n'.join(unique_lines)
        
        # 3. 토큰 예산 초과 시 압축
        estimated_tokens = len(optimized) // 4  # 근사치
        if estimated_tokens > self.token_budget:
            logger.warning(f"토큰 예산 초과: {estimated_tokens} > {self.token_budget}, 압축 진행")
            optimized = self._compress(optimized, self.token_budget)
        
        savings = 1.0 - (len(optimized) / (len(prompt) + 0.001))
        logger.debug(f"최적화 완료: {savings * 100:.1f}% 절약")
        
        return optimized.strip()
    
    def _compress(self, prompt: str, token_budget: int) -> str:
        """프롬프트 압축 (토큰 예산 초과 시)"""
        # 섹션별로 분할
        sections = prompt.split('\n\n')
        
        # 우선순위: Role < Context < Constraints < Format < Task
        # Task는 가장 중요하므로 마지막에 유지
        
        compressed_sections = []
        current_tokens = 0
        target_chars = token_budget * 4  # 토큰 → 문자 근사
        
        for section in sections:
            section_tokens = len(section) // 4
            if current_tokens + section_tokens <= token_budget:
                compressed_sections.append(section)
                current_tokens += section_tokens
            else:
                # 남은 예산 내에서 축약
                remaining = target_chars - (current_tokens * 4)
                if remaining > 100:  # 최소 100자는 있어야 의미 있음
                    compressed = section[:remaining] + "..."
                    compressed_sections.append(compressed)
                break
        
        return '\n\n'.join(compressed_sections)
    
    def estimate_tokens(self, text: str) -> int:
        """텍스트의 토큰 수 추정"""
        # 한글/영문 혼합 고려
        korean_chars = len([c for c in text if '가' <= c <= '힣'])
        other_chars = len(text) - korean_chars
        estimated = (korean_chars * 2) + (other_chars // 4)
        return max(1, estimated)


# 전역 Synthesizer 인스턴스
_synthesizer_instance: Optional[PromptSynthesizer] = None


def get_prompt_synthesizer() -> PromptSynthesizer:
    """전역 Prompt Synthesizer 인스턴스 가져오기 (싱글톤)"""
    global _synthesizer_instance
    if _synthesizer_instance is None:
        _synthesizer_instance = PromptSynthesizer()
    return _synthesizer_instance

