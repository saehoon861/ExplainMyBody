"""
Ollama LLM Client for ExplainMyBody
"""

import requests
import json
import re
from typing import Optional


class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.1:8b", max_tokens: int = 8192):
        self.base_url = base_url
        self.model = model
        self.max_tokens = max_tokens

    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = None) -> str:
        url = f"{self.base_url}/api/generate"
        tokens = max_tokens if max_tokens else self.max_tokens
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": tokens
            }
        }
        try:
            response = requests.post(url, json=payload, timeout=180)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Ollama connection failed: {e}")

    def generate_chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, max_tokens: int = None) -> str:
        """
        Ollama chat API를 사용하여 system/user 메시지 구분

        Args:
            system_prompt: 시스템 프롬프트 (역할 정의, 가이드라인)
            user_prompt: 사용자 프롬프트 (실제 입력 데이터)
            temperature: 온도
            max_tokens: 최대 토큰 수

        Returns:
            LLM 응답 문자열
        """
        url = f"{self.base_url}/api/chat"
        tokens = max_tokens if max_tokens else self.max_tokens
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": tokens
            }
        }
        try:
            response = requests.post(url, json=payload, timeout=180)
            response.raise_for_status()
            result = response.json()
            return result.get("message", {}).get("content", "")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Ollama chat connection failed: {e}")

    def _fix_json(self, json_str: str) -> str:
        """Fix common JSON errors from LLM output"""
        # Fix number ranges: 8-12 -> "8-12"
        json_str = re.sub(r'": (\d+)-(\d+)([,}\]])', r'": "\1-\2"\3', json_str)
        # Fix time formats: 30초 -> "30초"
        json_str = re.sub(r'": (\d+초)([,}\]])', r'": "\1"\2', json_str)
        json_str = re.sub(r'": (\d+분)([,}\]])', r'": "\1"\2', json_str)
        # Fix ranges like 30초-1분
        json_str = re.sub(r'": (\d+[초분]?-\d+[초분]?)([,}\]])', r'": "\1"\2', json_str)
        return json_str

    def generate_json(self, prompt: str, temperature: float = 0.3, debug: bool = False) -> Optional[dict]:
        raw_response = self.generate(prompt, temperature=temperature)

        if debug:
            print(f"[Debug] Raw LLM response (first 500 chars):\n{raw_response[:500]}")

        try:
            json_start = raw_response.find("{")
            json_end = raw_response.rfind("}") + 1

            if json_start != -1 and json_end > json_start:
                json_str = raw_response[json_start:json_end]
                json_str = self._fix_json(json_str)
                return json.loads(json_str)
            else:
                print("[Warning] No JSON block found")
                print(f"[Debug] Full response:\n{raw_response[:1000]}...")
                return None
        except json.JSONDecodeError as e:
            print(f"[Warning] JSON parse error: {e}")
            print(f"[Debug] Attempted JSON:\n{json_str[:500]}...")
            return None

    def check_connection(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

    def list_models(self) -> list:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except:
            return []


class LLMJsonParser:
    """
    Pipeline 외부에서 LLM raw 문자열을 JSON으로 변환할 때 사용.
    OllamaClient.generate_json 과 동일한 로직을 재사용하지만,
    이미 확보한 raw 응답을 후처리만 하고 싶을 때 활용한다.
    """

    @staticmethod
    def _fix_json(json_str: str) -> str:
        """Fix common JSON errors from LLM output"""
        json_str = re.sub(r'": (\d+)-(\d+)([,}\]])', r'": "\1-\2"\3', json_str)
        json_str = re.sub(r'": (\d+초)([,}\]])', r'": "\1"\2', json_str)
        json_str = re.sub(r'": (\d+분)([,}\]])', r'": "\1"\2', json_str)
        json_str = re.sub(r'": (\d+[초분]?-\d+[초분]?)([,}\]])', r'": "\1"\2', json_str)
        return json_str

    @classmethod
    def parse(cls, raw_response: str, debug: bool = False) -> Optional[dict]:
        try:
            json_start = raw_response.find("{")
            json_end = raw_response.rfind("}") + 1

            if json_start != -1 and json_end > json_start:
                json_str = raw_response[json_start:json_end]
                json_str = cls._fix_json(json_str)
                return json.loads(json_str)
            else:
                if debug:
                    print("[Warning] No JSON block found")
                    print(f"[Debug] Full response:\n{raw_response[:1000]}...")
                return None
        except json.JSONDecodeError as e:
            if debug:
                print(f"[Warning] JSON parse error: {e}")
                print(f"[Debug] Attempted JSON:\n{json_str[:500]}...")
            return None
