# stage1 + stage2 통합함수
# 역할
# - 키 체중 --> BMI계산
# -BMI+체지방률 -->stage1체형
# -SMM/체중 -->근육레벨로 보정 -->Stage2최종 체형

#기준 분류함수들
def classify_bmi(bmi):

    if bmi < 18.5 :
        category = "저체중"
    elif bmi < 23.0 and bmi > 18.5:
        category = "정상"
    elif bmi < 24.9 and bmi > 23.0:
        category = "과체중"
    elif bmi < 29.9 and bmi > 25.0:
        category = "비만1단계"
    elif bmi < 29.9 and bmi > 34.9:
        category = '비만2단계'
    else:
        category = "고도비만"

    return round(bmi, 1), category


def classify_body_fat_rate(fat_rate):
    if fat_rate < 10:
        return "표준미만"
    elif fat_rate < 20 and fat_rate > 10:
        return "표준"
    elif fat_rate < 24 and fat_rate > 21:
        return "과체중"
    else:
        return "비만"
    

def classify_muscle_level(smm, weight):
    ratio = smm / weight

    if ratio >= 0.55:
        level = "근육 매우 많음"
    elif ratio >= 0.50:
        level = "근육 많음"
    elif ratio >= 0.45:
        level = "근육 충분"
    elif ratio >= 0.40:
        level = "근육 보통"
    else:
        level = "근육 적음"

    return round(ratio, 3), level


#stage1 판단
def stage1_body_type(bmi_cat, fat_cat, smm_cat=None):
    if bmi_cat == "정상":
        return "표준형" if fat_cat == "표준" else "마른형" if fat_cat == "표준이하" else "마른비만형"

    if bmi_cat == "저체중":
        return "마른비만형" if fat_cat in ["과체중", "비만"] else "마른형"

    if bmi_cat == "과체중":
        return "비만형" if fat_cat in ["과체중", "비만"] else "근육형"

    
    if bmi_cat == "비만1단계":
        if fat_cat == "표준이하" and smm_cat in ["근육 매우 많음", "근육 많음", "근육 충분"]:
            return "근육형"
        return "비만형"
    
    if bmi_cat == "비만2단계":
        if fat_cat == "표준이하" and smm_cat in ["근육 매우 많음", "근육 많음"]:
            return "근육형"
        return "비만형"

    if bmi_cat == "고도비만":
        if fat_cat == "표준이하" and smm_cat in ["근육 매우 많음", "근육 많음"]:
            return "근육형"
        return "고도비만형"


#Stage2 근육보정
def stage2_adjust(stage1_type, muscle_level):
    table = {
        "마른형": {
            "근육 적음": "마른형",
            "근육 보통": "마른형",
            "근육 충분": "마른근육형",
            "근육 많음": "근육형",
            "근육 매우 많음": "근육형",
        },
        "표준형": {
            "근육 적음": "마른형",
            "근육 보통": "표준형",
            "근육 충분": "근육형",
            "근육 많음": "근육형",
            "근육 매우 많음": "근육형",
        },
        "근육형": {
            "근육 적음": "비만형",
            "근육 보통": "비만형",
            "근육 충분": "근육형",
            "근육 많음": "고근육체형",
            "근육 매우 많음": "고근육체형",
        },
        "비만형": {
            "근육 적음": "비만형",
            "근육 보통": "비만형",
            "근육 충분": "고근육체형",
            "근육 많음": "고근육체형",
            "근육 매우 많음": "고근육체형",
        },
        "고도비만형": {
            "근육 적음": "고도비만형",
            "근육 보통": "고도비만형",
            "근육 충분": "비만형",
            "근육 많음": "고근육체형",
            "근육 매우 많음": "고근육체형",
        },
        "마른비만형": {
            "근육 적음": "마른비만형",
            "근육 보통": "마른비만형",
            "근육 충분": "표준형",
            "근육 많음": "근육형",
            "근육 매우 많음": "고근육체형",
        }
    }
    return table.get(stage1_type, {}).get(muscle_level, stage1_type)


#Stage1 + Stage2 통합 함수
def analyze_stage1_2(bmi, weight_kg, fat_rate, smm, smm_cat):
    bmi, bmi_cat = classify_bmi(bmi)
    fat_cat = classify_body_fat_rate(fat_rate)

    stage1 = stage1_body_type(bmi_cat, fat_cat, smm_cat)

    smm_ratio, muscle_level = classify_muscle_level(smm, weight_kg)
    stage2 = stage2_adjust(stage1, muscle_level)

    return {
        "bmi": bmi,
        "bmi_category": bmi_cat,
        "fat_category": fat_cat,
        "smm_ratio": smm_ratio,
        "muscle_level": muscle_level,
        "stage1_type": stage1,
        "stage2_type": stage2
    }


