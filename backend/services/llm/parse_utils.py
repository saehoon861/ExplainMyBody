"""
LLM 응답 파싱 유틸리티
LLM1 출력 결과를 요약(summary)과 전문(content)으로 분리하는 기능 제공
"""

import re
from typing import Dict


def split_analysis_response(text: str) -> Dict[str, str]:
    """
    LLM 분석 응답을 요약(summary)과 전문(content)으로 분리
    
    우선순위:
    1. "### [종합 체형 평가]" 섹션
    2. "### [요약]" 또는 "### [분석 요약]" 섹션
    3. 첫 번째 "###" 섹션
    4. 위 모두 없으면 처음 500자를 summary로 사용
    
    Args:
        text: LLM 응답 전문
        
    Returns:
        {
            "summary": 요약 내용,
            "content": 전체 내용
        }
    """
    if not text or not text.strip():
        return {"summary": "", "content": ""}
    
    # 우선순위 1: "### [종합 체형 평가]" 섹션
    summary_patterns = [
        r"###\s*\[종합\s*체형\s*평가\]",
        r"###\s*\[요약\]",
        r"###\s*\[분석\s*요약\]",
    ]
    
    summary_content = None
    summary_start_idx = -1
    summary_end_idx = -1
    
    # 우선순위 순서대로 패턴 검색
    for pattern in summary_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            summary_start_idx = match.start()
            # 해당 섹션의 시작 위치부터 다음 "###" 섹션까지 또는 끝까지
            next_section = re.search(r"\n###\s*\[", text[match.end():])
            if next_section:
                summary_end_idx = match.end() + next_section.start()
            else:
                summary_end_idx = len(text)
            
            # 섹션 제목을 제외한 내용만 추출
            summary_content = text[match.end():summary_end_idx].strip()
            break
    
    # 우선순위 패턴에서 찾지 못한 경우, 첫 번째 "###" 섹션 사용
    if summary_content is None:
        first_section = re.search(r"###\s*\[([^\]]+)\]", text)
        if first_section:
            summary_start_idx = first_section.start()
            next_section = re.search(r"\n###\s*\[", text[first_section.end():])
            if next_section:
                summary_end_idx = first_section.end() + next_section.start()
            else:
                summary_end_idx = len(text)
            
            summary_content = text[first_section.end():summary_end_idx].strip()
    
    # 어떤 섹션도 찾지 못한 경우, 처음 500자를 summary로 사용
    if summary_content is None:
        summary_content = text[:500].strip()
        if len(text) > 500:
            summary_content += "..."
    
    # content는 항상 전체 텍스트
    return {
        "summary": summary_content,
        "content": text
    }
