"""
학술지 CSV/Excel 파서

대한영양학회, 한국체육학회 등 학술단체에서 제공하는
논문 목록 CSV/Excel 파일을 PaperMetadata로 변환합니다.
"""

import json
import csv
from typing import List, Optional, Dict
from pathlib import Path
from datetime import datetime

try:
    import pandas as pd
except ImportError:
    print("❌ pandas 라이브러리가 필요합니다: pip install pandas openpyxl")
    exit(1)

from models import PaperMetadata


class SocietyCSVParser:
    """학술지 CSV/Excel 파서"""

    # 컬럼 매핑 (다양한 형식 지원)
    COLUMN_MAPPINGS = {
        'title': ['제목', 'title', '논문명', '논문제목', 'Title', 'Article Title'],
        'abstract': ['초록', 'abstract', '요약', 'Abstract', 'Summary'],
        'keywords': ['키워드', 'keywords', 'Keyword', 'Keywords', '주제어'],
        'year': ['발행년도', 'year', '연도', 'Year', 'Publication Year'],
        'authors': ['저자', 'author', 'authors', 'Author', 'Authors'],
        'journal': ['학술지', 'journal', 'Journal', '저널', '학회지']
    }

    def __init__(self):
        pass

    def find_column(self, df: pd.DataFrame, field: str) -> Optional[str]:
        """
        DataFrame에서 필드에 해당하는 컬럼명 찾기

        Args:
            df: pandas DataFrame
            field: 찾을 필드 (title, abstract, etc.)

        Returns:
            실제 컬럼명 (없으면 None)
        """
        possible_names = self.COLUMN_MAPPINGS.get(field, [])

        for col in df.columns:
            if col in possible_names:
                return col

        return None

    def parse_csv(
        self,
        csv_path: str,
        domain: str,
        source: str = "학술지",
        encoding: str = "utf-8"
    ) -> List[PaperMetadata]:
        """
        CSV 파일에서 PaperMetadata 리스트 생성

        Args:
            csv_path: CSV 파일 경로
            domain: 도메인 분류
            source: 출처 (학회명 등)
            encoding: 파일 인코딩 (기본: utf-8, 한국어 파일은 cp949 시도)

        Returns:
            PaperMetadata 리스트
        """
        print(f"\n📄 처리 중: {csv_path}")

        try:
            # CSV 읽기 (인코딩 자동 감지)
            try:
                df = pd.read_csv(csv_path, encoding=encoding)
            except UnicodeDecodeError:
                # cp949 시도
                df = pd.read_csv(csv_path, encoding='cp949')

        except Exception as e:
            print(f"  ❌ CSV 읽기 실패: {e}")
            return []

        # 컬럼 매핑
        title_col = self.find_column(df, 'title')
        abstract_col = self.find_column(df, 'abstract')
        keywords_col = self.find_column(df, 'keywords')
        year_col = self.find_column(df, 'year')
        authors_col = self.find_column(df, 'authors')
        journal_col = self.find_column(df, 'journal')

        if not title_col:
            print(f"  ❌ '제목' 컬럼을 찾을 수 없습니다")
            print(f"     사용 가능한 컬럼: {list(df.columns)}")
            return []

        papers = []

        # 각 행 처리
        for idx, row in df.iterrows():
            try:
                # 제목 필수
                title = str(row[title_col]).strip()
                if not title or title == 'nan':
                    continue

                # 초록 (없으면 빈 문자열)
                abstract = ""
                if abstract_col and abstract_col in row:
                    abstract = str(row[abstract_col]).strip()
                    if abstract == 'nan':
                        abstract = ""

                # 초록이 너무 짧으면 스킵
                if len(abstract) < 100:
                    print(f"  ⚠️ 초록이 너무 짧아 스킵: {title[:30]}...")
                    continue

                # 키워드 파싱
                keywords = []
                if keywords_col and keywords_col in row:
                    kw_str = str(row[keywords_col]).strip()
                    if kw_str and kw_str != 'nan':
                        # 세미콜론, 쉼표, 슬래시로 구분
                        keywords = [k.strip() for k in kw_str.replace(';', ',').replace('/', ',').split(',')]
                        keywords = [k for k in keywords if k]

                # 연도 파싱
                year = None
                if year_col and year_col in row:
                    try:
                        year = int(row[year_col])
                    except:
                        pass

                # 저자 파싱
                authors = []
                if authors_col and authors_col in row:
                    authors_str = str(row[authors_col]).strip()
                    if authors_str and authors_str != 'nan':
                        # 세미콜론, 쉼표로 구분
                        authors = [a.strip() for a in authors_str.replace(';', ',').split(',')]
                        authors = [a for a in authors if a][:5]  # 최대 5명

                # 저널명
                journal = source
                if journal_col and journal_col in row:
                    journal_name = str(row[journal_col]).strip()
                    if journal_name and journal_name != 'nan':
                        journal = journal_name

                # PaperMetadata 생성
                paper = PaperMetadata(
                    domain=domain,
                    language='ko',
                    title=title,
                    abstract=abstract,
                    keywords=keywords,
                    source=source,
                    year=year,
                    pmid=None,
                    doi=None,
                    authors=authors,
                    journal=journal
                )

                papers.append(paper)

            except Exception as e:
                print(f"  ⚠️ 행 {idx} 처리 실패: {e}")
                continue

        print(f"  ✅ {len(papers)}개 논문 파싱 완료")
        return papers

    def parse_excel(
        self,
        excel_path: str,
        domain: str,
        source: str = "학술지",
        sheet_name: int = 0
    ) -> List[PaperMetadata]:
        """
        Excel 파일에서 PaperMetadata 리스트 생성

        Args:
            excel_path: Excel 파일 경로
            domain: 도메인 분류
            source: 출처
            sheet_name: 시트 번호 또는 이름 (기본: 첫 번째 시트)

        Returns:
            PaperMetadata 리스트
        """
        print(f"\n📊 처리 중: {excel_path}")

        try:
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
        except Exception as e:
            print(f"  ❌ Excel 읽기 실패: {e}")
            return []

        # CSV와 동일한 로직 사용
        # (DataFrame으로 변환되었으므로 동일하게 처리)
        return self._parse_dataframe(df, domain, source)

    def _parse_dataframe(self, df: pd.DataFrame, domain: str, source: str) -> List[PaperMetadata]:
        """DataFrame을 PaperMetadata 리스트로 변환 (내부 메서드)"""

        # 컬럼 매핑
        title_col = self.find_column(df, 'title')
        abstract_col = self.find_column(df, 'abstract')
        keywords_col = self.find_column(df, 'keywords')
        year_col = self.find_column(df, 'year')
        authors_col = self.find_column(df, 'authors')
        journal_col = self.find_column(df, 'journal')

        if not title_col:
            print(f"  ❌ '제목' 컬럼을 찾을 수 없습니다")
            return []

        papers = []

        for idx, row in df.iterrows():
            try:
                title = str(row[title_col]).strip()
                if not title or title == 'nan':
                    continue

                abstract = ""
                if abstract_col:
                    abstract = str(row[abstract_col]).strip()
                    if abstract == 'nan':
                        abstract = ""

                if len(abstract) < 100:
                    continue

                keywords = []
                if keywords_col:
                    kw_str = str(row[keywords_col]).strip()
                    if kw_str != 'nan':
                        keywords = [k.strip() for k in kw_str.replace(';', ',').split(',')]

                year = None
                if year_col:
                    try:
                        year = int(row[year_col])
                    except:
                        pass

                authors = []
                if authors_col:
                    authors_str = str(row[authors_col]).strip()
                    if authors_str != 'nan':
                        authors = [a.strip() for a in authors_str.replace(';', ',').split(',')][:5]

                journal = source
                if journal_col:
                    j = str(row[journal_col]).strip()
                    if j != 'nan':
                        journal = j

                paper = PaperMetadata(
                    domain=domain,
                    language='ko',
                    title=title,
                    abstract=abstract,
                    keywords=keywords,
                    source=source,
                    year=year,
                    pmid=None,
                    doi=None,
                    authors=authors,
                    journal=journal
                )

                papers.append(paper)

            except Exception as e:
                continue

        print(f"  ✅ {len(papers)}개 논문 파싱 완료")
        return papers


