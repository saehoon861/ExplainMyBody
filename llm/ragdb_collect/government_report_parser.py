"""
정부/공공기관 보고서 PDF 파서

보건복지부, 식약처, 질병관리청 등의 공식 보고서에서
초록/요약 섹션을 추출하여 RAG 코퍼스로 변환합니다.
"""

import json
from typing import List, Optional, Dict
from pathlib import Path
from datetime import datetime

try:
    import pdfplumber
except ImportError:
    print("❌ pdfplumber 라이브러리가 필요합니다: pip install pdfplumber")
    exit(1)

from models import PaperMetadata


class GovernmentReportParser:
    """정부 보고서 PDF 파서"""

    # 초록/요약 섹션을 나타내는 키워드들
    SUMMARY_KEYWORDS = [
        "요약", "초록", "Summary", "Abstract", "Executive Summary",
        "연구요약", "정책요약", "개요", "핵심내용"
    ]

    # 섹션 종료 키워드 (이후는 본문으로 간주)
    END_KEYWORDS = [
        "목차", "차례", "서론", "배경", "1.", "I.", "제1장", "제1절"
    ]

    def __init__(self):
        pass

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """PDF에서 전체 텍스트 추출"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                # 처음 10페이지만 (초록은 대부분 앞쪽에 있음)
                for page in pdf.pages[:10]:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            print(f"❌ PDF 읽기 실패 {pdf_path}: {e}")
            return ""

    def find_summary_section(self, text: str) -> Optional[str]:
        """
        텍스트에서 초록/요약 섹션 추출

        Returns:
            초록 텍스트 (없으면 None)
        """
        lines = text.split('\n')

        # 초록 시작 위치 찾기
        summary_start = -1
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if any(keyword in line_stripped for keyword in self.SUMMARY_KEYWORDS):
                summary_start = i
                break

        if summary_start == -1:
            return None

        # 초록 끝 위치 찾기
        summary_lines = []
        for i in range(summary_start + 1, len(lines)):
            line = lines[i].strip()

            # 종료 키워드 발견 시 중단
            if any(keyword in line for keyword in self.END_KEYWORDS):
                break

            # 빈 줄이 5개 이상 연속되면 중단
            if not line:
                continue

            summary_lines.append(line)

            # 최대 50줄까지만
            if len(summary_lines) >= 50:
                break

        summary = ' '.join(summary_lines).strip()

        # 최소 길이 체크 (100자 이상)
        if len(summary) < 100:
            return None

        return summary

    def parse_pdf_manual(
        self,
        pdf_path: str,
        title: str,
        domain: str,
        year: Optional[int] = None,
        authors: Optional[List[str]] = None,
        source: str = "정부보고서"
    ) -> Optional[PaperMetadata]:
        """
        PDF 파일에서 PaperMetadata 생성

        Args:
            pdf_path: PDF 파일 경로
            title: 보고서 제목
            domain: 도메인 분류
            year: 발행 연도
            authors: 저자/기관 리스트
            source: 출처

        Returns:
            PaperMetadata 객체 (실패 시 None)
        """
        print(f"\n📄 처리 중: {title}")

        # PDF 텍스트 추출
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            print(f"  ❌ 텍스트 추출 실패")
            return None

        # 초록 섹션 추출
        abstract = self.find_summary_section(text)
        if not abstract:
            print(f"  ⚠️ 초록 섹션을 찾을 수 없음")
            # 전체 텍스트의 처음 500자를 초록으로 사용 (fallback)
            abstract = text[:500].strip()

        print(f"  ✅ 초록 추출 완료 ({len(abstract)}자)")

        # PaperMetadata 생성
        paper = PaperMetadata(
            domain=domain,
            language='ko',
            title=title,
            abstract=abstract,
            keywords=[],
            source=source,
            year=year,
            pmid=None,
            doi=None,
            authors=authors or [],
            journal=source
        )

        return paper

    def parse_batch_from_json(self, json_path: str) -> List[PaperMetadata]:
        """
        JSON 설정 파일을 읽어서 여러 PDF를 일괄 처리

        JSON 형식:
        [
          {
            "pdf_path": "path/to/report.pdf",
            "title": "보고서 제목",
            "domain": "korean_diet",
            "year": 2020,
            "authors": ["보건복지부"],
            "source": "보건복지부"
          },
          ...
        ]
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            reports_config = json.load(f)

        papers = []
        for config in reports_config:
            paper = self.parse_pdf_manual(
                pdf_path=config['pdf_path'],
                title=config['title'],
                domain=config['domain'],
                year=config.get('year'),
                authors=config.get('authors'),
                source=config.get('source', '정부보고서')
            )
            if paper:
                papers.append(paper)

        return papers


