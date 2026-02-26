from body_analysis.pipeline import BodyCompositionAnalyzer
import utils_test

def get_test_input_from_inbody():
    return {
        "sex": "남성",
        "age": 25,
        "height_cm": 175,
        "weight_kg": 70,
        "bmi": 23.1,
        "fat_rate": 15.2,
        "smm": 25.4,
        "muscle_seg": {
            "왼팔": 2.1,
            "오른팔": 2.2,
            "몸통": 10.3,
            "왼다리": 12.4,
            "오른다리": 12.5
            },
        "fat_seg": {
            "왼팔": 1.1,
            "오른팔": 1.2,
            "몸통": 4.3,
            "왼다리": 6.4,
            "오른다리": 6.5
            }
        }



def main():
    """
    메인 실행 함수
    """
    print("시스템: 체성분 분석 프로그램을 시작합니다.")
    

    # 1. 데이터 생성 (Factory 패턴)
    user = get_test_input_from_inbody()

    # 2. 분석기 초기화 및 실행 (Facade 패턴)
    analyzer = BodyCompositionAnalyzer(margin=0.10)
    
    print("\n> 데이터 분석 중...")
    # 전체 파이프라인 실행 (Stage 1 + 2 + 3)
    analysis_result = analyzer.analyze_full_pipeline(user)

    # 4. 결과 출력
    utils_test.ResultPrinter.print_analysis_result(analysis_result)

if __name__ == "__main__":
    main()