# -*- coding: utf-8 -*-
"""
LLM Provider 추상 기본 클래스

모든 LLM 제공자가 구현해야 하는 공통 인터페이스를 정의합니다.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class LLMResponse:
    """LLM 응답을 표준화하는 데이터 클래스"""
    
    def __init__(
        self,
        content: str,
        model: str,
        tokens_used: int = 0,
        finish_reason: Optional[str] = None,
        raw_response: Optional[Any] = None
    ):
        self.content = content
        self.model = model
        self.tokens_used = tokens_used
        self.finish_reason = finish_reason
        self.raw_response = raw_response
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'content': self.content,
            'model': self.model,
            'tokens_used': self.tokens_used,
            'finish_reason': self.finish_reason,
        }


class BaseLLMProvider(ABC):
    """
    모든 LLM 제공자의 추상 기본 클래스
    
    각 제공자는 이 클래스를 상속받아 generate(), generate_json() 등의 
    메서드를 구현해야 합니다.
    """
    
    def __init__(self, api_key: str, default_model: Optional[str] = None):
        """
        Args:
            api_key: API 키
            default_model: 기본 사용 모델
        """
        self.api_key = api_key
        self.default_model = default_model
        self._validate_api_key()
    
    def _validate_api_key(self):
        """API 키 유효성 검사"""
        if not self.api_key:
            logger.warning(f"{self.__class__.__name__}: API key가 설정되지 않았습니다.")
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        텍스트 생성
        
        Args:
            prompt: 사용자 프롬프트
            model: 사용할 모델 (None이면 default_model 사용)
            temperature: 생성 다양성 (0.0-2.0)
            max_tokens: 최대 토큰 수
            system_prompt: 시스템 프롬프트
            **kwargs: 제공자별 추가 파라미터
        
        Returns:
            LLMResponse 객체
        """
        pass
    
    @abstractmethod
    def generate_json(
        self,
        prompt: str,
        schema: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        temperature: float = 0.3,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        JSON 형식으로 구조화된 출력 생성
        
        Args:
            prompt: 사용자 프롬프트
            schema: JSON Schema (선택적)
            model: 사용할 모델
            temperature: 생성 다양성 (JSON은 낮은 값 권장)
            system_prompt: 시스템 프롬프트
            **kwargs: 제공자별 추가 파라미터
        
        Returns:
            파싱된 JSON 딕셔너리
        """
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        텍스트의 토큰 수 계산 (근사치)
        
        Args:
            text: 계산할 텍스트
        
        Returns:
            토큰 수
        """
        pass
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        현재 설정된 모델 정보 반환
        
        Returns:
            모델 정보 딕셔너리
        """
        return {
            'provider': self.__class__.__name__,
            'default_model': self.default_model,
            'has_api_key': bool(self.api_key),
        }
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        사용 가능한 모델 목록 반환
        
        Returns:
            모델 이름 리스트
        """
        pass


class LLMProviderError(Exception):
    """LLM Provider 관련 에러"""
    pass


class RateLimitError(LLMProviderError):
    """Rate Limit 에러"""
    pass


class InvalidResponseError(LLMProviderError):
    """잘못된 응답 에러"""
    pass


class ModelNotFoundError(LLMProviderError):
    """모델을 찾을 수 없음"""
    pass