def classify_part_level(value, ref, margin=0.10):
    """
    value : 부위 발달도 (부위 근육량 / 총 SMM)
    ref   : 기준 발달도
    margin: 허용 오차 비율 (기본 10%)
    """
    if value >= ref * (1 + margin):
        return "표준이상"
    elif value <= ref * (1 - margin):
        return "표준미만"
    else:
        return "표준"


def classify_body_parts(parts, total_smm, margin=0.10):
    """
    parts = {
        "left_arm":  수치,
        "right_arm": 수치,
        "trunk":     수치,
        "left_leg":  수치,
        "right_leg": 수치
    }
    total_smm: 총 골격근량
    """

    # 1️.부위 발달도 계산
    dev = {k: v / total_smm for k, v in parts.items()} #총 골격근량 중에서 부위마다 차지 하는 비율을 계산

    # 2️.기준 발달도 계산
    arm_ref = (dev["왼팔"] + dev["오른팔"]) / 2
    leg_ref = (dev["왼다리"] + dev["오른다리"]) / 2
    trunk_ref = (arm_ref + leg_ref) / 2   # 몸통 기준 (중간축)

    # 3️.부위별 표준화 결과
    part_level = {
        "왼팔": classify_part_level(dev["왼팔"], arm_ref, margin),
        "오른팔": classify_part_level(dev["오른팔"], arm_ref, margin),
        "몸통": classify_part_level(dev["몸통"], trunk_ref, margin),
        "왼다리": classify_part_level(dev["왼다리"], leg_ref, margin),
        "오른다리": classify_part_level(dev["오른다리"], leg_ref, margin),
    }

    return part_level


#부위별 체지방분석
def classify_body_fat_parts(fat_parts, total_fat, margin=0.10):
    """
    fat_parts = {
        "left_arm":  수치,
        "right_arm": 수치,
        "trunk":     수치,
        "left_leg":  수치,
        "right_leg": 수치
    }
    total_fat: 총 체지방량 (BFM)
    """

    # 1️.부위 체지방 발달도 계산
    dev = {k: v / total_fat for k, v in fat_parts.items()}

    # 2️.기준 발달도 계산
    arm_ref = (dev["왼팔"] + dev["오른팔"]) / 2
    leg_ref = (dev["왼다리"] + dev["오른다리"]) / 2

    # 체지방에서 몸통은 '자기 자신 기준' (보수적)
    trunk_ref = dev["몸통"]

    # 3️.부위별 표준화 결과
    fat_level = {
        "왼팔": classify_part_level(dev["왼팔"], arm_ref, margin),
        "오른팔": classify_part_level(dev["오른팔"], arm_ref, margin),
        "몸통": classify_part_level(dev["몸통"], trunk_ref, margin),
        "왼다리": classify_part_level(dev["왼다리"], leg_ref, margin),
        "오른다리": classify_part_level(dev["오른다리"], leg_ref, margin),
    }

    return fat_level

def is_numeric_seg(seg):
    """
    seg 딕셔너리의 값이 숫자인지 여부 판단
    """
    return all(isinstance(v, (int, float)) for v in seg.values())


def normalize_muscle_seg(muscle_input, total_smm, margin=0.10):
    """
    muscle_input:
      - 텍스트 seg → 그대로 반환
      - 수치 seg → classify_body_parts를 통해 표준화
    """

    # 이미 텍스트인 경우
    if not is_numeric_seg(muscle_input):
        return muscle_input

    # 수치인 경우 → 표준화
    return classify_body_parts(
        parts=muscle_input,
        total_smm=total_smm,
        margin=margin
    )

def normalize_fat_seg(fat_input, total_fat, margin=0.10):
    """
    fat_input:
      - 텍스트 seg → 그대로 반환
      - 수치 seg → classify_body_fat_parts를 통해 표준화
    """

    # 이미 텍스트인 경우
    if not is_numeric_seg(fat_input):
        return fat_input

    # 수치인 경우 → 표준화
    return classify_body_fat_parts(
        fat_parts=fat_input,
        total_fat=total_fat,
        margin=margin
    )


# 2.Stage3까지 포함한 전체 파이프라인
# stage3 분포 판정
HIGH = "표준이상"

def get_distribution(seg):
    arm_high = sum([seg["오른팔"] == HIGH, seg["왼팔"] == HIGH])
    leg_high = sum([seg["오른다리"] == HIGH, seg["왼다리"] == HIGH])

    if leg_high >= 2 and arm_high < 2:
        return "하체"
    elif arm_high >= 2 and leg_high < 2:
        return "상체"
    else:
        return "균형"
    
    
def stage3_classification(muscle_seg, fat_seg=None):
    muscle_dist = get_distribution(muscle_seg)

    if fat_seg is None:
        return "하체발달형" if muscle_dist == "하체" else "상체발달형" if muscle_dist == "상체" else "표준형"

    fat_dist = get_distribution(fat_seg)

    if fat_dist == "하체":
        return "하체비만형"
    elif fat_dist == "상체":
        return "상체비만형"
    else:
        return "하체발달형" if muscle_dist == "하체" else "상체발달형" if muscle_dist == "상체" else "표준형"