def create_template():
    """CSV 템플릿 생성"""

    template_data = [
        {
            "제목": "한국 성인의 단백질 섭취와 근육량의 관계",
            "초록": "본 연구는 한국 성인 1000명을 대상으로 단백질 섭취량과 근육량의 상관관계를 분석하였다. 결과적으로 체중 1kg당 1.2g 이상의 단백질을 섭취한 그룹에서 유의미하게 높은 근육량을 보였다.",
            "키워드": "단백질, 근육량, 한국인, 영양섭취",
            "발행년도": 2022,
            "저자": "김영희, 박철수, 이민지",
            "학술지": "대한영양학회지"
        },
        {
            "제목": "김치 섭취가 장내 미생물에 미치는 영향",
            "초록": "발효식품인 김치의 섭취가 장내 미생물 다양성에 미치는 영향을 분석한 연구. 12주간 매일 김치를 섭취한 그룹은 유익균이 증가하고 유해균이 감소하는 경향을 보였다.",
            "키워드": "김치, 발효식품, 장내미생물, 프로바이오틱스",
            "발행년도": 2021,
            "저자": "이수진, 최동욱",
            "학술지": "한국식품영양과학회지"
        }
    ]

    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    template_path = output_dir / "society_papers_template.csv"

    # CSV로 저장
    df = pd.DataFrame(template_data)
    df.to_csv(template_path, index=False, encoding='utf-8-sig')

    print(f"✅ CSV 템플릿 생성: {template_path}")
    print("\n📋 사용 방법:")
    print("1. 학술지 사이트에서 논문 목록 다운로드 (CSV 또는 Excel)")
    print("2. 컬럼명을 템플릿과 유사하게 맞추기 (제목, 초록, 키워드 등)")
    print("3. python society_csv_parser.py --process [파일경로] 실행")

    return str(template_path)


