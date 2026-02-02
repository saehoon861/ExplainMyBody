"""
Graph RAG 구축 파이프라인

outputs 폴더의 논문 초록을 읽어서 Graph RAG를 구축합니다.
"""

import json
from pathlib import Path
from typing import List, Dict, Set, Optional
from collections import defaultdict
import os
import time

# .env 파일에서 환경변수 로드
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv 없음. .env 파일을 읽으려면 pip install python-dotenv 실행")

# Neo4j (선택) 또는 NetworkX (간단)
try:
    import networkx as nx
    USE_NETWORKX = True
except ImportError:
    USE_NETWORKX = False
    print("⚠️ NetworkX 없음. pip install networkx 권장")

# OpenAI (한국어 요약 생성용)
try:
    from openai import OpenAI
    USE_OPENAI = True
except ImportError:
    USE_OPENAI = False
    print("⚠️ OpenAI 없음. 한국어 요약 생성 불가. pip install openai 권장")

# Ollama (로컬 임베딩)
try:
    import ollama
    USE_OLLAMA = True
except ImportError:
    USE_OLLAMA = False
    print("⚠️ Ollama 없음. 한국어 임베딩 생성 불가. pip install ollama 권장")


class GraphRAGBuilder:
    """Graph RAG 구축기"""

    def __init__(self, schema_path: str = "graph_rag_schema.json",
                 generate_ko_summaries: bool = False,
                 generate_ko_embeddings: bool = False,
                 embedding_provider: str = "openai",
                 openai_api_key: Optional[str] = None,
                 ollama_model: str = "exaone3.5:7.8b",
                 ollama_embedding_model: str = "bge-m3:latest"):
        """
        Args:
            schema_path: 스키마 JSON 파일 경로
            generate_ko_summaries: 영어 논문에 대해 한국어 요약 생성 여부 (로컬 Ollama 사용)
            generate_ko_embeddings: 한국어 요약에 대해 임베딩 생성 여부
            embedding_provider: 임베딩 제공자 ("openai" 또는 "ollama")
            openai_api_key: OpenAI API 키 (없으면 환경변수에서 로드)
            ollama_model: Ollama 요약 생성 모델
            ollama_embedding_model: Ollama 임베딩 모델 (기본: bge-m3:latest)
        """
        # 스키마 로드
        with open(schema_path, 'r', encoding='utf-8') as f:
            self.schema = json.load(f)['graph_rag_schema']

        # Concept 딕셔너리 생성 (빠른 검색용)
        self.concepts = self._build_concept_dict()

        # Graph 초기화
        if USE_NETWORKX:
            self.graph = nx.MultiDiGraph()
        else:
            self.nodes = {}
            self.edges = []

        # 임베딩 설정
        self.generate_ko_embeddings = generate_ko_embeddings
        self.embedding_provider = embedding_provider.lower()
        self.ollama_embedding_model = ollama_embedding_model
        
        # Ollama 초기화 (한국어 요약 생성용 + 임베딩용)
        self.generate_ko_summaries = generate_ko_summaries
        self.ollama_model = ollama_model
        self.ollama_available = False
        
        if (generate_ko_summaries or (generate_ko_embeddings and self.embedding_provider == "ollama")) and USE_OLLAMA:
            try:
                # Ollama 연결 테스트
                ollama.list()
                self.ollama_available = True
                if generate_ko_summaries:
                    print(f"✅ Ollama 클라이언트 초기화 완료 (요약 모델: {ollama_model})")
                if generate_ko_embeddings and self.embedding_provider == "ollama":
                    print(f"✅ Ollama 임베딩 모델: {ollama_embedding_model}")
            except Exception as e:
                print(f"⚠️ Ollama 연결 실패: {e}")
                print("   Ollama 서버가 실행 중인지 확인하세요: ollama serve")
                self.generate_ko_summaries = False
                if self.embedding_provider == "ollama":
                    self.generate_ko_embeddings = False

        # OpenAI 초기화 (한국어 임베딩 생성용)
        self.openai_client = None
        if generate_ko_embeddings and self.embedding_provider == "openai" and USE_OPENAI:
            api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
                print("✅ OpenAI 클라이언트 초기화 완료 (임베딩: text-embedding-3-small)")
            else:
                print("⚠️ OpenAI API 키 없음. 한국어 임베딩 생성 비활성화")
                self.generate_ko_embeddings = False

        print(f"✅ 스키마 로드 완료: {len(self.concepts)}개 개념")

    def _build_concept_dict(self) -> Dict[str, Dict]:
        """개념 딕셔너리 구축 (한국어/영어/동의어로 검색)"""
        concepts = {}

        for category_name, category_data in self.schema['concept_categories'].items():
            for concept in category_data['concepts']:
                concept_id = concept['id']
                concepts[concept_id] = concept

                # 동의어 매핑
                concept['search_terms'] = set()
                concept['search_terms'].add(concept['name_ko'].lower())
                concept['search_terms'].add(concept['name_en'].lower())

                for syn in concept.get('synonyms_ko', []):
                    concept['search_terms'].add(syn.lower())
                for syn in concept.get('synonyms_en', []):
                    concept['search_terms'].add(syn.lower())

        return concepts

    def load_papers(self, corpus_path: str) -> List[Dict]:
        """논문 JSON 로드"""
        with open(corpus_path, 'r', encoding='utf-8') as f:
            papers = json.load(f)

        print(f"📄 논문 로드: {len(papers)}개")
        return papers

    def extract_mentioned_concepts(self, text: str, ko_summary: Optional[str] = None) -> List[Dict]:
        """
        텍스트에서 언급된 개념 추출

        Args:
            text: 논문 초록 (원본)
            ko_summary: 한국어 요약 (있는 경우)

        Returns:
            [{"concept_id": "muscle_hypertrophy", "confidence": 0.92}, ...]
        """
        # 원본 + 한국어 요약 결합
        combined_text = text
        if ko_summary:
            combined_text = f"{text} {ko_summary}"

        text_lower = combined_text.lower()
        mentioned = []

        for concept_id, concept in self.concepts.items():
            # 검색어 매칭
            for term in concept['search_terms']:
                if term in text_lower:
                    # 신뢰도 계산 (단순: 등장 횟수 기반)
                    count = text_lower.count(term)
                    confidence = min(0.5 + (count * 0.1), 1.0)

                    mentioned.append({
                        'concept_id': concept_id,
                        'concept_name_ko': concept['name_ko'],
                        'concept_name_en': concept['name_en'],
                        'matched_term': term,
                        'count': count,
                        'confidence': confidence
                    })
                    break  # 하나만 매칭되면 충분

        return mentioned

    def generate_korean_summary(self, english_abstract: str) -> Optional[str]:
        """
        영어 초록을 한국어로 요약 생성 (로컬 Ollama 사용)

        Args:
            english_abstract: 영어 초록

        Returns:
            한국어 요약 (실패 시 None)
        """
        if not self.generate_ko_summaries:
            return None

        try:
            prompt = f"""다음 영어 논문 초록을 읽고 핵심 내용을 2-3문장의 한국어로 요약하세요.
다음 정보를 반드시 포함하세요:
1. 주요 연구 목적
2. 핵심 결과 (숫자/수치 포함)
3. 임상적 의의

체성분, 근육, 영양, 운동 관련 키워드를 정확히 번역하세요.

논문 초록:
{english_abstract}

한국어 요약:"""

            response = ollama.chat(
                model=self.ollama_model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                options={
                    "temperature": 0.6,
                    "num_predict": 300
                }
            )

            summary = response['message']['content'].strip()
            time.sleep(0.2)  # Rate limiting (로컬이라 짧게)
            return summary

        except Exception as e:
            print(f"⚠️ 한국어 요약 생성 실패: {e}")
            return None

    def generate_korean_embedding(self, korean_text: str) -> Optional[List[float]]:
        """
        한국어 텍스트의 임베딩 생성 (OpenAI 또는 Ollama)

        Args:
            korean_text: 한국어 텍스트

        Returns:
            임베딩 벡터 (실패 시 None)
        """
        if not self.generate_ko_embeddings:
            return None
        
        # Ollama 임베딩
        if self.embedding_provider == "ollama":
            return self.generate_ollama_embedding(korean_text)
        
        # OpenAI 임베딩
        elif self.embedding_provider == "openai":
            return self.generate_openai_embedding(korean_text)
        
        return None
    
    def generate_ollama_embedding(self, text: str) -> Optional[List[float]]:
        """
        Ollama를 사용한 임베딩 생성 (bge-m3:latest 등)

        Args:
            text: 임베딩할 텍스트

        Returns:
            임베딩 벡터 (실패 시 None)
        """
        if not self.ollama_available:
            return None
        
        # 텍스트 검증
        if not text or not text.strip():
            return None
        
        # 텍스트 정제 (제어 문자 제거)
        clean_text = text.strip()
        if len(clean_text) < 10:  # 너무 짧은 텍스트 스킵
            return None

        try:
            response = ollama.embeddings(
                model=self.ollama_embedding_model,
                prompt=clean_text
            )
            embedding = response['embedding']
            
            # NaN 체크
            if any(isinstance(x, float) and (x != x) for x in embedding):  # x != x는 NaN 체크
                return None
            
            time.sleep(0.05)  # Rate limiting (로컬이라 짧게)
            return embedding

        except Exception as e:
            # NaN 에러는 조용히 스킵 (너무 많은 출력 방지)
            if "NaN" not in str(e):
                print(f"⚠️ Ollama 임베딩 생성 실패: {e}")
            return None
    
    def generate_openai_embedding(self, text: str) -> Optional[List[float]]:
        """
        OpenAI를 사용한 임베딩 생성

        Args:
            text: 임베딩할 텍스트

        Returns:
            임베딩 벡터 (실패 시 None)
        """
        if not self.openai_client:
            return None

        # OpenAI text-embedding-3-small 최대 토큰: 8191
        # 안전하게 최대 6000 토큰으로 제한 (대략 24000자)
        MAX_CHARS = 24000
        if len(text) > MAX_CHARS:
            text = text[:MAX_CHARS]

        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            embedding = response.data[0].embedding
            time.sleep(0.1)  # Rate limiting
            return embedding

        except Exception as e:
            print(f"⚠️ OpenAI 임베딩 생성 실패: {e}")
            return None

    def add_paper_node(self, paper: Dict, paper_id: str):
        """논문 노드 추가 (영어 논문인 경우 한국어 요약 생성 및 임베딩)"""
        abstract = paper.get('abstract', '')
        lang = paper.get('language', 'unknown')
        
        # abstract 검증
        if not abstract or not isinstance(abstract, str):
            abstract = paper.get('title', '')  # fallback to title

        # 한국어 요약 생성 (영어 논문만, 로컬 Ollama)
        chunk_ko_summary = None
        if self.generate_ko_summaries and lang == 'en' and abstract:
            chunk_ko_summary = self.generate_korean_summary(abstract)

        # 한국어 임베딩 생성 (한국어 요약이 있는 경우, 또는 한국어 논문)
        embedding_ko = None
        if self.generate_ko_embeddings:
            # 한국어 요약이 있으면 그걸 사용, 없으면 원본 abstract 사용
            text_to_embed = chunk_ko_summary if chunk_ko_summary else abstract
            if text_to_embed and text_to_embed.strip():
                embedding_ko = self.generate_korean_embedding(text_to_embed)

        node_data = {
            'node_type': 'paper',
            'id': paper_id,
            'title': paper['title'],
            'chunk_text': abstract,  # 원본 초록
            'lang': lang,
            'chunk_ko_summary': chunk_ko_summary,  # 한국어 요약
            'embedding_ko': embedding_ko,  # 한국어 임베딩 (OpenAI 또는 Ollama)
            'embedding_provider': self.embedding_provider if embedding_ko else None,
            'domain': paper['domain'],
            'source': paper['source'],
            'year': paper.get('year'),
            'pmid': paper.get('pmid'),
            'doi': paper.get('doi')
        }

        if USE_NETWORKX:
            self.graph.add_node(paper_id, **node_data)
        else:
            self.nodes[paper_id] = node_data

    def add_concept_node(self, concept_id: str):
        """개념 노드 추가 (concept_type 포함)"""
        if concept_id not in self.concepts:
            return

        concept = self.concepts[concept_id]
        # concept_type은 이미 concept dict에 포함되어 있음

        if USE_NETWORKX:
            if not self.graph.has_node(concept_id):
                self.graph.add_node(concept_id, **concept, node_type='concept')
        else:
            if concept_id not in self.nodes:
                self.nodes[concept_id] = {**concept, 'node_type': 'concept'}

    def add_edge(self, source_id: str, target_id: str, edge_type: str, **properties):
        """일반적인 엣지 추가 (모든 관계 타입 지원)"""
        edge_data = {
            'type': edge_type,
            **properties
        }

        if USE_NETWORKX:
            self.graph.add_edge(source_id, target_id, **edge_data)
        else:
            self.edges.append({
                'source': source_id,
                'target': target_id,
                **edge_data
            })
    
    def add_mentions_edge(self, paper_id: str, mention: Dict):
        """MENTIONS 관계 추가"""
        concept_id = mention['concept_id']
        self.add_edge(
            paper_id, 
            concept_id, 
            'MENTIONS',
            confidence=mention['confidence'],
            matched_term=mention['matched_term'],
            count=mention['count']
        )
    
    def add_correlates_with_edge(self, concept_id1: str, concept_id2: str, correlation: float, direction: str = "bidirectional"):
        """CORRELATES_WITH 관계 추가 (개념 간 상관관계)"""
        self.add_edge(
            concept_id1,
            concept_id2,
            'CORRELATES_WITH',
            correlation=correlation,
            direction=direction
        )
    
    def add_similar_to_edge(self, paper_id1: str, paper_id2: str, similarity_score: float, similarity_type: str = "content"):
        """SIMILAR_TO 관계 추가 (논문 간 유사도)"""
        self.add_edge(
            paper_id1,
            paper_id2,
            'SIMILAR_TO',
            similarity_score=similarity_score,
            similarity_type=similarity_type
        )
    
    def add_increases_edge(self, intervention_id: str, target_id: str, magnitude: float = 0.5, evidence_level: str = "moderate"):
        """INCREASES 관계 추가 (Intervention → Biomarker/Outcome)"""
        self.add_edge(
            intervention_id,
            target_id,
            'INCREASES',
            magnitude=magnitude,
            evidence_level=evidence_level
        )
    
    def add_supports_edge(self, intervention_id: str, target_id: str, evidence_level: str = "moderate"):
        """SUPPORTS 관계 추가 (Intervention → Biomarker/Outcome)"""
        self.add_edge(
            intervention_id,
            target_id,
            'SUPPORTS',
            evidence_level=evidence_level
        )
    
    def add_reduces_edge(self, intervention_id: str, target_id: str, magnitude: float = 0.5, evidence_level: str = "moderate"):
        """REDUCES 관계 추가 (Intervention → Biomarker/Outcome)"""
        self.add_edge(
            intervention_id,
            target_id,
            'REDUCES',
            magnitude=magnitude,
            evidence_level=evidence_level
        )
    
    def add_plan_node(self, plan_id: str, plan_type: str, target_concept: str, **plan_details):
        """운동 처방(Plan) 노드 추가"""
        node_data = {
            'node_type': 'plan',
            'id': plan_id,
            'plan_type': plan_type,
            'target_concept': target_concept,
            **plan_details
        }
        
        if USE_NETWORKX:
            self.graph.add_node(plan_id, **node_data)
        else:
            self.nodes[plan_id] = node_data

    def build_from_papers(self, papers: List[Dict]) -> Dict:
        """
        논문 리스트로부터 그래프 구축

        Returns:
            통계 정보
        """
        stats = {
            'total_papers': len(papers),
            'papers_with_concepts': 0,
            'total_concepts_found': 0,
            'total_mentions': 0,
            'concepts_by_domain': defaultdict(set),
            'english_papers': 0,
            'korean_papers': 0,
            'ko_summaries_generated': 0,
            'ko_embeddings_generated': 0,
            # 관계 타입별 통계
            'relationships': {
                'MENTIONS': 0,
                'CORRELATES_WITH': 0,
                'SIMILAR_TO': 0,
                'INCREASES': 0,
                'SUPPORTS': 0,
                'REDUCES': 0,
                'AFFECTS': 0,
                'REQUIRES': 0,
                'CONTRADICTS': 0
            },
            # Concept 타입별 통계
            'concept_types': {
                'Outcome': 0,
                'Intervention': 0,
                'Biomarker': 0,
                'Disease': 0,
                'Measurement': 0,
                'Unknown': 0
            }
        }

        print("\n🔨 그래프 구축 시작...")
        if self.generate_ko_summaries:
            print(f"   📝 영어 논문에 대해 한국어 요약 생성 활성화 (로컬 Ollama: {self.ollama_model})")
        if self.generate_ko_embeddings:
            if self.embedding_provider == "ollama":
                print(f"   🧮 한국어 임베딩 생성 활성화 (Ollama: {self.ollama_embedding_model})")
            else:
                print(f"   🧮 한국어 임베딩 생성 활성화 (OpenAI: text-embedding-3-small)")

        for i, paper in enumerate(papers):
            # PMID가 None이거나 없으면 DOI 또는 index 사용 (한국어 논문 대응)
            pmid = paper.get('pmid') or paper.get('doi') or f"idx_{i}"
            paper_id = f"paper_{pmid}"
            lang = paper['language']

            # 통계
            if lang == 'en':
                stats['english_papers'] += 1
            elif lang == 'ko':
                stats['korean_papers'] += 1

            # 논문 노드 추가 (한국어 요약 생성 포함)
            self.add_paper_node(paper, paper_id)

            # 한국어 요약 생성 여부 확인
            if USE_NETWORKX:
                node_data = self.graph.nodes[paper_id]
            else:
                node_data = self.nodes[paper_id]

            ko_summary = node_data.get('chunk_ko_summary')
            if ko_summary:
                stats['ko_summaries_generated'] += 1

            ko_embedding = node_data.get('embedding_ko')
            if ko_embedding:
                stats['ko_embeddings_generated'] += 1

            # 개념 추출 (한국어 요약 포함)
            mentioned = self.extract_mentioned_concepts(paper['abstract'], ko_summary)

            if mentioned:
                stats['papers_with_concepts'] += 1
                stats['total_mentions'] += len(mentioned)

            # 개념 노드 및 관계 추가
            mentioned_concept_ids = []
            for mention in mentioned:
                concept_id = mention['concept_id']
                mentioned_concept_ids.append(concept_id)

                # 개념 노드 추가
                self.add_concept_node(concept_id)
                
                # Concept 타입 통계
                concept_type = self.concepts[concept_id].get('concept_type', 'Unknown')
                stats['concept_types'][concept_type] = stats['concept_types'].get(concept_type, 0) + 1

                # MENTIONS 관계 추가
                self.add_mentions_edge(paper_id, mention)
                stats['relationships']['MENTIONS'] += 1

                # 통계
                stats['concepts_by_domain'][paper['domain']].add(concept_id)
            
            # CORRELATES_WITH 관계 추가 (같은 논문에 언급된 개념들 간)
            if len(mentioned_concept_ids) >= 2:
                for j in range(len(mentioned_concept_ids)):
                    for k in range(j + 1, len(mentioned_concept_ids)):
                        concept_id1 = mentioned_concept_ids[j]
                        concept_id2 = mentioned_concept_ids[k]
                        
                        # 상관관계 점수: 같은 논문에 함께 등장 = 0.7 (기본값)
                        correlation = 0.7
                        
                        # CORRELATES_WITH 관계 추가 (양방향)
                        self.add_correlates_with_edge(concept_id1, concept_id2, correlation)
                        stats['relationships']['CORRELATES_WITH'] += 1

            if (i + 1) % 100 == 0:
                current_total_rels = sum(stats['relationships'].values())
                print(f"  처리: {i + 1}/{len(papers)}개 (한국어 요약: {stats['ko_summaries_generated']}개, 관계: {current_total_rels}개)")

        # Concept 간 도메인 지식 기반 관계 추가
        print("\n🔗 Concept 간 관계 추가 중...")
        concept_relationships = self.schema.get('concept_relationships', {}).get('rules', [])
        
        for rule in concept_relationships:
            source_id = rule['source']
            target_id = rule['target']
            relation = rule['relation']
            
            # 두 concept가 모두 그래프에 존재하는지 확인
            if USE_NETWORKX:
                has_source = self.graph.has_node(source_id)
                has_target = self.graph.has_node(target_id)
            else:
                has_source = source_id in self.nodes
                has_target = target_id in self.nodes
            
            if has_source and has_target:
                if relation == 'INCREASES':
                    self.add_increases_edge(source_id, target_id)
                    stats['relationships']['INCREASES'] += 1
                elif relation == 'SUPPORTS':
                    self.add_supports_edge(source_id, target_id)
                    stats['relationships']['SUPPORTS'] += 1
                elif relation == 'REDUCES':
                    self.add_reduces_edge(source_id, target_id)
                    stats['relationships']['REDUCES'] += 1
        
        print(f"   ✅ Concept 관계 추가 완료: INCREASES({stats['relationships']['INCREASES']}), SUPPORTS({stats['relationships']['SUPPORTS']}), REDUCES({stats['relationships']['REDUCES']})")

        stats['unique_concepts'] = len(set().union(*stats['concepts_by_domain'].values()))
        
        # 전체 관계 수 계산
        stats['total_relationships'] = sum(stats['relationships'].values())

        print(f"\n✅ 그래프 구축 완료!")
        print(f"   📄 논문 노드: {stats['total_papers']}개")
        print(f"     • 영어: {stats['english_papers']}개")
        print(f"     • 한국어: {stats['korean_papers']}개")
        if self.generate_ko_summaries:
            print(f"     • 한국어 요약 생성: {stats['ko_summaries_generated']}개")
        if self.generate_ko_embeddings:
            print(f"     • 한국어 임베딩 생성: {stats['ko_embeddings_generated']}개")
        print(f"   🔗 개념 발견: {stats['unique_concepts']}개")
        
        # Concept 타입별 통계
        print(f"   📊 Concept 타입별:")
        for c_type, count in stats['concept_types'].items():
            if count > 0:
                print(f"     • {c_type}: {count}개")
        
        print(f"   🕸️  관계 (Relationships): {stats['total_relationships']}개")
        
        # 관계 타입별 상세 통계
        for rel_type, count in stats['relationships'].items():
            if count > 0:
                icon = "✅" if count > 0 else "⚪"
                print(f"     {icon} {rel_type}: {count}개")
        
        # 0개인 관계 타입 표시
        zero_rels = [rel_type for rel_type, count in stats['relationships'].items() if count == 0]
        if zero_rels:
            print(f"     ⚠️  미구현: {', '.join(zero_rels)}")

        return stats

    def export_to_json(self, output_path: str):
        """JSON으로 내보내기"""
        if USE_NETWORKX:
            from networkx.readwrite import json_graph
            data = json_graph.node_link_data(self.graph)
        else:
            data = {
                'nodes': list(self.nodes.values()),
                'edges': self.edges
            }
        
        # set을 list로 변환 (JSON serializable하게)
        def convert_sets(obj):
            """재귀적으로 set을 list로 변환"""
            if isinstance(obj, set):
                return list(obj)
            elif isinstance(obj, dict):
                return {k: convert_sets(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_sets(item) for item in obj]
            else:
                return obj
        
        data = convert_sets(data)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"💾 저장 완료: {output_path}")

    def export_to_neo4j_cypher(self, output_path: str):
        """Neo4j Cypher 스크립트로 내보내기"""
        cypher_lines = []

        # 개념 노드 생성 (concept_type 레이블 포함)
        cypher_lines.append("// Concept Nodes (by type)")
        
        # Concept을 타입별로 그룹화
        concepts_by_type = {}
        for concept_id, concept in self.concepts.items():
            c_type = concept.get('concept_type', 'Unknown')
            if c_type not in concepts_by_type:
                concepts_by_type[c_type] = []
            concepts_by_type[c_type].append((concept_id, concept))
        
        # 타입별로 노드 생성
        for c_type, concepts in concepts_by_type.items():
            cypher_lines.append(f"\n// {c_type} Concepts ({len(concepts)}개)")
            for concept_id, concept in concepts:
                props = {
                    'id': concept_id,
                    'name_ko': concept['name_ko'],
                    'name_en': concept['name_en'],
                    'importance': concept.get('importance', 0.5)
                }
                props_str = ', '.join([f"{k}: '{v}'" if isinstance(v, str) else f"{k}: {v}"
                                       for k, v in props.items()])
                # Concept와 구체적 타입 모두 레이블로 추가
                cypher_lines.append(f"CREATE (c{concept_id}:Concept:{c_type} {{{props_str}}});")

        cypher_lines.append("\n// Paper Nodes")
        if USE_NETWORKX:
            for node_id, node_data in self.graph.nodes(data=True):
                if node_data.get('node_type') == 'paper':
                    props_str = f"id: '{node_id}', title: '{node_data['title'][:100]}'"
                    cypher_lines.append(f"CREATE (p{node_id.replace('-', '_')}:Paper {{{props_str}}});")

            # 관계 타입별로 그룹화
            cypher_lines.append("\n// Relationships")
            
            relationships_by_type = {}
            for source, target, edge_data in self.graph.edges(data=True):
                rel_type = edge_data.get('type', 'UNKNOWN')
                if rel_type not in relationships_by_type:
                    relationships_by_type[rel_type] = []
                relationships_by_type[rel_type].append((source, target, edge_data))
            
            # 각 관계 타입별로 출력
            for rel_type, edges in relationships_by_type.items():
                cypher_lines.append(f"\n// {rel_type} Relationships ({len(edges)}개)")
                
                for source, target, edge_data in edges:
                    source_safe = source.replace('-', '_')
                    target_safe = target.replace('-', '_')
                    
                    # 관계별 속성 처리
                    props = {k: v for k, v in edge_data.items() if k != 'type'}
                    props_str = ', '.join([f"{k}: {v}" if isinstance(v, (int, float)) else f"{k}: '{v}'"
                                          for k, v in props.items()])
                    props_clause = f" {{{props_str}}}" if props_str else ""
                    
                    # 노드 타입 추론
                    if rel_type == 'MENTIONS':
                        cypher_lines.append(
                            f"MATCH (p:Paper {{id: '{source}'}}), (c:Concept {{id: '{target}'}}) "
                            f"CREATE (p)-[:{rel_type}{props_clause}]->(c);"
                        )
                    elif rel_type == 'CORRELATES_WITH':
                        cypher_lines.append(
                            f"MATCH (c1:Concept {{id: '{source}'}}), (c2:Concept {{id: '{target}'}}) "
                            f"CREATE (c1)-[:{rel_type}{props_clause}]->(c2);"
                        )
                    elif rel_type in ['INCREASES', 'SUPPORTS', 'REDUCES']:
                        cypher_lines.append(
                            f"MATCH (i:Intervention {{id: '{source}'}}), (t:Concept {{id: '{target}'}}) "
                            f"CREATE (i)-[:{rel_type}{props_clause}]->(t);"
                        )
                    elif rel_type == 'SIMILAR_TO':
                        cypher_lines.append(
                            f"MATCH (p1:Paper {{id: '{source}'}}), (p2:Paper {{id: '{target}'}}) "
                            f"CREATE (p1)-[:{rel_type}{props_clause}]->(p2);"
                        )
                    else:
                        # 기타 관계 타입
                        cypher_lines.append(
                            f"MATCH (n1 {{id: '{source}'}}), (n2 {{id: '{target}'}}) "
                            f"CREATE (n1)-[:{rel_type}{props_clause}]->(n2);"
                        )

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(cypher_lines))

        print(f"💾 Neo4j Cypher 저장: {output_path}")