#전체 파이프라인 (최종)
def full_body_analysis_from_inbody(
    bmi, weight_kg, fat_rate,
    smm, smm_cat,
    muscle_input, fat_input=None,
    sex="남자", age=None,
    margin=0.10
):
    # Stage1 + Stage2
    stage12 = analyze_stage1_2(
        bmi=bmi,
        weight_kg=weight_kg,
        fat_rate=fat_rate,
        smm=smm,
        smm_cat=smm_cat
    )

    # 🔹 근육 seg 정규화
    muscle_seg = normalize_muscle_seg(
        muscle_input,
        total_smm=smm,
        margin=margin
    )

    # 🔹 체지방 seg 정규화
    fat_seg = None
    if fat_input is not None:
        total_fat = weight_kg * fat_rate / 100
        fat_seg = normalize_fat_seg(
            fat_input,
            total_fat=total_fat,
            margin=margin
        )

    # Stage3
    stage3 = stage3_classification(muscle_seg, fat_seg)

    return {
        "basic_info": {
            "sex": sex,
            "age": age,
            "weight_kg": weight_kg
        },
        "stage1_2": stage12,
        "muscle_seg": muscle_seg,
        "fat_seg": fat_seg,
        "stage3": stage3
    }

    
def get_user_input_from_inbody():
    print("\n[기본 정보 입력 – 인바디 기록지 기준]")
    
    sex = "남자"   #고정
    age = int(input("나이: "))
    height_cm = float(input("키(cm): "))
    weight_kg = float(input("체중(kg): "))

    bmi = float(input("BMI 지수 (인바디): "))
    fat_rate = float(input("체지방률(%): "))
    smm = float(input("골격근량 SMM(kg): "))

    print("\n[부위별 근육량 입력 (kg)]")
    muslce_mode = input("입력 방식 선택 (1: 수치, 2: 텍스트): ").strip()

    if muslce_mode == "1":
        muscle_input = {
            "왼팔": float(input("왼팔: ")),
            "오른팔": float(input("오른팔: ")),
            "몸통": float(input("몸통: ")),
            "왼다리": float(input("왼다리: ")),
            "오른다리": float(input("오른다리: "))
            }

    elif muslce_mode == "2":
        muscle_input = {
            "왼팔": input("왼팔: ").strip(),
            "오른팔": input("오른팔: ").strip(),
            "몸통": input("몸통: ").strip(),
            "왼다리": input("왼다리: ").strip(),
            "오른다리": input("오른다리: ").strip()
            }

    else:
        raise ValueError("잘못된 입력 방식입니다.")

    print("\n[부위별 체지방량 입력 (kg)]")
    fat_mode = input("입력 방식 선택 (1: 수치, 2: 텍스트, 3: no): ").strip()
    
    if fat_mode == "1":
        fat_input = {

            "왼팔": float(input("왼팔: ")),
            "오른팔": float(input("오른팔: ")),
            "몸통": float(input("몸통: ")),
            "왼다리": float(input("왼다리: ")),
            "오른다리": float(input("오른다리: "))
            }
    
    elif fat_mode == "2":
        fat_input = {
            "왼팔": input("왼팔: ").strip(),
            "오른팔": input("오른팔: ").strip(),
            "몸통": input("몸통: ").strip(),
            "왼다리": input("왼다리: ").strip(),
            "오른다리": input("오른다리: ").strip()
            }
        
    elif fat_mode == "3":
        fat_input = {
            "왼팔": None,
            "오른팔": None,
            "몸통": None,
            "왼다리": None,
            "오른다리": None
            }
    else:
        raise ValueError("잘못된 입력 방식입니다.")
        
    return {
        "sex": sex,
        "age": age,
        "height_cm": height_cm,
        "weight_kg": weight_kg,
        "bmi": bmi,
        "fat_rate": fat_rate,
        "smm": smm,
        "muscle_seg": muscle_input,
        "fat_seg": fat_input
    }

# 1.사용자 입력
user = get_user_input_from_inbody()

# 2️.전체 분석 실행
result = full_body_analysis_from_inbody(
    bmi=user["bmi"],
    weight_kg=user["weight_kg"],
    fat_rate=user["fat_rate"],
    smm=user["smm"],
    smm_cat=None,                      # 필요 시 자동 계산 가능
    muscle_input=user["muscle_seg"],
    fat_input=user["fat_seg"],
    sex=user["sex"],
    age=user["age"]
)

# 3️.결과 출력
print("\n[최종 체형 분석 결과]")
for k, v in result.items():
    print(f"{k}: {v}")




