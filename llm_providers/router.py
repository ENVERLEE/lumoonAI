# -*- coding: utf-8 -*-
"""
LLM Model Router

작업 복잡도와 품질 요구사항에 따라 최적의 모델과 제공자를 선택하는 라우터
"""

import logging
from typing import Optional, Dict, Any, Tuple
from enum import Enum

from django.conf import settings

from .base import BaseLLMProvider, LLMProviderError
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .google_provider import GoogleProvider
from .perplexity_provider import PerplexityProvider
from core.usage_decorator import can_use_model, get_user_subscription

logger = logging.getLogger(__name__)


class TaskType(str, Enum):
    """작업 유형"""
    INTENT_PARSING = "intent_parsing"
    CONTEXT_QUESTIONS = "context_questions"
    PROMPT_SYNTHESIS = "prompt_synthesis"
    FINAL_GENERATION = "final_generation"
    REFINEMENT = "refinement"


class QualityLevel(str, Enum):
    """품질 수준"""
    LOW = "low"
    BALANCED = "balanced"
    HIGH = "high"


class ModelRouter:
    """
    LLM 모델 라우터
    
    작업 유형과 품질 요구사항에 따라 최적의 제공자와 모델을 선택합니다.
    """
    
    # 작업별 모델 전략
    TASK_MODEL_STRATEGY = {
        TaskType.INTENT_PARSING: {
            'provider': 'openai',
            'model': 'gpt-5-nano',
            'temperature': 0.3,
            'rationale': '의도 파싱은 초경량 모델로 충분 (빠른 응답 + 저비용)'
        },
        TaskType.CONTEXT_QUESTIONS: {
            'provider': 'openai',
            'model': 'gpt-5-nano',
            'temperature': 0.4,
            'rationale': '질문 생성은 경량 모델로 충분'
        },
        TaskType.PROMPT_SYNTHESIS: {
            'provider': 'openai',
            'model': 'gpt-5-nano',
            'temperature': 0.2,
            'rationale': '프롬프트 합성은 경량 모델로 처리'
        },
        TaskType.FINAL_GENERATION: {
            QualityLevel.LOW: {
                'provider': 'openai',
                'model': 'gpt-5-nano',
                'temperature': 0.7,
            },
            QualityLevel.BALANCED: {
                'provider': 'openai',
                'model': 'gpt-5-mini',
                'temperature': 0.7,
            },
            QualityLevel.HIGH: {
                'provider': 'openai',
                'model': 'gpt-4o',
                'temperature': 0.8,
            },
        },
        TaskType.REFINEMENT: {
            'provider': 'openai',
            'model': 'gpt-5-nano',
            'temperature': 0.5,
            'rationale': '개선은 경량 모델로 충분'
        },
    }
    
    def __init__(self):
        """Router 초기화"""
        self._providers: Dict[str, BaseLLMProvider] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """사용 가능한 제공자 초기화"""
        # OpenAI
        openai_key = settings.OPENAI_API_KEY
        if openai_key:
            try:
                self._providers['openai'] = OpenAIProvider(api_key=openai_key)
                logger.info("OpenAI Provider 초기화 완료")
            except Exception as e:
                logger.warning(f"OpenAI Provider 초기화 실패: {e}")
        
        # Anthropic
        anthropic_key = settings.ANTHROPIC_API_KEY
        if anthropic_key:
            try:
                self._providers['anthropic'] = AnthropicProvider(api_key=anthropic_key)
                logger.info("Anthropic Provider 초기화 완료")
            except Exception as e:
                logger.warning(f"Anthropic Provider 초기화 실패: {e}")
        
        # Google
        google_key = settings.GOOGLE_API_KEY
        if google_key:
            try:
                self._providers['google'] = GoogleProvider(api_key=google_key)
                logger.info("Google Provider 초기화 완료")
            except Exception as e:
                logger.warning(f"Google Provider 초기화 실패: {e}")
        
        # Perplexity
        perplexity_key = settings.PERPLEXITY_API_KEY
        if perplexity_key:
            try:
                self._providers['perplexity'] = PerplexityProvider(api_key=perplexity_key)
                logger.info("Perplexity Provider 초기화 완료")
            except Exception as e:
                logger.warning(f"Perplexity Provider 초기화 실패: {e}")
        
        if not self._providers:
            logger.error("사용 가능한 LLM 제공자가 없습니다! API 키를 확인하세요.")
    
    def get_provider(
        self,
        task_type: TaskType,
        quality: QualityLevel = QualityLevel.BALANCED,
        preferred_provider: Optional[str] = None,
        user=None,
        preferred_model: Optional[str] = None
    ) -> Tuple[BaseLLMProvider, str, float]:
        """
        작업 유형에 맞는 제공자와 모델 선택
        
        Args:
            task_type: 작업 유형
            quality: 품질 수준 (FINAL_GENERATION에만 적용)
            preferred_provider: 선호 제공자 (선택적)
            user: 사용자 객체 (플랜 확인용)
            preferred_model: 선호 모델 (FINAL_GENERATION에서만 사용 가능)
        
        Returns:
            (provider, model, temperature) 튜플
        
        Raises:
            LLMProviderError: 사용 가능한 제공자가 없을 때
        """
        # 전략 가져오기
        strategy = self.TASK_MODEL_STRATEGY.get(task_type)
        
        if not strategy:
            raise LLMProviderError(f"알 수 없는 작업 유형: {task_type}")
        
        # FINAL_GENERATION은 품질 수준별 전략
        if task_type == TaskType.FINAL_GENERATION:
            # 사용자가 모델을 선택한 경우
            if preferred_model and user:
                # 플랜 기반 권한 확인
                if not can_use_model(user, preferred_model):
                    logger.warning(
                        f"사용자 {user.username if user.is_authenticated else 'anonymous'}는 "
                        f"{preferred_model} 모델을 사용할 수 없습니다. "
                        f"플랜에 맞는 모델로 대체합니다."
                    )
                    preferred_model = None
            
            # 선호 모델이 있고 권한이 있으면 사용
            if preferred_model:
                # 선호 모델에 맞는 전략 찾기
                strategy_for_model = self._get_strategy_for_model(preferred_model, quality)
                if strategy_for_model:
                    provider_name = strategy_for_model['provider']
                    model = preferred_model
                    temperature = strategy_for_model.get('temperature', 0.7)
                else:
                    # 전략이 없으면 기본 전략 사용
                    strategy = strategy.get(quality, strategy[QualityLevel.BALANCED])
                    provider_name = preferred_provider or strategy['provider']
                    model = preferred_model  # 사용자가 선택한 모델 강제 사용
                    temperature = strategy.get('temperature', 0.7)
            else:
                # 기본 전략 사용 (플랜 기반 필터링)
                strategy = strategy.get(quality, strategy[QualityLevel.BALANCED])

                # 사용자 플랜에 맞는 모델로 필터링
                if user:
                    subscription, plan = get_user_subscription(user)
                    if plan and plan.plan_type == 'free':
                        # 무료 플랜은 gpt-5-nano만 사용 가능
                        model = 'gpt-5-nano'
                        provider_name = 'openai'
                        temperature = 0.7
                    else:
                        # 유료 플랜은 전략대로 선택하되, 플랜의 허용 모델 확인
                        model = strategy['model']
                        provider_name = preferred_provider or strategy['provider']
                        temperature = strategy['temperature']
                        
                        # 모델이 플랜에서 허용되지 않으면 무료 플랜으로 강제
                        if plan and model not in plan.allowed_models:
                            logger.warning(
                                f"모델 {model}이 플랜 {plan.display_name}에서 허용되지 않습니다. "
                                f"gpt-5-nano로 대체합니다."
                            )
                            model = 'gpt-5-nano'
                else:
                    # 익명 사용자는 기본 전략
                    provider_name = preferred_provider or strategy['provider']
                    model = strategy['model']
                    temperature = strategy['temperature']
        else:
            # FINAL_GENERATION 외 작업은 기본 전략
            provider_name = preferred_provider or strategy['provider']
            model = strategy['model']
            temperature = strategy['temperature']

            # 무료 플랜 강제 적용 (무료 플랜은 모든 작업에서 gpt-5-nano)
            if user:
                subscription, plan = get_user_subscription(user)
                if plan and plan.plan_type == 'free':
                    model = 'gpt-5-nano'
                    provider_name = 'openai'
        
        # 제공자 가져오기
        provider = self._providers.get(provider_name)
        
        if not provider:
            # 폴백: 사용 가능한 다른 제공자 선택
            logger.warning(f"선호 제공자 '{provider_name}'를 사용할 수 없습니다. 폴백 시도...")
            provider = self._get_fallback_provider()
            if not provider:
                raise LLMProviderError("사용 가능한 LLM 제공자가 없습니다.")
            
            # 폴백 제공자에 맞는 모델 선택
            provider_name = [k for k, v in self._providers.items() if v == provider][0]
            model = self._get_fallback_model(provider_name, task_type, quality)
        
        logger.debug(f"선택된 제공자: {provider_name}, 모델: {model}, 온도: {temperature}")
        return provider, model, temperature
    
    def _get_strategy_for_model(self, model_name: str, quality: QualityLevel) -> Optional[Dict]:
        """특정 모델에 대한 전략 가져오기"""
        # 모델 이름에 따른 기본 전략
        model_strategies = {
            'gpt-5-nano': {'provider': 'openai', 'temperature': 0.7},
            'gpt-5-mini': {'provider': 'openai', 'temperature': 0.7},
            'gpt-5': {'provider': 'openai', 'temperature': 0.8},
            'gpt-4.1': {'provider': 'openai', 'temperature': 0.8},
            'gpt-4.1-mini': {'provider': 'openai', 'temperature': 0.7},
        }
        return model_strategies.get(model_name)
    
    def _get_fallback_provider(self) -> Optional[BaseLLMProvider]:
        """폴백 제공자 선택 (우선순위: OpenAI > Anthropic > Google)"""
        for provider_name in ['openai', 'anthropic', 'google']:
            provider = self._providers.get(provider_name)
            if provider:
                logger.info(f"폴백 제공자로 {provider_name} 선택")
                return provider
        return None
    
    def _get_fallback_model(
        self,
        provider_name: str,
        task_type: TaskType,
        quality: QualityLevel
    ) -> str:
        """폴백 제공자에 맞는 모델 선택"""
        provider = self._providers.get(provider_name)
        if not provider:
            return 'gpt-4o-mini'  # 기본값
        
        available_models = provider.get_available_models()
        
        # 작업 유형에 따른 모델 선택
        if task_type in [TaskType.INTENT_PARSING, TaskType.CONTEXT_QUESTIONS, TaskType.PROMPT_SYNTHESIS]:
            # 초경량 모델 선호
            for model in ['gpt-5-nano', 'gpt-4.1-nano', 'gpt-4o-mini', 'claude-3-5-haiku-20241022', 'gemini-1.5-flash']:
                if model in available_models:
                    return model
        elif task_type == TaskType.FINAL_GENERATION:
            # 품질에 따라
            if quality == QualityLevel.HIGH:
                for model in ['gpt-4o', 'claude-3-5-sonnet-20241022', 'gemini-1.5-pro']:
                    if model in available_models:
                        return model
            elif quality == QualityLevel.BALANCED:
                for model in ['gpt-5-mini', 'gpt-4o-mini', 'claude-3-5-haiku-20241022', 'gemini-1.5-flash']:
                    if model in available_models:
                        return model
            elif quality == QualityLevel.LOW:
                for model in ['gpt-5-nano', 'gpt-4.1-nano', 'gpt-4o-mini', 'claude-3-5-haiku-20241022']:
                    if model in available_models:
                        return model
        
        # 기본: 사용 가능한 첫 번째 모델
        return available_models[0] if available_models else 'gpt-4o-mini'
    
    def calculate_complexity(
        self,
        prompt: str,
        context_length: int = 0,
        requires_reasoning: bool = False,
        requires_creativity: bool = False,
        requires_precision: bool = True
    ) -> QualityLevel:
        """
        작업 복잡도 계산
        
        Args:
            prompt: 프롬프트 텍스트
            context_length: 컨텍스트 길이
            requires_reasoning: 추론 필요 여부
            requires_creativity: 창의성 필요 여부
            requires_precision: 정확도 필요 여부
        
        Returns:
            추천 품질 수준
        """
        complexity_score = 0
        
        # 길이 기반
        prompt_tokens = len(prompt) // 4  # 근사치
        if prompt_tokens > 2000:
            complexity_score += 3
        elif prompt_tokens > 1000:
            complexity_score += 2
        elif prompt_tokens > 500:
            complexity_score += 1
        
        # 컨텍스트 길이
        if context_length > 10000:
            complexity_score += 2
        elif context_length > 5000:
            complexity_score += 1
        
        # 작업 특성
        if requires_reasoning:
            complexity_score += 2
        if requires_creativity:
            complexity_score += 1
        if requires_precision:
            complexity_score += 1
        
        # 점수에 따른 품질 수준 결정
        if complexity_score >= 6:
            return QualityLevel.HIGH
        elif complexity_score >= 3:
            return QualityLevel.BALANCED
        else:
            return QualityLevel.LOW
    
    def get_available_providers(self) -> Dict[str, bool]:
        """사용 가능한 제공자 목록"""
        return {name: (provider is not None) for name, provider in self._providers.items()}
    
    def search_internet(
        self,
        query: str,
        max_tokens: Optional[int] = 1000
    ) -> Dict[str, Any]:
        """
        인터넷 검색 수행 (Perplexity Sonar 사용)
        
        Args:
            query: 검색 쿼리
            max_tokens: 최대 토큰 수
        
        Returns:
            검색 결과 딕셔너리
        
        Raises:
            LLMProviderError: Perplexity Provider를 사용할 수 없을 때
        """
        perplexity = self._providers.get('perplexity')
        
        if not perplexity:
            raise LLMProviderError(
                "Perplexity Provider를 사용할 수 없습니다. "
                "PERPLEXITY_API_KEY를 설정했는지 확인하세요."
            )
        
        logger.info(f"Perplexity Sonar로 인터넷 검색: {query[:50]}...")
        
        return perplexity.search_internet(query=query, max_tokens=max_tokens)
    
    def enhance_prompt_with_internet(
        self,
        prompt: str,
        user_query: str,
        max_search_tokens: int = 800
    ) -> str:
        """
        인터넷 검색 결과로 프롬프트 강화
        
        Args:
            prompt: 원본 프롬프트
            user_query: 사용자 질문 (검색에 사용)
            max_search_tokens: 검색 결과 최대 토큰 수
        
        Returns:
            인터넷 검색 결과가 포함된 강화된 프롬프트
        """
        try:
            # 인터넷 검색 수행
            search_result = self.search_internet(
                query=user_query,
                max_tokens=max_search_tokens
            )
            
            # 검색 결과를 프롬프트에 통합
            enhanced_prompt = f"""[인터넷 검색 정보]
다음은 최신 웹 검색 결과입니다:

{search_result['content']}

[원본 요청]
{prompt}

위 검색 정보를 참고하여 답변해주세요. 검색 결과에 나온 최신 정보를 활용하되, 
부정확한 정보는 걸러내고 신뢰할 수 있는 내용만 사용하세요.
"""
            
            logger.info(f"프롬프트 강화 완료: 검색 토큰 {search_result['tokens_used']}")
            
            return enhanced_prompt
        
        except LLMProviderError as e:
            # 검색 실패 시 원본 프롬프트 반환
            logger.warning(f"인터넷 검색 실패, 원본 프롬프트 사용: {e}")
            return prompt


# 전역 Router 인스턴스
_router_instance: Optional[ModelRouter] = None


def get_router() -> ModelRouter:
    """전역 Router 인스턴스 가져오기 (싱글톤)"""
    global _router_instance
    if _router_instance is None:
        _router_instance = ModelRouter()
    return _router_instance

