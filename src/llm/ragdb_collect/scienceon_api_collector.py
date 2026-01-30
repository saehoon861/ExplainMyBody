"""
ScienceON API Gateway를 사용한 한국어 논문 자동 수집

KISTI의 ScienceON API를 사용하여 과학기술 논문을 자동으로 수집합니다.
1억 3780만 건 이상의 논문 데이터베이스 (2026-01-19 기준)

API 키 발급:
https://apigateway.kisti.re.kr/

토큰 발급 방식:
1. MAC 주소 + 현재 시간 → JSON
2. 인증키로 AES256 암호화
3. URI 인코딩
4. Access Token 발급 (2시간 유효)
5. Refresh Token으로 자동 갱신 (2주 유효)
"""

import requests
import time
import json
import uuid
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64

from models import PaperMetadata


class TokenManager:
    """ScienceON API Gateway 토큰 관리"""

    def __init__(self, client_id: str, auth_key: str, mac_address: Optional[str] = None):
        """
        Args:
            client_id: 클라이언트 ID (발급받은 64자리)
            auth_key: 인증키 (32자리, AES256 암호화에 사용)
            mac_address: MAC 주소 (없으면 자동 생성)
        """
        self.client_id = client_id
        self.auth_key = auth_key
        self.mac_address = mac_address or self._get_mac_address()
        
        # 토큰 저장
        self.access_token: Optional[str] = None
        self.access_token_expire: Optional[datetime] = None
        self.refresh_token: Optional[str] = None
        self.refresh_token_expire: Optional[datetime] = None
        
        # API 엔드포인트
        self.token_url = "https://apigateway.kisti.re.kr/tokenrequest.do"

    def _get_mac_address(self) -> str:
        """시스템 MAC 주소 가져오기"""
        mac = uuid.getnode()
        mac_str = ':'.join(('%012X' % mac)[i:i+2] for i in range(0, 12, 2))
        return mac_str

    def _encrypt_accounts(self, mac_address: str, datetime_str: str) -> str:
        """
        accounts 파라미터 생성 (AES256 암호화 + URI 인코딩)
        
        Args:
            mac_address: MAC 주소
            datetime_str: 현재 시간 (YYYYMMDDHHmmss)
        
        Returns:
            암호화된 accounts 값
        """
        # JSON 데이터 생성
        data = {
            "mac_address": mac_address,
            "datetime": datetime_str
        }
        json_str = json.dumps(data, separators=(',', ':'))
        
        # AES256 암호화
        cipher = AES.new(
            self.auth_key.encode('utf-8'),
            AES.MODE_ECB
        )
        padded_data = pad(json_str.encode('utf-8'), AES.block_size)
        encrypted = cipher.encrypt(padded_data)
        
        # Base64 인코딩
        encrypted_b64 = base64.b64encode(encrypted).decode('utf-8')
        
        # URI 인코딩
        return quote(encrypted_b64)

    def request_token(self) -> bool:
        """
        Access Token과 Refresh Token 발급
        
        Returns:
            성공 여부
        """
        try:
            # 현재 시간
            now = datetime.now()
            datetime_str = now.strftime('%Y%m%d%H%M%S')
            
            # accounts 파라미터 생성
            accounts = self._encrypt_accounts(self.mac_address, datetime_str)
            
            # 토큰 요청
            url = f"{self.token_url}?accounts={accounts}&client_id={self.client_id}"
            
            print(f"🔑 토큰 발급 요청 중...")
            print(f"   MAC 주소: {self.mac_address}")
            print(f"   시간: {datetime_str}")
            
            response = requests.get(url, timeout=30)
            
            if response.status_code != 200:
                print(f"❌ 토큰 발급 실패 (status: {response.status_code})")
                print(f"   응답: {response.text}")
                return False
            
            # 응답 파싱
            data = response.json()
            
            # 에러 체크
            if 'errorCode' in data:
                print(f"❌ 토큰 발급 실패: {data.get('errorMessage')}")
                print(f"   에러 코드: {data.get('errorCode')}")
                return False
            
            # 토큰 저장
            self.access_token = data['access_token']
            self.access_token_expire = datetime.strptime(
                data['access_token_expire'], 
                '%Y-%m-%d %H:%M:%S.%f'
            )
            self.refresh_token = data['refresh_token']
            self.refresh_token_expire = datetime.strptime(
                data['refresh_token_expire'],
                '%Y-%m-%d %H:%M:%S.%f'
            )
            
            print(f"✅ 토큰 발급 성공")
            print(f"   Access Token 만료: {self.access_token_expire}")
            print(f"   Refresh Token 만료: {self.refresh_token_expire}")
            
            return True
            
        except Exception as e:
            print(f"❌ 토큰 발급 실패: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_valid_token(self) -> Optional[str]:
        """
        유효한 Access Token 반환 (자동 갱신)
        
        Returns:
            Access Token 또는 None
        """
        now = datetime.now()
        
        # 토큰이 없거나 만료됨
        if not self.access_token or not self.access_token_expire:
            if not self.request_token():
                return None
            return self.access_token
        
        # Access Token이 5분 내 만료 예정
        if now >= self.access_token_expire - timedelta(minutes=5):
            print(f"🔄 Access Token 갱신 필요 (만료 임박)")
            
            # Refresh Token도 만료됨
            if now >= self.refresh_token_expire:
                print(f"⚠️ Refresh Token도 만료됨. 재발급 필요")
                if not self.request_token():
                    return None
            else:
                # TODO: Refresh Token으로 갱신 구현
                # 현재는 새로 발급
                if not self.request_token():
                    return None
        
        return self.access_token


class ScienceOnAPICollector:
    """ScienceON API Gateway 수집기 (토큰 기반)"""

    def __init__(self, client_id: str, auth_key: str, mac_address: Optional[str] = None):
        """
        Args:
            client_id: 클라이언트 ID (64자리)
            auth_key: 인증키 (32자리)
            mac_address: MAC 주소 (선택, 없으면 자동)
        """
        # 토큰 매니저
        self.token_manager = TokenManager(client_id, auth_key, mac_address)
        
        # ScienceON API Gateway 엔드포인트
        self.search_url = "https://apigateway.kisti.re.kr/api/articlesearch"
        
        # Rate limiting
        self.rate_limit = 2  # 2초 대기

    def search_papers(
        self,
        query: str,
        max_results: int = 100,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        language: str = "ko"  # ko: 한국어, en: 영어
    ) -> List[dict]:
        """
        ScienceON에서 논문 검색

        Args:
            query: 검색어
            max_results: 최대 결과 수
            start_year: 시작 연도
            end_year: 종료 연도
            language: 언어 필터 (ko, en)

        Returns:
            논문 정보 딕셔너리 리스트
        """
        papers = []

        print(f"\n🔍 ScienceON 검색: '{query}' (최대 {max_results}개)")

        # 페이지네이션
        page_size = 100
        total_pages = (max_results + page_size - 1) // page_size

        for page in range(1, total_pages + 1):
            try:
                # 유효한 토큰 가져오기
                token = self.token_manager.get_valid_token()
                if not token:
                    print(f"  ❌ 유효한 토큰을 가져올 수 없습니다")
                    break
                
                # API 요청 파라미터
                params = {
                    'access_token': token,
                    'query': query,
                    'pageNo': page,
                    'numOfRows': min(page_size, max_results - len(papers))
                }
                
                # 연도 필터
                if start_year:
                    params['startYear'] = start_year
                if end_year:
                    params['endYear'] = end_year

                # API 요청
                response = requests.get(
                    self.search_url,
                    params=params,
                    timeout=30
                )

                if response.status_code != 200:
                    print(f"  ⚠️ API 요청 실패 (status: {response.status_code})")
                    print(f"  📄 응답 내용: {response.text[:500]}")
                    break

                # JSON 파싱
                try:
                    data = response.json()
                except json.JSONDecodeError as e:
                    print(f"  ❌ JSON 파싱 실패: {e}")
                    print(f"  📄 응답 내용 (처음 500자):")
                    print(f"  {response.text[:500]}")
                    print(f"  📋 Content-Type: {response.headers.get('Content-Type')}")
                    break

                # API 응답 구조 확인 (첫 페이지만)
                if page == 1:
                    print(f"  🔍 API 응답 구조:")
                    print(f"     키 목록: {list(data.keys())}")
                    
                # 총 결과 수 확인 (다양한 필드명 시도)
                total = None
                if page == 1:
                    for total_key in ['total', 'totalCount', 'totalItems', 'count']:
                        if total_key in data:
                            total = data[total_key]
                            print(f"  📊 총 {total:,}개 논문 발견 (필드: {total_key})")
                            break
                    
                    if total is None:
                        print(f"  ⚠️ 총 개수 정보를 찾을 수 없습니다")

                # 논문 정보 추출 (다양한 필드명 시도)
                items = []
                for items_key in ['items', 'data', 'results', 'list', 'records']:
                    if items_key in data:
                        items = data[items_key]
                        if page == 1:
                            print(f"  📋 데이터 필드: {items_key} ({len(items) if isinstance(items, list) else 0}개)")
                        break

                if not items:
                    print(f"  ⚠️ {page}페이지에 결과 없음")
                    break

                for item in items:
                    paper_info = self._parse_scienceon_item(item)
                    if paper_info:
                        papers.append(paper_info)

                print(f"  ✅ {page}/{total_pages} 페이지: {len(items)}개 수집 (총 {len(papers)}개)")

                # Rate limiting
                time.sleep(self.rate_limit)

                # 목표 달성
                if len(papers) >= max_results:
                    break

            except Exception as e:
                print(f"  ❌ 페이지 {page} 처리 실패: {e}")
                continue

        print(f"✅ ScienceON 검색 완료: {len(papers)}개 수집")
        return papers

    def _parse_scienceon_item(self, item: dict) -> Optional[dict]:
        """ScienceON JSON 아이템을 딕셔너리로 파싱"""
        try:
            # 제목
            title = item.get('title', '').strip()
            if not title:
                return None

            # 초록
            abstract = item.get('abstract', '').strip()

            # 초록이 너무 짧으면 스킵
            if len(abstract) < 100:
                return None

            # 키워드
            keywords = item.get('keywords', [])
            if isinstance(keywords, str):
                keywords = [k.strip() for k in keywords.split(',')]

            # 연도
            year = item.get('year')
            if year:
                try:
                    year = int(year)
                except:
                    year = None

            # 저자
            authors_raw = item.get('authors', [])
            authors = []
            if isinstance(authors_raw, list):
                for author in authors_raw[:5]:
                    if isinstance(author, dict):
                        name = author.get('name', '')
                    else:
                        name = str(author)
                    if name:
                        authors.append(name.strip())
            elif isinstance(authors_raw, str):
                authors = [a.strip() for a in authors_raw.split(',')][:5]

            # 저널
            journal = item.get('journal', {})
            if isinstance(journal, dict):
                journal_name = journal.get('title', 'ScienceON')
            else:
                journal_name = str(journal) if journal else 'ScienceON'

            # DOI
            doi = item.get('doi')

            return {
                'title': title,
                'abstract': abstract,
                'keywords': keywords,
                'year': year,
                'authors': authors,
                'journal': journal_name,
                'doi': doi
            }

        except Exception as e:
            print(f"  ⚠️ 아이템 파싱 실패: {e}")
            return None

    def collect_domain(
        self,
        domain: str,
        queries: List[str],
        target_count: int,
        start_year: int = 2010
    ) -> List[PaperMetadata]:
        """
        특정 도메인의 논문 수집

        Args:
            domain: 도메인 분류
            queries: 검색어 리스트
            target_count: 목표 수집 개수
            start_year: 시작 연도

        Returns:
            PaperMetadata 리스트
        """
        all_papers = []
        seen_titles = set()

        results_per_query = max(10, target_count // len(queries))
        current_year = datetime.now().year

        for query in queries:
            papers_data = self.search_papers(
                query=query,
                max_results=results_per_query,
                start_year=start_year,
                end_year=current_year,
                language='ko'
            )

            # PaperMetadata로 변환
            for data in papers_data:
                # 중복 체크
                title_normalized = data['title'].lower().strip()
                if title_normalized in seen_titles:
                    continue

                seen_titles.add(title_normalized)

                # PaperMetadata 생성
                paper = PaperMetadata(
                    domain=domain,
                    language='ko',
                    title=data['title'],
                    abstract=data['abstract'],
                    keywords=data['keywords'],
                    source='ScienceON',
                    year=data['year'],
                    pmid=None,
                    doi=data.get('doi'),
                    authors=data['authors'],
                    journal=data['journal']
                )

                all_papers.append(paper)

            # 목표 달성
            if len(all_papers) >= target_count:
                break

            # 쿼리 간 대기
            time.sleep(2)

        return all_papers[:target_count]


def main():
    """메인 실행 함수"""

    print("=" * 60)
    print("🇰🇷 ScienceON API 한국어 논문 수집")
    print("=" * 60)
    print("📊 데이터베이스: 1억 3780만 건 이상 (2026-01-19 기준)")
    print("=" * 60)

    # API 키 입력
    print("\n📋 ScienceON API Gateway 인증 정보:")
    print("  1. https://apigateway.kisti.re.kr/ 접속")
    print("  2. 회원가입 → API 사용 신청")
    print("  3. 승인 후 다음 정보 발급:")
    print("     - Client ID (64자리)")
    print("     - 인증키 (32자리, AES256 암호화용)")
    print("     - MAC 주소 (신청 시 제출)")
    print("")

    client_id = input("Client ID (64자리)를 입력하세요: ").strip()
    auth_key = input("인증키 (32자리)를 입력하세요: ").strip()
    mac_address = input("MAC 주소 (선택, 엔터=자동): ").strip() or None

    if not client_id or not auth_key:
        print("❌ Client ID와 인증키가 필요합니다.")
        return
    
    if len(auth_key) != 32:
        print("❌ 인증키는 32자리여야 합니다.")
        return

    # 수집기 초기화
    collector = ScienceOnAPICollector(
        client_id=client_id,
        auth_key=auth_key,
        mac_address=mac_address
    )

    # 한국어 검색어
    KOREAN_DIET_QUERIES = [
        "한식 영양",
        "김치 건강",
        "발효식품",
        "한국 식습관",
        "전통음식",
    ]

    BODY_COMPOSITION_QUERIES = [
        "근감소증",
        "체성분 분석",
        "골격근량",
        "체지방",
        "생체전기저항",
    ]

    # 한국 식단 수집
    print("\n" + "=" * 60)
    print("📚 도메인 1: 한국형 식단 (목표: 300개)")
    print("=" * 60)

    korean_diet_papers = collector.collect_domain(
        domain='korean_diet',
        queries=KOREAN_DIET_QUERIES,
        target_count=300,
        start_year=2010
    )

    # 체형 분석 수집
    print("\n" + "=" * 60)
    print("📚 도메인 2: 체형 분석/인바디 (목표: 300개)")
    print("=" * 60)

    body_comp_papers = collector.collect_domain(
        domain='body_composition',
        queries=BODY_COMPOSITION_QUERIES,
        target_count=300,
        start_year=2010
    )

    # 전체 수집 결과
    all_papers = korean_diet_papers + body_comp_papers

    # 결과 저장
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 전체 저장
    corpus_path = output_dir / f"scienceon_korean_{timestamp}.json"
    with open(corpus_path, "w", encoding="utf-8") as f:
        json.dump([p.model_dump() for p in all_papers], f, ensure_ascii=False, indent=2)

    print(f"\n✅ 저장 완료: {corpus_path}")

    # 도메인별 저장
    if korean_diet_papers:
        diet_path = output_dir / f"korean_diet_scienceon_{timestamp}.json"
        with open(diet_path, "w", encoding="utf-8") as f:
            json.dump([p.model_dump() for p in korean_diet_papers], f, ensure_ascii=False, indent=2)
        print(f"   - 한국 식단: {diet_path} ({len(korean_diet_papers)}개)")

    if body_comp_papers:
        body_path = output_dir / f"body_composition_scienceon_{timestamp}.json"
        with open(body_path, "w", encoding="utf-8") as f:
            json.dump([p.model_dump() for p in body_comp_papers], f, ensure_ascii=False, indent=2)
        print(f"   - 체형 분석: {body_path} ({len(body_comp_papers)}개)")

    # 통계
    print("\n" + "=" * 60)
    print("📊 수집 완료")
    print("=" * 60)
    print(f"총 수집: {len(all_papers)}개")
    print(f"  - 한국 식단: {len(korean_diet_papers)}개")
    print(f"  - 체형 분석: {len(body_comp_papers)}개")
    print("=" * 60)


if __name__ == "__main__":
    main()
