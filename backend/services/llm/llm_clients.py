import os
from typing import List, Tuple, AsyncGenerator
from abc import ABC, abstractmethod
from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

class BaseLLMClient(ABC):
    @abstractmethod
    def generate_chat(self, system_prompt: str, user_prompt: str) -> str:
        """단일 턴 채팅 생성"""
        pass

    @abstractmethod
    def generate_chat_with_history(self, system_prompt: str, messages: List[Tuple[str, str]]) -> str:
        """대화 기록을 포함하여 채팅 생성"""
        pass

    @abstractmethod
    async def agenerate_chat(self, system_prompt: str, user_prompt: str, key: str) -> dict:
        """비동기 채팅 생성 (병렬 처리용)"""
        pass

    @abstractmethod
    def create_embedding(self, text: str) -> List[float]:
        """임베딩 생성"""
        pass

    @abstractmethod
    async def generate_chat_with_history_stream(self, system_prompt: str, messages: List[Tuple[str, str]]) -> AsyncGenerator[str, None]:
        """대화 기록을 포함하여 스트리밍 채팅 생성"""
        pass


class OpenAIClient(BaseLLMClient):
    """OpenAI API 클라이언트"""

    def __init__(self, model: str = "gpt-4o-mini"):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.async_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model

    def generate_chat(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content

    def generate_chat_with_history(self, system_prompt: str, messages: List[Tuple[str, str]]) -> str:
        # LangGraph 메시지 튜플 (role, content)을 OpenAI 포맷으로 변환
        formatted_messages = [{"role": "system", "content": system_prompt}]

        for role, content in messages:
            # role 매핑: human/user -> user, ai/assistant -> assistant
            openai_role = "user" if role in ["human", "user"] else "assistant"
            formatted_messages.append({"role": openai_role, "content": content})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=formatted_messages,
            temperature=0.7,
        )
        return response.choices[0].message.content

    async def agenerate_chat(self, system_prompt: str, user_prompt: str, key: str) -> dict:
        """비동기 채팅 생성 (병렬 처리용)"""
        response = await self.async_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
        )
        return {
            "key": key,
            "content": response.choices[0].message.content
        }

    def create_embedding(self, text: str) -> List[float]:
        # text-embedding-3-small 모델 사용 (1536차원)
        response = self.client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding

    async def generate_chat_with_history_stream(self, system_prompt: str, messages: List[Tuple[str, str]]) -> AsyncGenerator[str, None]:
        formatted_messages = [{"role": "system", "content": system_prompt}]
        
        for role, content in messages:
            openai_role = "user" if role in ["human", "user"] else "assistant"
            formatted_messages.append({"role": openai_role, "content": content})

        stream = await self.async_client.chat.completions.create(
            model=self.model,
            messages=formatted_messages,
            temperature=0.7,
            stream=True
        )

        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content


def create_llm_client(model_name: str = "gpt-4o-mini") -> BaseLLMClient:
    """LLM 클라이언트 팩토리 함수"""
    if "gpt" in model_name:
        return OpenAIClient(model=model_name)
    else:
        raise ValueError(f"지원하지 않는 모델입니다: {model_name}")