def create_template():
    """
    정부 보고서 수집을 위한 JSON 템플릿 생성

    사용법:
    1. 정부 사이트에서 PDF 보고서 다운로드
    2. 이 템플릿에 정보 입력
    3. government_report_parser.py로 일괄 처리
    """
    template = [
        {
            "pdf_path": "downloads/mohw_nutrition_2023.pdf",
            "title": "2023 국민건강영양조사 영양 섭취 기준",
            "domain": "korean_diet",
            "year": 2023,
            "authors": ["보건복지부", "질병관리청"],
            "source": "보건복지부"
        },
        {
            "pdf_path": "downloads/mfds_functional_food_2022.pdf",
            "title": "기능성 식품 섭취 가이드라인",
            "domain": "protein_hypertrophy",
            "year": 2022,
            "authors": ["식품의약품안전처"],
            "source": "식약처"
        },
        {
            "pdf_path": "downloads/ksns_protein_guideline_2021.pdf",
            "title": "한국인을 위한 단백질 섭취 기준",
            "domain": "protein_hypertrophy",
            "year": 2021,
            "authors": ["대한영양학회"],
            "source": "대한영양학회"
        }
    ]

    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    template_path = output_dir / "government_reports_template.json"
    with open(template_path, 'w', encoding='utf-8') as f:
        json.dump(template, f, ensure_ascii=False, indent=2)

    print(f"✅ 템플릿 생성: {template_path}")
    print("\n📋 사용 방법:")
    print("1. 정부/기관 사이트에서 PDF 보고서 다운로드")
    print("2. 템플릿에 PDF 경로와 메타데이터 입력")
    print("3. python government_report_parser.py 실행")

    return str(template_path)


def main():
    """메인 실행 함수"""

    # 템플릿 생성
    template_path = create_template()

    print("\n" + "=" * 60)
    print("📚 정부 보고서 수집 가이드")
    print("=" * 60)

    print("\n🔗 추천 사이트:")
    print("  1. 보건복지부: https://www.mohw.go.kr/")
    print("     - 국민건강영양조사 결과")
    print("     - 한국인 영양섭취기준")
    print("")
    print("  2. 질병관리청: https://www.kdca.go.kr/")
    print("     - KNHANES 원시자료")
    print("     - 만성질환 예방 가이드")
    print("")
    print("  3. 식약처: https://www.mfds.go.kr/")
    print("     - 기능성 식품 가이드라인")
    print("     - 영양성분 기준")
    print("")
    print("  4. 대한영양학회: http://www.kns.or.kr/")
    print("     - 단백질 섭취 기준")
    print("     - 한국인 영양소 섭취기준")
    print("")
    print("  5. 체육과학연구원: https://www.sports.re.kr/")
    print("     - 운동 영양 가이드")
    print("     - 체력 평가 기준")

    print("\n📥 예상 수집량:")
    print("  - 보건복지부: 30-50개 보고서")
    print("  - 질병관리청: 20-30개 보고서")
    print("  - 식약처: 10-20개 보고서")
    print("  - 학회: 20-30개 가이드라인")
    print("  - 총 80-130개 공식 문서")

    print("\n🎯 다음 단계:")
    print(f"  1. {template_path} 파일 수정")
    print("  2. PDF 파일 다운로드")
    print("  3. python government_report_parser.py --process 실행")

    # 만약 --process 옵션이 있으면 실제 처리
    import sys
    if '--process' in sys.argv:
        parser = GovernmentReportParser()

        if Path(template_path).exists():
            print("\n" + "=" * 60)
            print("🚀 보고서 처리 시작")
            print("=" * 60)

            papers = parser.parse_batch_from_json(template_path)

            if papers:
                # 결과 저장
                output_dir = Path("outputs")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                output_path = output_dir / f"government_reports_{timestamp}.json"
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump([p.model_dump() for p in papers], f, ensure_ascii=False, indent=2)

                print(f"\n✅ 수집 완료: {len(papers)}개 문서")
                print(f"   저장 경로: {output_path}")
            else:
                print("\n⚠️ 수집된 문서가 없습니다.")
        else:
            print(f"\n❌ 템플릿 파일이 없습니다: {template_path}")


if __name__ == "__main__":
    main()
