"""
LLM Client 통합 모듈
Claude, OpenAI, Ollama 클라이언트를 제공
"""

import os
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

load_dotenv()


class BaseLLMClient:
    """Base LLM Client Interface"""

    def generate_chat(self, system_prompt: str, user_prompt: str) -> str:
        raise NotImplementedError

    def generate_with_messages(self, messages: List[Dict[str, str]]) -> str:
        raise NotImplementedError

    def check_connection(self) -> bool:
        raise NotImplementedError


class ClaudeClient(BaseLLMClient):
    """Claude API Client"""

    def __init__(self, model: str = "claude-haiku-4-5-20251001"):
        import anthropic
        self.model = model
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def generate_chat(self, system_prompt: str, user_prompt: str) -> str:
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=8192,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )
            return message.content[0].text
        except Exception as e:
            raise RuntimeError(f"Claude API error: {e}")

    def generate_with_messages(self, messages: List[Dict[str, str]]) -> str:
        try:
            # Extract system message if present
            system_msg = None
            chat_messages = []

            for msg in messages:
                if msg["role"] == "system":
                    system_msg = msg["content"]
                else:
                    chat_messages.append(msg)

            response = self.client.messages.create(
                model=self.model,
                max_tokens=8192,
                system=system_msg if system_msg else "",
                messages=chat_messages
            )
            return response.content[0].text
        except Exception as e:
            raise RuntimeError(f"Claude API error: {e}")

    def check_connection(self) -> bool:
        try:
            self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )
            return True
        except:
            return False


class OpenAIClient(BaseLLMClient):
    """OpenAI API Client"""

    def __init__(self, model: str = "gpt-4.1"):
        from openai import OpenAI
        self.model = model
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def generate_chat(self, system_prompt: str, user_prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=4096,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {e}")

    def generate_with_messages(self, messages: List[Dict[str, str]]) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=4096,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {e}")

    def check_connection(self) -> bool:
        try:
            self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=10
            )
            return True
        except:
            return False

    def create_embedding(self, text: str, model: str = "text-embedding-3-small") -> List[float]:
        """텍스트를 임베딩 벡터로 변환"""
        try:
            response = self.client.embeddings.create(
                model=model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            raise RuntimeError(f"OpenAI Embedding error: {e}")


class OllamaClient(BaseLLMClient):
    """Ollama Local LLM Client"""

    def __init__(
        self, 
        model: str = "exaone3.5:7.8b", 
        base_url: str = "http://localhost:11434",
        embedding_model: Optional[str] = None
    ):
        self.model = model
        self.base_url = base_url
        # embedding_model이 지정되지 않으면 bge-m3:latest 사용
        self.embedding_model = embedding_model or "bge-m3:latest"

    def generate_chat(self, system_prompt: str, user_prompt: str) -> str:
        import requests
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "stream": False
                }
            )
            response.raise_for_status()
            return response.json()["message"]["content"]
        except Exception as e:
            raise RuntimeError(f"Ollama API error: {e}")

    def generate_with_messages(self, messages: List[Dict[str, str]]) -> str:
        import requests
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False
                }
            )
            response.raise_for_status()
            return response.json()["message"]["content"]
        except Exception as e:
            raise RuntimeError(f"Ollama API error: {e}")

    def check_connection(self) -> bool:
        import requests
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except:
            return False

    def create_embedding(self, text: str, model: Optional[str] = None) -> List[float]:
        """
        텍스트를 임베딩 벡터로 변환
        
        Args:
            text: 임베딩할 텍스트
            model: 사용할 embedding 모델 (None이면 초기화 시 지정한 embedding_model 사용)
        
        Returns:
            임베딩 벡터 리스트
        """
        import requests
        try:
            embedding_model = model or self.embedding_model
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": embedding_model,
                    "prompt": text
                }
            )
            response.raise_for_status()
            return response.json()["embedding"]
        except Exception as e:
            raise RuntimeError(f"Ollama Embedding error: {e}")


def create_llm_client(model: str) -> BaseLLMClient:
    """
    모델 이름에 따라 적절한 LLM Client 생성

    Args:
        model: 모델 이름 (예: "claude-haiku-4-5-20251001", "gpt-4o-mini", "exaone3.5:7.8b")

    Returns:
        BaseLLMClient 인스턴스
    """
    if model.startswith("claude-"):
        return ClaudeClient(model=model)
    elif model.startswith("gpt-"):
        return OpenAIClient(model=model)
    else:
        return OllamaClient(model=model)
