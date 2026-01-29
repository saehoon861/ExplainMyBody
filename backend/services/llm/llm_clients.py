"""
LLM 클라이언트 팩토리
- OpenAI, Anthropic, Ollama 등 다양한 LLM 클라이언트를 생성
"""

import os
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple

from openai import OpenAI
from anthropic import Anthropic
import httpx


class BaseLLMClient(ABC):
    """LLM 클라이언트 추상 베이스 클래스"""

    @abstractmethod
    def generate_chat(self, system_prompt: str, user_prompt: str) -> str:
        """채팅 생성"""
        pass

    @abstractmethod
    def create_embedding(self, text: str) -> List[float]:
        """임베딩 생성"""
        pass


class OpenAIClient(BaseLLMClient):
    """OpenAI API 클라이언트"""

    def __init__(self, model: str = "gpt-4o-mini"):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model

    def generate_chat(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content

    def generate_chat_with_history(self, system_prompt: str, messages: List[Tuple[str, str]]) -> str:
        """대화 기록을 포함하여 채팅 생성"""
        formatted_messages = [{"role": "system", "content": system_prompt}]
        for role, content in messages:
            formatted_messages.append({"role": role, "content": content})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=formatted_messages,
        )
        return response.choices[0].message.content

    def create_embedding(self, text: str, model="text-embedding-3-small") -> List[float]:
        response = self.client.embeddings.create(input=[text], model=model)
        return response.data[0].embedding


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude API 클라이언트"""

    def __init__(self, model: str = "claude-3-5-sonnet-20240620"):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = model

    def generate_chat(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text

    def create_embedding(self, text: str) -> List[float]:
        raise NotImplementedError("Anthropic 클라이언트는 임베딩을 지원하지 않습니다.")


class OllamaClient(BaseLLMClient):
    """Ollama 클라이언트"""

    def __init__(self, model: str, embedding_model: str, base_url: str = "http://localhost:11434"):
        self.model = model
        self.embedding_model = embedding_model
        self.base_url = base_url
        self.client = httpx.Client(base_url=self.base_url)

    def generate_chat(self, system_prompt: str, user_prompt: str) -> str:
        # Ollama는 system 프롬프트를 messages 리스트 안에 넣는 것을 선호합니다.
        response = self.client.post("/api/chat", json={
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False
        })
        response.raise_for_status()
        return response.json()["message"]["content"]

    def create_embedding(self, text: str) -> List[float]:
        response = self.client.post("/api/embeddings", json={"model": self.embedding_model, "prompt": text})
        response.raise_for_status()
        return response.json()["embedding"]


def create_llm_client(model_name: str) -> BaseLLMClient:
    if model_name.startswith("gpt"):
        return OpenAIClient(model=model_name)
    elif model_name.startswith("claude"):
        return AnthropicClient(model=model_name)
    else:
        # 기본적으로 Ollama 클라이언트를 사용하거나, 특정 모델명으로 분기할 수 있습니다.
        return OllamaClient(model=model_name, embedding_model="bge-m3:latest")