# -*- coding: utf-8 -*-
"""
Google LLM Provider

Google Generative AI (Gemini) API를 위한 Provider 구현
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


class GoogleProvider(BaseLLMProvider):
    """Google Generative AI (Gemini) Provider"""
    
    AVAILABLE_MODELS = [
        'gemini-1.5-pro',
        'gemini-1.5-flash',
        'gemini-1.0-pro',
    ]
    
    def __init__(self, api_key: str, default_model: str = 'gemini-1.5-flash'):
        super().__init__(api_key, default_model)
        self.genai = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Google Generative AI 클라이언트 초기화"""
        if not self.api_key:
            logger.warning("Google API key가 없어 클라이언트를 초기화할 수 없습니다.")
            return
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.genai = genai
            logger.info("Google Generative AI 클라이언트 초기화 완료")
        except ImportError:
            logger.error("google-generativeai 패키지가 설치되지 않았습니다. pip install google-generativeai 실행 필요")
            raise LLMProviderError("google-generativeai 패키지가 필요합니다.")
        except Exception as e:
            logger.error(f"Google 클라이언트 초기화 실패: {e}")
            raise LLMProviderError(f"Google 초기화 실패: {e}")
    
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
        if not self.genai:
            raise LLMProviderError("Google 클라이언트가 초기화되지 않았습니다.")
        
        model_name = model or self.default_model
        
        if model_name not in self.AVAILABLE_MODELS:
            raise ModelNotFoundError(f"모델 '{model_name}'을 사용할 수 없습니다. 사용 가능: {self.AVAILABLE_MODELS}")
        
        try:
            # 모델 생성
            generation_config = {
                "temperature": temperature,
            }
            if max_tokens:
                generation_config["max_output_tokens"] = max_tokens
            
            model_instance = self.genai.GenerativeModel(
                model_name=model_name,
                generation_config=generation_config
            )
            
            # 시스템 프롬프트 처리 (Gemini는 system instruction 지원)
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            response = model_instance.generate_content(full_prompt)
            
            content = response.text
            # Gemini API는 토큰 사용량을 제공하지 않을 수 있음
            tokens_used = self.count_tokens(prompt) + self.count_tokens(content)
            finish_reason = getattr(response.candidates[0], 'finish_reason', None) if response.candidates else None
            
            logger.debug(f"Google 생성 완료: 약 {tokens_used} 토큰 사용")
            
            return LLMResponse(
                content=content,
                model=model_name,
                tokens_used=tokens_used,
                finish_reason=str(finish_reason) if finish_reason else None,
                raw_response=response
            )
        
        except Exception as e:
            error_msg = str(e)
            if 'quota' in error_msg.lower() or 'rate' in error_msg.lower():
                raise RateLimitError(f"Rate limit/Quota 초과: {error_msg}")
            elif 'invalid' in error_msg.lower():
                raise InvalidResponseError(f"잘못된 응답: {error_msg}")
            else:
                raise LLMProviderError(f"Google API 호출 실패: {error_msg}")
    
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
        if not self.genai:
            raise LLMProviderError("Google 클라이언트가 초기화되지 않았습니다.")
        
        model_name = model or self.default_model
        
        # JSON 모드 지시 추가
        json_instruction = "\n\n반드시 유효한 JSON 형식으로만 응답하세요. 마크다운이나 다른 텍스트 없이 순수 JSON만 반환하세요."
        full_prompt = prompt + json_instruction
        
        # 시스템 프롬프트에도 JSON 요청 추가
        if system_prompt:
            full_system_prompt = system_prompt + "\n\n당신은 항상 순수 JSON 형식으로만 응답합니다."
        else:
            full_system_prompt = "당신은 JSON 형식으로 응답하는 AI 어시스턴트입니다."
        
        try:
            generation_config = {
                "temperature": temperature,
                "response_mime_type": "application/json",  # Gemini 1.5는 JSON 모드 지원
            }
            
            model_instance = self.genai.GenerativeModel(
                model_name=model_name,
                generation_config=generation_config
            )
            
            full_input = f"{full_system_prompt}\n\n{full_prompt}"
            response = model_instance.generate_content(full_input)
            
            content = response.text
            
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
            raise LLMProviderError(f"Google JSON 생성 실패: {str(e)}")
    
    def count_tokens(self, text: str) -> int:
        """토큰 수 계산 (근사치)"""
        # Gemini도 비슷한 방식으로 근사
        if self.genai:
            try:
                model = self.genai.GenerativeModel(self.default_model)
                result = model.count_tokens(text)
                return result.total_tokens
            except:
                pass
        
        # 폴백: 간단 추정
        korean_chars = len([c for c in text if '가' <= c <= '힣'])
        other_chars = len(text) - korean_chars
        estimated = (korean_chars * 2) + (other_chars // 4)
        return max(1, estimated)
    
    def get_available_models(self) -> List[str]:
        """사용 가능한 모델 목록"""
        return self.AVAILABLE_MODELS.copy()

