"""
샘플 InBody 데이터를 Pydantic 스키마에 맞게 변환

Flat 구조 → Nested 구조 변환
"""

import json
from pathlib import Path

def convert_flat_to_nested(flat_data: dict) -> dict:
    """Flat 구조를 Nested 구조로 변환"""

    # 성별 정규화: 남자/여자 → 남성/여성
    gender = flat_data.get("성별")
    if gender == "남자":
        gender = "남성"
    elif gender == "여자":
        gender = "여성"

    return {
        "기본정보": {
            "신장": flat_data.get("신장"),
            "연령": flat_data.get("나이"),
            "성별": gender
        },
        "체성분": {
            "체수분": flat_data.get("체수분"),
            "단백질": flat_data.get("단백질"),
            "무기질": flat_data.get("무기질"),
            "체지방": flat_data.get("체지방")
        },
        "체중관리": {
            "체중": flat_data.get("체중"),
            "골격근량": flat_data.get("골격근량"),
            "체지방량": flat_data.get("체지방량") or flat_data.get("체지방"),
            "적정체중": flat_data.get("적정체중"),
            "체중조절": flat_data.get("체중조절"),
            "지방조절": flat_data.get("지방조절"),
            "근육조절": flat_data.get("근육조절")
        },
        "비만분석": {
            "BMI": flat_data.get("BMI"),
            "체지방률": flat_data.get("체지방률"),
            "복부지방률": flat_data.get("복부지방률"),
            "내장지방레벨": flat_data.get("내장지방레벨"),
            "비만도": flat_data.get("비만도")
        },
        "연구항목": {
            "제지방량": flat_data.get("제지방량"),
            "기초대사량": flat_data.get("기초대사량"),
            "권장섭취열량": flat_data.get("권장섭취열량")
        },
        "부위별근육분석": {
            "왼쪽팔": flat_data.get("근육_부위별등급", {}).get("왼팔"),
            "오른쪽팔": flat_data.get("근육_부위별등급", {}).get("오른팔"),
            "복부": flat_data.get("근육_부위별등급", {}).get("몸통"),
            "왼쪽하체": flat_data.get("근육_부위별등급", {}).get("왼다리"),
            "오른쪽하체": flat_data.get("근육_부위별등급", {}).get("오른다리")
        },
        "부위별체지방분석": {
            "왼쪽팔": flat_data.get("체지방_부위별등급", {}).get("왼팔"),
            "오른쪽팔": flat_data.get("체지방_부위별등급", {}).get("오른팔"),
            "복부": flat_data.get("체지방_부위별등급", {}).get("몸통"),
            "왼쪽하체": flat_data.get("체지방_부위별등급", {}).get("왼다리"),
            "오른쪽하체": flat_data.get("체지방_부위별등급", {}).get("오른다리")
        },
        "body_type1": flat_data.get("body_type1"),
        "body_type2": flat_data.get("body_type2")
    }


def main():
    """모든 샘플 파일 변환"""

    pipeline_dir = Path(__file__).parent

    # 변환할 파일 목록
    sample_files = [
        "sample_inbody_gymnast.json",
        "sample_inbody_obese.json",
        "sample_inbody_skinnyfat.json",
        "sample_inbody_juggernaut.json",
        "sample_inbody_strongman.json",
        "sample_inbody_teentank.json",
        "sample_inbody_underweight.json",
        "sample_inbody_underweight2.json",
    ]

    for filename in sample_files:
        filepath = pipeline_dir / filename

        if not filepath.exists():
            print(f"⚠️  파일 없음: {filename}")
            continue

        try:
            # 파일 읽기
            with open(filepath, 'r', encoding='utf-8') as f:
                flat_data = json.load(f)

            # 이미 nested 구조인지 확인 후 성별 값 체크
            if "기본정보" in flat_data:
                # 성별이 "남자" 또는 "여자"인 경우 재변환 필요
                gender = flat_data.get("기본정보", {}).get("성별")
                if gender not in ["남자", "여자"]:
                    print(f"✅ {filename} - 이미 변환됨")
                    continue
                print(f"🔄 {filename} - 성별 값 수정 필요")

            # 변환
            nested_data = convert_flat_to_nested(flat_data)

            # 저장
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(nested_data, f, ensure_ascii=False, indent=2)

            print(f"✅ {filename} - 변환 완료")

        except Exception as e:
            print(f"❌ {filename} - 변환 실패: {e}")

    print("\n완료!")


if __name__ == "__main__":
    main()
