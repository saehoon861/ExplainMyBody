"""
한국어 요약 생성 테스트 스크립트

Ollama 서버가 실행 중이고 요약 모델(llama3.2, gemma2 등)이 설치되어 있는지 확인합니다.
"""

import ollama
import sys


def test_ollama_connection():
    """Ollama 서버 연결 테스트"""
    print("🔍 Ollama 서버 연결 테스트...")

    try:
        models = ollama.list()
        print("✅ Ollama 서버 연결 성공!")
        print(f"   설치된 모델: {len(models.get('models', []))}개")
        return True
    except Exception as e:
        print(f"❌ Ollama 서버 연결 실패: {e}")
        print("\n해결 방법:")
        print("1. Ollama 설치: curl -fsSL https://ollama.ai/install.sh | sh")
        print("2. Ollama 서버 실행: ollama serve")
        return False


def test_model_available(model_name: str = "llama3.2"):
    """모델 설치 여부 확인"""
    print(f"\n🔍 모델 '{model_name}' 설치 확인...")

    try:
        models = ollama.list()
        model_list = [m['name'] for m in models.get('models', [])]

        # 모델이 설치되어 있는지 확인 (llama3.2:latest 형태일 수 있음)
        is_installed = any(model_name in m for m in model_list)

        if is_installed:
            print(f"✅ 모델 '{model_name}' 설치됨")
            return True
        else:
            print(f"⚠️ 모델 '{model_name}' 미설치")
            print(f"\n설치 방법:")
            print(f"   ollama pull {model_name}")
            print(f"\n설치된 모델 목록:")
            for m in model_list:
                print(f"   - {m}")
            return False

    except Exception as e:
        print(f"❌ 모델 확인 실패: {e}")
        return False


def test_summary_generation(model_name: str = "llama3.2"):
    """한국어 요약 생성 테스트"""
    print(f"\n🔍 한국어 요약 생성 테스트 ({model_name})...")

    test_abstracts = [
        "Resistance training combined with adequate protein intake (1.6g/kg/day) significantly increases skeletal muscle mass and strength in healthy adults. A 12-week intervention study showed 2.3kg muscle mass gain compared to control group.",
        "Body composition analysis using bioelectrical impedance analysis (BIA) provides accurate assessment of visceral fat levels. InBody measurements correlate strongly with DEXA scan results.",
        "Traditional Korean fermented foods such as kimchi contain beneficial probiotics that improve gut health and metabolic function."
    ]

    try:
        for i, abstract in enumerate(test_abstracts, 1):
            print(f"\n테스트 {i}: {abstract[:50]}...")

            response = ollama.chat(
                model=model_name,
                messages=[
                    {
                        "role": "user",
                        "content": f"""다음 영어 논문 초록을 2-3문장의 한국어로 요약하세요:

{abstract}

한국어 요약:"""
                    }
                ],
                options={
                    "temperature": 0.3,
                    "num_predict": 300
                }
            )

            summary = response['message']['content'].strip()
            print(f"   ✅ 요약 생성 성공!")
            print(f"   - 길이: {len(summary)}자")
            print(f"   - 요약: {summary}")

        print(f"\n✅ 모든 테스트 통과!")
        return True

    except Exception as e:
        print(f"❌ 요약 생성 실패: {e}")
        return False


def main():
    """메인 함수"""
    print("=" * 60)
    print("🧪 Ollama 한국어 요약 생성 테스트")
    print("=" * 60)

    # 모델 이름 파라미터
    model_name = sys.argv[1] if len(sys.argv) > 1 else "llama3.2"
    print(f"\n테스트 모델: {model_name}")

    # 1. Ollama 서버 연결 테스트
    if not test_ollama_connection():
        return

    # 2. 모델 설치 확인
    if not test_model_available(model_name):
        return

    # 3. 요약 생성 테스트
    if not test_summary_generation(model_name):
        return

    print("\n" + "=" * 60)
    print("✅ 모든 테스트 성공!")
    print("=" * 60)
    print("\n다음 단계:")
    print("   python build_graph_rag.py --ko-summary --ko-embedding")
    print(f"   python build_graph_rag.py --ko-summary --ko-embedding --ollama-model={model_name}")


if __name__ == "__main__":
    try:
        import ollama
    except ImportError:
        print("❌ ollama 패키지가 설치되지 않았습니다.")
        print("\n설치 방법:")
        print("   pip install ollama")
        sys.exit(1)

    main()