def main():
    """메인 실행 함수"""

    template_path = create_template()

    print("\n" + "=" * 60)
    print("📚 학술지 논문 수집 가이드")
    print("=" * 60)

    print("\n🔗 추천 학술지:")
    print("  1. 대한영양학회: http://www.kns.or.kr/")
    print("     - 한국영양학회지 (무료 논문 多)")
    print("")
    print("  2. 한국체육학회: http://www.koreasportscience.org/")
    print("     - 운동영양학회지")
    print("")
    print("  3. 한국식품영양과학회: http://www.kosfost.or.kr/")
    print("     - 발효식품, 한식 연구")
    print("")
    print("  4. 대한비만학회: http://www.kosso.or.kr/")
    print("     - 체지방, 체성분 연구")
    print("")
    print("  5. 대한노인병학회: http://www.geriatrics.or.kr/")
    print("     - 근감소증, 노화 연구")

    print("\n📥 수집 방법:")
    print("  1. 학회 사이트 접속")
    print("  2. 검색 또는 최신 논문 목록")
    print("  3. Excel/CSV 다운로드 (대부분 무료 제공)")
    print("  4. 초록이 포함된 논문만 선택")

    print("\n📊 예상 수집량:")
    print("  - 영양학회: 50-100개")
    print("  - 체육학회: 30-50개")
    print("  - 식품학회: 30-50개")
    print("  - 비만학회: 20-30개")
    print("  - 총 130-230개")

    # --process 옵션이 있으면 실제 처리
    import sys
    if '--process' in sys.argv and len(sys.argv) > 2:
        csv_path = sys.argv[2]

        if not Path(csv_path).exists():
            print(f"\n❌ 파일이 없습니다: {csv_path}")
            return

        parser = SocietyCSVParser()

        # 도메인 선택
        print("\n도메인 선택:")
        print("  1. protein_hypertrophy (단백질/근육)")
        print("  2. fat_loss (체지방 감량)")
        print("  3. korean_diet (한국 식단)")
        print("  4. body_composition (체성분 분석)")
        domain_input = input("번호 입력 (기본: 3): ").strip() or "3"

        domain_map = {
            "1": "protein_hypertrophy",
            "2": "fat_loss",
            "3": "korean_diet",
            "4": "body_composition"
        }
        domain = domain_map.get(domain_input, "korean_diet")

        # 출처 입력
        source = input("출처 입력 (예: 대한영양학회): ").strip() or "학술지"

        # 파일 확장자에 따라 처리
        if csv_path.endswith('.csv'):
            papers = parser.parse_csv(csv_path, domain, source)
        elif csv_path.endswith(('.xlsx', '.xls')):
            papers = parser.parse_excel(csv_path, domain, source)
        else:
            print(f"❌ 지원하지 않는 형식입니다. CSV 또는 Excel 파일을 사용하세요.")
            return

        if papers:
            # 결과 저장
            output_dir = Path("outputs")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            output_path = output_dir / f"society_papers_{timestamp}.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump([p.model_dump() for p in papers], f, ensure_ascii=False, indent=2)

            print(f"\n✅ 수집 완료: {len(papers)}개 논문")
            print(f"   저장 경로: {output_path}")
        else:
            print("\n⚠️ 파싱된 논문이 없습니다.")


if __name__ == "__main__":
    main()
