# -*- coding: utf-8 -*-
"""
Anthropic LLM Provider

Anthropic API (Claude 3.5 Sonnet, Claude 3 Haiku 등)를 위한 Provider 구현
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


class AnthropicProvider(BaseLLMProvider):
    """Anthropic API Provider"""
    
    AVAILABLE_MODELS = [
        'claude-3-5-sonnet-20241022',
        'claude-3-5-haiku-20241022',
        'claude-3-opus-20240229',
        'claude-3-sonnet-20240229',
        'claude-3-haiku-20240307',
    ]
    
    def __init__(self, api_key: str, default_model: str = 'claude-3-5-haiku-20241022'):
        super().__init__(api_key, default_model)
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Anthropic 클라이언트 초기화"""
        if not self.api_key:
            logger.warning("Anthropic API key가 없어 클라이언트를 초기화할 수 없습니다.")
            return
        
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
            logger.info("Anthropic 클라이언트 초기화 완료")
        except ImportError:
            logger.error("anthropic 패키지가 설치되지 않았습니다. pip install anthropic 실행 필요")
            raise LLMProviderError("anthropic 패키지가 필요합니다.")
        except Exception as e:
            logger.error(f"Anthropic 클라이언트 초기화 실패: {e}")
            raise LLMProviderError(f"Anthropic 초기화 실패: {e}")
    
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
            raise LLMProviderError("Anthropic 클라이언트가 초기화되지 않았습니다.")
        
        model = model or self.default_model
        
        if model not in self.AVAILABLE_MODELS:
            raise ModelNotFoundError(f"모델 '{model}'을 사용할 수 없습니다. 사용 가능: {self.AVAILABLE_MODELS}")
        
        # Claude는 max_tokens가 필수
        if max_tokens is None:
            max_tokens = 4096
        
        try:
            message_params = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            if system_prompt:
                message_params["system"] = system_prompt
            
            response = self.client.messages.create(**message_params)
            
            content = response.content[0].text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            finish_reason = response.stop_reason
            
            logger.debug(f"Anthropic 생성 완료: {tokens_used} 토큰 사용")
            
            return LLMResponse(
                content=content,
                model=model,
                tokens_used=tokens_used,
                finish_reason=finish_reason,
                raw_response=response
            )
        
        except Exception as e:
            error_msg = str(e)
            if 'rate_limit' in error_msg.lower() or '429' in error_msg:
                raise RateLimitError(f"Rate limit 초과: {error_msg}")
            elif 'invalid' in error_msg.lower():
                raise InvalidResponseError(f"잘못된 응답: {error_msg}")
            else:
                raise LLMProviderError(f"Anthropic API 호출 실패: {error_msg}")
    
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
            raise LLMProviderError("Anthropic 클라이언트가 초기화되지 않았습니다.")
        
        model = model or self.default_model
        
        # JSON 모드 지시 추가
        json_instruction = "\n\n반드시 유효한 JSON 형식으로만 응답하세요. ```json 마커나 다른 텍스트 없이 순수 JSON만 반환하세요."
        full_prompt = prompt + json_instruction
        
        # 시스템 프롬프트에도 JSON 요청 추가
        if system_prompt:
            full_system_prompt = system_prompt + "\n\n당신은 항상 순수 JSON 형식으로만 응답합니다."
        else:
            full_system_prompt = "당신은 JSON 형식으로 응답하는 AI 어시스턴트입니다. 순수 JSON만 반환하고 다른 텍스트는 포함하지 마세요."
        
        max_tokens = kwargs.pop('max_tokens', 4096)
        
        try:
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=full_system_prompt,
                messages=[{"role": "user", "content": full_prompt}],
                **kwargs
            )
            
            content = response.content[0].text
            
            # JSON 파싱
            try:
                # ```json 마커 제거
                content = content.strip()
                if content.startswith('```json'):
                    content = content[7:]
                if content.startswith('```'):
                    content = content[3:]
                if content.endswith('```'):
                    content = content[:-3]
                content = content.strip()
                
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
            raise LLMProviderError(f"Anthropic JSON 생성 실패: {str(e)}")
    
    def count_tokens(self, text: str) -> int:
        """토큰 수 계산 (근사치)"""
        # Anthropic의 토큰 계산도 비슷한 방식
        # 더 정확한 계산을 위해서는 anthropic의 토큰 카운터 사용 필요
        korean_chars = len([c for c in text if '가' <= c <= '힣'])
        other_chars = len(text) - korean_chars
        estimated = (korean_chars * 2) + (other_chars // 4)
        return max(1, estimated)
    
    def get_available_models(self) -> List[str]:
        """사용 가능한 모델 목록"""
        return self.AVAILABLE_MODELS.copy()

