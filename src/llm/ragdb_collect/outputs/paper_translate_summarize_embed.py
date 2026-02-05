"""
논문 메타데이터(JSON)를 입력으로 받아
1) Ollama(exaone3.5:7.8b)로 한글 번역 + 인바디 관점 요약
2) 검색 친화적 구조화 텍스트 생성
3) OpenAI text-embedding-3-small로 임베딩

- 번역/요약 결과는 고정 텍스트로 저장 (embedding drift 방지)
- OpenAI API Key는 환경변수 OPENAI_API_KEY 사용
"""

import json
import os
import requests
from typing import Dict, Any
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

# =====================
# Config
# =====================
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "exaone3.5:7.8b"
EMBEDDING_MODEL = "text-embedding-3-small"

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# =====================
# Ollama 호출
# =====================
def ollama_generate(prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2
        }
    }
    res = requests.post(OLLAMA_URL, json=payload, timeout=300)
    res.raise_for_status()
    return res.json()["response"].strip()


# =====================
# 번역 + 요약 프롬프트
# =====================
def build_translate_prompt(paper: Dict[str, Any]) -> str:
    return f"""
다음은 영어 논문 정보이다.
이 논문을 **인바디 기반 체형 분석 및 운동/식단 추천 RAG**에 사용하기 위해 가공하라.

요구사항:
1. 전체 내용을 자연스러운 한국어로 번역
2. 인바디 지표(골격근량, 체지방률, 내장지방 등)와 연결되는 관점으로 재해석
3. 검색에 유리하도록 구조화된 텍스트로 출력
4. 과장 없이 논문 내용에 근거해서만 작성
5. 수치, 조건, 단위는 절대 생략하지 말 것

출력 포맷을 반드시 지켜라:

[BACKGROUND]
...

[KEY FINDINGS]
- ...

[IMPLICATIONS FOR INBODY ANALYSIS]
- ...

[RECOMMENDED TAGS]
...

[ORIGINAL KEY TERMS]
영어 핵심 용어 나열

=== 논문 정보 ===
제목: {paper['title']}
초록: {paper['abstract']}
키워드: {', '.join(paper.get('keywords', []))}
"""


# =====================
# 임베딩
# =====================
def embed_text(text: str):
    emb = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return emb.data[0].embedding


# =====================
# 파이프라인
# =====================
def process_paper(paper: Dict[str, Any]) -> dict:
    """번역 + 임베딩 실행, 파일 I/O 없이 record 반환"""
    prompt = build_translate_prompt(paper)
    translated = ollama_generate(prompt)
    embedding = embed_text(translated)

    base_name = (paper.get("pmid") or paper.get("doi") or "paper").replace("/", "_")

    return {
        "id": base_name,
        "text": translated,
        "embedding": [round(v, 5) for v in embedding],  # pgvector float4 정밀도 충분
        "metadata": {
            "pmid": paper.get("pmid"),
            "doi": paper.get("doi"),
            "year": paper.get("year"),
            "journal": paper.get("journal"),
            "domain": paper.get("domain"),
            "source": paper.get("source"),
            "language": "ko"
        }
    }


# =====================
# 실행 예시
# =====================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="논문 번역·요약·임베딩 파이프라인")
    parser.add_argument("-n", "--limit", type=int, default=None, help="처리할 논문 수 (기본값: 전체)")
    parser.add_argument("-s", "--skip", type=int, default=0, help="앞에서 건너뛸 논문 수")
    parser.add_argument("-o", "--output", type=str, default="outputs", help="출력 디렉토리")
    parser.add_argument("--fresh", action="store_true", help="기존 출력 파일 덮어쓰기 (기본: append)")
    args = parser.parse_args()

    with open("ragdb_final_corpus_20260129_195141.json", "r", encoding="utf-8") as f:
        paper_data = json.load(f)

    subset = paper_data[args.skip : args.skip + args.limit if args.limit else None]
    total = len(subset)
    print(f"처리 대상: {total}건 (전체 {len(paper_data)}건, skip={args.skip})")

    os.makedirs(args.output, exist_ok=True)
    jsonl_path = os.path.join(args.output, "corpus_embeddings.jsonl")
    txt_path = os.path.join(args.output, "corpus_translated.txt")

    mode = "w" if args.fresh else "a"
    with open(jsonl_path, mode, encoding="utf-8") as jf, \
         open(txt_path, mode, encoding="utf-8") as tf:
        for i, paper in enumerate(subset):
            try:
                result = process_paper(paper)
                jf.write(json.dumps(result, ensure_ascii=False) + "\n")
                jf.flush()
                tf.write(f"=== [{result['id']}] ===\n{result['text']}\n\n")
                tf.flush()
                print(f"[{i+1}/{total}] 완료: {result['id']}")
            except Exception as e:
                pmid = paper.get("pmid") or paper.get("doi") or "unknown"
                print(f"[{i+1}/{total}] 오류 (pmid={pmid}): {e}")
