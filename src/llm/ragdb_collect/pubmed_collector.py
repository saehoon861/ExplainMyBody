"""
PubMed API를 사용한 논문 초록 수집
"""

import time
import requests
from typing import List, Optional
from xml.etree import ElementTree as ET

from models import PaperMetadata
import config


class PubMedCollector:
    """PubMed API 수집기"""

    def __init__(self, email: str, api_key: Optional[str] = None):
        """
        Args:
            email: NCBI 요구사항 (rate limit 완화)
            api_key: API Key (선택, 있으면 초당 10개 요청 가능)
        """
        self.email = email
        self.api_key = api_key
        self.base_url = config.PUBMED_BASE_URL

    def search(self, query: str, max_results: int = 100) -> List[str]:
        """
        PubMed 검색 (PMID 리스트 반환)

        Args:
            query: 검색 쿼리
            max_results: 최대 결과 수

        Returns:
            PMID 리스트
        """
        url = f"{self.base_url}esearch.fcgi"
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "email": self.email,
        }

        if self.api_key:
            params["api_key"] = self.api_key

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            pmid_list = data.get("esearchresult", {}).get("idlist", [])
            print(f"  - 검색어: '{query[:50]}...' → {len(pmid_list)}개 발견")
            return pmid_list

        except Exception as e:
            print(f"  ⚠️  검색 실패: {e}")
            return []

    def fetch_abstracts(self, pmid_list: List[str]) -> List[dict]:
        """
        PMID 리스트로부터 초록 및 메타데이터 가져오기

        Args:
            pmid_list: PMID 리스트

        Returns:
            논문 정보 딕셔너리 리스트
        """
        if not pmid_list:
            return []

        url = f"{self.base_url}efetch.fcgi"
        params = {
            "db": "pubmed",
            "id": ",".join(pmid_list),
            "retmode": "xml",
            "email": self.email,
        }

        if self.api_key:
            params["api_key"] = self.api_key

        try:
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()

            # XML 파싱
            root = ET.fromstring(response.content)
            papers = []

            for article in root.findall(".//PubmedArticle"):
                paper = self._parse_article(article)
                if paper:
                    papers.append(paper)

            print(f"  ✓ {len(papers)}개 초록 수집 완료")
            return papers

        except Exception as e:
            print(f"  ⚠️  초록 가져오기 실패: {e}")
            return []

    def _parse_article(self, article: ET.Element) -> Optional[dict]:
        """XML 논문 파싱"""
        try:
            # PMID
            pmid = article.findtext(".//PMID")

            # 제목
            title = article.findtext(".//ArticleTitle")
            if not title:
                return None

            # 초록
            abstract_texts = article.findall(".//AbstractText")
            if not abstract_texts:
                return None  # 초록 없으면 스킵

            abstract = " ".join([a.text or "" for a in abstract_texts])

            # 연도
            year_elem = article.find(".//PubDate/Year")
            year = int(year_elem.text) if year_elem is not None and year_elem.text else None

            # 저널
            journal = article.findtext(".//Journal/Title")

            # 저자
            authors = []
            for author in article.findall(".//Author"):
                lastname = author.findtext("LastName")
                forename = author.findtext("ForeName")
                if lastname:
                    name = f"{lastname}"
                    if forename:
                        name = f"{forename} {lastname}"
                    authors.append(name)

            # 키워드
            keywords = []
            for keyword in article.findall(".//Keyword"):
                if keyword.text:
                    keywords.append(keyword.text)

            # MeSH terms도 키워드로 추가
            for mesh in article.findall(".//MeshHeading/DescriptorName"):
                if mesh.text:
                    keywords.append(mesh.text)

            # DOI
            doi = None
            for article_id in article.findall(".//ArticleId"):
                if article_id.get("IdType") == "doi":
                    doi = article_id.text

            return {
                "pmid": pmid,
                "title": title,
                "abstract": abstract,
                "year": year,
                "journal": journal,
                "authors": authors[:5],  # 최대 5명만
                "keywords": keywords[:10],  # 최대 10개만
                "doi": doi,
            }

        except Exception as e:
            print(f"  ⚠️  파싱 실패: {e}")
            return None

    def collect_domain(
        self,
        domain: str,
        queries: List[str],
        target_count: int,
        results_per_query: int = 100,
    ) -> List[PaperMetadata]:
        """
        특정 도메인의 논문 수집

        Args:
            domain: 도메인 이름
            queries: 검색 쿼리 리스트
            target_count: 목표 수집 개수
            results_per_query: 쿼리당 결과 수

        Returns:
            PaperMetadata 리스트
        """
        print(f"\n{'='*60}")
        print(f"도메인: {domain} (목표: {target_count}개)")
        print(f"{'='*60}")

        all_papers = []
        seen_pmids = set()

        for i, query in enumerate(queries, 1):
            if len(all_papers) >= target_count:
                print(f"  ✓ 목표 달성 ({len(all_papers)}개)")
                break

            print(f"\n[{i}/{len(queries)}] 검색 중...")

            # 검색
            pmid_list = self.search(query, max_results=results_per_query)

            # 중복 제거
            new_pmids = [p for p in pmid_list if p not in seen_pmids]
            seen_pmids.update(new_pmids)

            if not new_pmids:
                print("  - 새로운 결과 없음")
                continue

            # 초록 가져오기
            papers = self.fetch_abstracts(new_pmids)

            # PaperMetadata로 변환
            for paper in papers:
                if not paper.get("abstract"):
                    continue

                metadata = PaperMetadata(
                    domain=domain,
                    language="en",
                    title=paper["title"],
                    abstract=paper["abstract"],
                    keywords=paper.get("keywords", []),
                    source="PubMed",
                    year=paper.get("year"),
                    pmid=paper.get("pmid"),
                    doi=paper.get("doi"),
                    authors=paper.get("authors", []),
                    journal=paper.get("journal"),
                )
                all_papers.append(metadata)

            # Rate limit (API key 없으면 초당 3개 제한)
            sleep_time = 0.34 if not self.api_key else 0.1
            time.sleep(sleep_time)

        print(f"\n✅ {domain} 수집 완료: {len(all_papers)}개")
        return all_papers[:target_count]  # 목표 개수만큼만 반환
