"""
Claude API Client for ExplainMyBody
"""

import os
from typing import Optional
from anthropic import Anthropic


class ClaudeClient:
    """Claude API 클라이언트"""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022", max_tokens: int = 16384):
        """
        Claude API 클라이언트 초기화

        Args:
            api_key: Anthropic API 키 (None이면 환경변수에서 로드)
            model: Claude 모델명
            max_tokens: 최대 토큰 수
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found. Set it in .env file or pass as argument.")

        self.client = Anthropic(api_key=self.api_key)
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
            message = self.client.messages.create(
                model=self.model,
                max_tokens=tokens,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text
        except Exception as e:
            raise ConnectionError(f"Claude API call failed: {e}")

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
            message = self.client.messages.create(
                model=self.model,
                max_tokens=tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            return message.content[0].text
        except Exception as e:
            raise ConnectionError(f"Claude API call failed: {e}")

    def check_connection(self) -> bool:
        """
        API 연결 테스트

        Returns:
            연결 성공 여부
        """
        try:
            # 간단한 테스트 요청
            self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            return True
        except:
            return False
