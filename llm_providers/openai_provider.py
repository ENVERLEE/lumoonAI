# -*- coding: utf-8 -*-
"""
OpenAI LLM Provider

OpenAI API (GPT-4o, GPT-4o-mini, GPT-3.5-turbo 등)를 위한 Provider 구현
"""

import json
import logging
from typing import Dict, Any, Optional, List

from .base import (
    BaseLLMProvider,
    LLMResponse,
    LLMProviderError,
    RateLimitError,
    InvalidResponseError,
    ModelNotFoundError
)

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API Provider"""
    
    AVAILABLE_MODELS = [
        'gpt-5-mini',
        'gpt-5-nano',
        'gpt-4o',
        'gpt-4o-mini',
        'gpt-4-turbo',
        'gpt-4',
        'gpt-4.1-nano',
    ]
    
    def __init__(self, api_key: str, default_model: str = 'gpt-4o-mini'):
        super().__init__(api_key, default_model)
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """OpenAI 클라이언트 초기화"""
        if not self.api_key:
            logger.warning("OpenAI API key가 없어 클라이언트를 초기화할 수 없습니다.")
            return
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
            logger.info("OpenAI 클라이언트 초기화 완료")
        except ImportError:
            logger.error("openai 패키지가 설치되지 않았습니다. pip install openai 실행 필요")
            raise LLMProviderError("openai 패키지가 필요합니다.")
        except Exception as e:
            logger.error(f"OpenAI 클라이언트 초기화 실패: {e}")
            raise LLMProviderError(f"OpenAI 초기화 실패: {e}")
    
    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """텍스트 생성"""
        if not self.client:
            raise LLMProviderError("OpenAI 클라이언트가 초기화되지 않았습니다.")
        
        model = model or self.default_model
        
        if model not in self.AVAILABLE_MODELS:
            raise ModelNotFoundError(f"모델 '{model}'을 사용할 수 없습니다. 사용 가능: {self.AVAILABLE_MODELS}")
        
        # 메시지 구성
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # API 호출 파라미터 구성
        api_params = {
            "model": model,
            "messages": messages,
            **kwargs
        }
        
        # GPT-5 nano/mini 모델은 temperature를 지원하지 않음 (기본값 1만 사용)
        if model not in ['gpt-5-nano', 'gpt-5-mini']:
            api_params["temperature"] = temperature
        
        # max_tokens가 None이 아닐 때만 추가
        if max_tokens is not None:
            api_params["max_tokens"] = max_tokens
        
        try:
            response = self.client.chat.completions.create(**api_params)
            
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            finish_reason = response.choices[0].finish_reason
            
            logger.debug(f"OpenAI 생성 완료: {tokens_used} 토큰 사용")
            
            return LLMResponse(
                content=content,
                model=model,
                tokens_used=tokens_used,
                finish_reason=finish_reason,
                raw_response=response
            )
        
        except Exception as e:
            error_msg = str(e)
            if 'rate_limit' in error_msg.lower():
                raise RateLimitError(f"Rate limit 초과: {error_msg}")
            elif 'invalid' in error_msg.lower():
                raise InvalidResponseError(f"잘못된 응답: {error_msg}")
            else:
                raise LLMProviderError(f"OpenAI API 호출 실패: {error_msg}")
    
    def generate_json(
        self,
        prompt: str,
        schema: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        temperature: float = 0.3,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """JSON 형식 생성"""
        if not self.client:
            raise LLMProviderError("OpenAI 클라이언트가 초기화되지 않았습니다.")
        
        model = model or self.default_model
        
        # JSON 모드 지시 추가
        json_instruction = "\n\n반드시 유효한 JSON 형식으로만 응답하세요. 다른 텍스트는 포함하지 마세요."
        full_prompt = prompt + json_instruction
        
        # 시스템 프롬프트에도 JSON 요청 추가
        if system_prompt:
            full_system_prompt = system_prompt + "\n\n당신은 항상 JSON 형식으로 응답합니다."
        else:
            full_system_prompt = "당신은 JSON 형식으로 응답하는 AI 어시스턴트입니다."
        
        # 메시지 구성
        messages = [
            {"role": "system", "content": full_system_prompt},
            {"role": "user", "content": full_prompt}
        ]
        
        try:
            # JSON 모드 지원 (GPT-5, GPT-4o, GPT-4-turbo 등)
            api_params = {
                "model": model,
                "messages": messages,
                **kwargs
            }
            
            # GPT-5 nano/mini 모델은 temperature를 지원하지 않음
            if model not in ['gpt-5-nano', 'gpt-5-mini']:
                api_params["temperature"] = temperature
            
            # JSON 모드 지원 모델인 경우 response_format 추가
            if model in ['gpt-5-mini', 'gpt-5-nano', 'gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo']:
                api_params["response_format"] = {"type": "json_object"}
            
            response = self.client.chat.completions.create(**api_params)
            
            content = response.choices[0].message.content
            
            # JSON 파싱
            try:
                parsed_json = json.loads(content)
                logger.debug(f"JSON 파싱 성공: {len(content)} 문자")
                return parsed_json
            except json.JSONDecodeError as je:
                logger.error(f"JSON 파싱 실패: {je}")
                # 재시도: content에서 JSON 추출 시도
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    try:
                        return json.loads(json_match.group())
                    except:
                        pass
                raise InvalidResponseError(f"JSON 파싱 실패: {content[:200]}")
        
        except (RateLimitError, InvalidResponseError, ModelNotFoundError):
            raise
        except Exception as e:
            raise LLMProviderError(f"OpenAI JSON 생성 실패: {str(e)}")
    
    def count_tokens(self, text: str) -> int:
        """토큰 수 계산 (근사치)"""
        # 간단한 근사: 4 문자 ≈ 1 토큰 (영어 기준)
        # 한글은 더 많은 토큰 사용 (약 1.5배)
        # 정확한 계산은 tiktoken 라이브러리 필요
        try:
            import tiktoken
            encoding = tiktoken.encoding_for_model(self.default_model)
            return len(encoding.encode(text))
        except ImportError:
            # tiktoken 없으면 간단 추정
            # 한글/영문 혼합 고려
            korean_chars = len([c for c in text if '가' <= c <= '힣'])
            other_chars = len(text) - korean_chars
            # 한글 1글자 ≈ 2 토큰, 영문 4글자 ≈ 1 토큰
            estimated = (korean_chars * 2) + (other_chars // 4)
            return max(1, estimated)
    
    def get_available_models(self) -> List[str]:
        """사용 가능한 모델 목록"""
        return self.AVAILABLE_MODELS.copy()

