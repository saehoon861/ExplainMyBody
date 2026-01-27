# 결과를 즉시 확인하기 위한 코드
# 임의로 분석한 결과를 출력하는 테스트 코드
# 실제 프로젝트에서는 사용되지 않을 예정



# ============================================================================
# 결과 출력 유틸리티
# ============================================================================

class ResultPrinter:
    """분석 결과 출력"""
    
    @staticmethod
    def print_analysis_result(result):
        """분석 결과를 포맷팅하여 출력"""
        print("\n" + "=" * 60)
        print("체성분 분석 결과")
        print("=" * 60)
        
        print(f"2차 체형 (근육 보정): {result.get('stage2', 'N/A')}")
        print(f"최종 체형: {result.get('stage3', 'N/A')}")
        
        print("\n" + "=" * 60 + "\n")

        print("return 타입: ",type(result))
        print("return 값: ",result)
