"""
OpenAI API Client for ExplainMyBody
"""

import os
from typing import Optional
from openai import OpenAI


class OpenAIClient:
    """OpenAI API 클라이언트"""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4.1", max_tokens: int = 16384):
        """
        OpenAI API 클라이언트 초기화

        Args:
            api_key: OpenAI API 키 (None이면 환경변수에서 로드)
            model: OpenAI 모델명
            max_tokens: 최대 토큰 수
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found. Set it in .env file or pass as argument.")

        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        self.max_tokens = max_tokens

    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: Optional[int] = None) -> str:
        """
        단일 프롬프트로 텍스트 생성

        Args:
            prompt: 프롬프트
            temperature: 온도
            max_tokens: 최대 토큰 (None이면 기본값 사용)

        Returns:
            생성된 텍스트
        """
        tokens = max_tokens if max_tokens else self.max_tokens

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=tokens,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            raise ConnectionError(f"OpenAI API call failed: {e}")

    def generate_chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, max_tokens: Optional[int] = None) -> str:
        """
        System/User 프롬프트로 텍스트 생성

        Args:
            system_prompt: 시스템 프롬프트
            user_prompt: 사용자 프롬프트
            temperature: 온도
            max_tokens: 최대 토큰

        Returns:
            생성된 텍스트
        """
        tokens = max_tokens if max_tokens else self.max_tokens

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=tokens,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            raise ConnectionError(f"OpenAI API call failed: {e}")

    def check_connection(self) -> bool:
        """
        API 연결 테스트

        Returns:
            연결 성공 여부
        """
        try:
            # 간단한 테스트 요청
            self.client.chat.completions.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            return True
        except:
            return False