def main():
    """메인 실행 함수"""
    import sys

    print("=" * 60)
    print("🕸️ Graph RAG 구축 파이프라인")
    print("=" * 60)

    # 옵션 파싱
    generate_ko_summary = '--ko-summary' in sys.argv
    generate_ko_embedding = '--ko-embedding' in sys.argv

    # 임베딩 제공자 선택 (기본: openai)
    embedding_provider = "openai"
    for arg in sys.argv:
        if arg.startswith('--embedding-provider='):
            embedding_provider = arg.split('=')[1]
    
    # Ollama 모델 지정
    ollama_model = "qwen3:14b"
    for arg in sys.argv:
        if arg.startswith('--ollama-model='):
            ollama_model = arg.split('=')[1]
    
    # Ollama 임베딩 모델 지정 (기본: bge-m3:latest)
    ollama_embedding_model = "bge-m3:latest"
    for arg in sys.argv:
        if arg.startswith('--ollama-embedding-model='):
            ollama_embedding_model = arg.split('=')[1]
    
    # 논문 개수 제한 (테스트용)
    limit = None
    for arg in sys.argv:
        if arg.startswith('--limit='):
            try:
                limit = int(arg.split('=')[1])
                print(f"📊 테스트 모드: 처음 {limit}개 논문만 처리합니다.")
            except ValueError:
                print(f"⚠️ --limit 값이 유효하지 않습니다. 전체 논문을 처리합니다.")

    # 1. 빌더 초기화
    builder = GraphRAGBuilder(
        schema_path="graph_rag_schema.json",
        generate_ko_summaries=generate_ko_summary,
        generate_ko_embeddings=generate_ko_embedding,
        embedding_provider=embedding_provider,
        ollama_model=ollama_model,
        ollama_embedding_model=ollama_embedding_model
    )

    # 2. 논문 로드
    output_dir = Path("outputs")
    corpus_files = list(output_dir.glob("ragdb_final_corpus_*.json"))

    if not corpus_files:
        print("❌ 논문 코퍼스 파일이 없습니다.")
        print("   먼저 merge_korean_corpus.py를 실행하세요.")
        return

    latest_corpus = sorted(corpus_files)[-1]
    papers = builder.load_papers(str(latest_corpus))
    
    # 논문 개수 제한 적용
    if limit and limit > 0:
        papers = papers[:limit]
        print(f"✂️ 제한 적용: {len(papers)}개 논문 선택")

    # 3. 그래프 구축
    stats = builder.build_from_papers(papers)

    # 4. 내보내기
    # 현재 시간으로 고유한 타임스탬프 생성
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 논문 개수도 파일명에 포함
    paper_count = len(papers)
    
    # JSON 형식
    json_output = output_dir / f"graph_rag_{paper_count}papers_{timestamp}.json"
    builder.export_to_json(str(json_output))

    # Neo4j Cypher 스크립트
    cypher_output = output_dir / f"graph_rag_neo4j_{paper_count}papers_{timestamp}.cypher"
    builder.export_to_neo4j_cypher(str(cypher_output))

    # 5. 통계 저장
    stats_output = output_dir / f"graph_rag_stats_{paper_count}papers_{timestamp}.json"
    with open(stats_output, 'w', encoding='utf-8') as f:
        # defaultdict를 일반 dict로 변환
        stats['concepts_by_domain'] = {
            domain: list(concepts)
            for domain, concepts in stats['concepts_by_domain'].items()
        }
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(f"📊 통계 저장: {stats_output}")

    print("\n" + "=" * 60)
    print("✅ Graph RAG 구축 완료!")
    print("=" * 60)
    print(f"\n다음 단계:")
    print(f"1. JSON 사용: {json_output}")
    print(f"2. Neo4j 사용: {cypher_output} 파일을 Neo4j에 임포트")
    print(f"\n💡 사용 가능한 옵션:")
    print(f"   --ko-summary                      한국어 요약 생성 (로컬 Ollama)")
    print(f"   --ko-embedding                    한국어 임베딩 생성")
    print(f"   --embedding-provider=PROVIDER     임베딩 제공자 (기본: openai, 옵션: ollama)")
    print(f"   --ollama-model=MODEL              Ollama 요약 모델 지정 (기본: qwen3:14b)")
    print(f"   --ollama-embedding-model=MODEL    Ollama 임베딩 모델 (기본: bge-m3:latest)")
    print(f"   --limit=N                         처리할 논문 개수 제한 (테스트용)")
    print(f"\n   예시:")
    print(f"   # 테스트: 50개만 빠르게 (임베딩 없음)")
    print(f"   python build_graph_rag.py --limit=50")
    print(f"")
    print(f"   # 테스트: 50개 + Ollama 임베딩")
    print(f"   python build_graph_rag.py --ko-embedding --embedding-provider=ollama --limit=50")
    print(f"")
    print(f"   # OpenAI 임베딩 (전체)")
    print(f"   python build_graph_rag.py --ko-summary --ko-embedding")
    print(f"")
    print(f"   # Ollama bge-m3:latest 임베딩 (전체, 로컬)")
    print(f"   python build_graph_rag.py --ko-summary --ko-embedding --embedding-provider=ollama")
    print(f"")
    print(f"   # 다른 Ollama 임베딩 모델")
    print(f"   python build_graph_rag.py --ko-embedding --embedding-provider=ollama --ollama-embedding-model=nomic-embed-text")


if __name__ == "__main__":
    main()
