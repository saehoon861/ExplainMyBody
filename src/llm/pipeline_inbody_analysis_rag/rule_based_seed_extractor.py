"""
Rule-based Seed Concept Extractor
- LLM 없이 하드코딩된 룰로 InBody measurements에서 Seed 추출
- Deterministic: 동일 입력 → 동일 출력
- Call1에서 사용: 체형 판정 + seed tag 포함
"""

from typing import List, Tuple, Dict
from shared.models import InBodyMeasurements
from .seed_concept_definitions import SEED_CONCEPTS, format_seed_tag, get_seed_name_ko


class RuleBasedSeedExtractor:
    """
    Rule-based Seed Concept Extractor

    InBody measurements → Seed concepts (deterministic)
    """

    def __init__(self):
        """초기화"""
        self.seed_concepts = SEED_CONCEPTS

    def extract_seeds(
        self,
        measurements: InBodyMeasurements
    ) -> List[str]:
        """
        InBody measurements에서 Seed concepts 추출

        Args:
            measurements: InBody 측정 데이터

        Returns:
            추출된 seed_id 리스트

        Example:
            ["skeletal_muscle_low", "visceral_fat_high", "bmi_overweight"]
        """
        extracted_seeds = []

        for seed_id, seed_info in self.seed_concepts.items():
            extraction_rule = seed_info.get("extraction_rule")
            if not extraction_rule:
                continue

            # Rule 실행
            try:
                condition = extraction_rule["condition"]
                if condition(measurements):
                    extracted_seeds.append(seed_id)
            except Exception as e:
                # 필드가 없거나 에러 발생 시 스킵
                continue

        return extracted_seeds

    def extract_with_descriptions(
        self,
        measurements: InBodyMeasurements
    ) -> List[Tuple[str, str, str]]:
        """
        Seed 추출 + 설명 포함

        Returns:
            [(seed_id, name_ko, description), ...]

        Example:
            [
                ("skeletal_muscle_low", "골격근량 부족", "골격근량이 표준 범위 이하"),
                ("visceral_fat_high", "내장지방 과다", "내장지방 레벨이 위험 수준")
            ]
        """
        seeds = self.extract_seeds(measurements)

        return [
            (
                seed_id,
                self.seed_concepts[seed_id]["name_ko"],
                self.seed_concepts[seed_id]["description"]
            )
            for seed_id in seeds
        ]

    def generate_assessment_with_seeds(
        self,
        measurements: InBodyMeasurements
    ) -> str:
        """
        체형 판정 자연어 생성 + seed tag 포함

        Call1 대체용: LLM 없이 rule 기반 판정

        Returns:
            체형 판정 텍스트 (seed tag 포함)

        Example:
            ```
            [체형 판정 결과]

            - 체형 유형: 근육 부족형 + 내장지방 과다

            - 근육 상태: 부족 (seed: skeletal_muscle_low)

            - 지방 상태: 과다 (seed: body_fat_high)

            - 내장지방 위험도: 주의 (seed: visceral_fat_high)

            - 부위별 불균형:
              상체 근육 발달이 상대적으로 부족한 경향이 있습니다.

            - key_risks (성별/연령 기반 건강 위험 가능성):
              - 내장지방 과다 (seed: visceral_fat_high)
              - 근육량 부족 (seed: skeletal_muscle_low)

            - priority_focus (우선 개선 방향):
              근육량 보완과 내장지방 관리가 가장 우선적인 과제로 보입니다.
            ```
        """
        seeds = self.extract_with_descriptions(measurements)

        # 체형 유형 판정
        body_type = self._determine_body_type(measurements, seeds)

        # 근육 상태
        muscle_status, muscle_seed = self._assess_muscle(measurements, seeds)

        # 지방 상태
        fat_status, fat_seed = self._assess_fat(measurements, seeds)

        # 내장지방 위험도
        visceral_status, visceral_seed = self._assess_visceral_fat(measurements, seeds)

        # 부위별 불균형
        imbalance_text = self._assess_imbalance(measurements)

        # key_risks
        key_risks = self._generate_key_risks(measurements, seeds)

        # priority_focus
        priority_focus = self._generate_priority_focus(measurements, seeds)

        # 최종 텍스트 조합
        assessment_parts = []

        assessment_parts.append("[체형 판정 결과]\n")
        assessment_parts.append(f"- 체형 유형: {body_type}\n")
        assessment_parts.append(f"\n- 근육 상태: {muscle_status} {format_seed_tag('', muscle_seed) if muscle_seed else ''}")
        assessment_parts.append(f"\n- 지방 상태: {fat_status} {format_seed_tag('', fat_seed) if fat_seed else ''}")
        assessment_parts.append(f"\n- 내장지방 위험도: {visceral_status} {format_seed_tag('', visceral_seed) if visceral_seed else ''}")
        assessment_parts.append(f"\n- 부위별 불균형:\n  {imbalance_text}")
        assessment_parts.append(f"\n- key_risks (성별/연령 기반 건강 위험 가능성):")
        for risk in key_risks:
            assessment_parts.append(f"\n  - {risk}")
        assessment_parts.append(f"\n- priority_focus (우선 개선 방향):\n  {priority_focus}")

        return "".join(assessment_parts)

    def _determine_body_type(
        self,
        measurements: InBodyMeasurements,
        seeds: List[Tuple[str, str, str]]
    ) -> str:
        """체형 유형 판정"""
        seed_ids = [s[0] for s in seeds]

        if "body_type_sarcopenic_obesity" in seed_ids:
            return "근감소성 비만형"
        elif "body_type_skinny_fat" in seed_ids:
            return "마른 비만형"
        elif "skeletal_muscle_low" in seed_ids and "body_fat_high" in seed_ids:
            return "근육 부족형 + 체지방 과다"
        elif "skeletal_muscle_low" in seed_ids:
            return "근육 부족형"
        elif "body_fat_high" in seed_ids or "visceral_fat_high" in seed_ids:
            return "비만형"
        elif "bmi_overweight" in seed_ids:
            return "과체중형"
        elif "bmi_underweight" in seed_ids:
            return "저체중형"
        else:
            return "표준 체형"

    def _assess_muscle(
        self,
        measurements: InBodyMeasurements,
        seeds: List[Tuple[str, str, str]]
    ) -> Tuple[str, str]:
        """근육 상태 판정"""
        seed_ids = [s[0] for s in seeds]

        if "skeletal_muscle_low" in seed_ids:
            return "부족", "skeletal_muscle_low"
        elif "skeletal_muscle_normal" in seed_ids:
            return "정상", "skeletal_muscle_normal"
        else:
            return "정상", ""

    def _assess_fat(
        self,
        measurements: InBodyMeasurements,
        seeds: List[Tuple[str, str, str]]
    ) -> Tuple[str, str]:
        """지방 상태 판정"""
        seed_ids = [s[0] for s in seeds]

        if "body_fat_high" in seed_ids:
            return "과다", "body_fat_high"
        elif "body_fat_normal" in seed_ids:
            return "정상", "body_fat_normal"
        else:
            return "정상", ""

    def _assess_visceral_fat(
        self,
        measurements: InBodyMeasurements,
        seeds: List[Tuple[str, str, str]]
    ) -> Tuple[str, str]:
        """내장지방 위험도 판정"""
        seed_ids = [s[0] for s in seeds]

        if "visceral_fat_high" in seed_ids:
            return "주의", "visceral_fat_high"
        elif "visceral_fat_normal" in seed_ids:
            return "낮음", "visceral_fat_normal"
        else:
            return "정보 없음", ""

    def _assess_imbalance(
        self,
        measurements: InBodyMeasurements
    ) -> str:
        """부위별 불균형 판정"""
        muscle_grades = measurements.근육_부위별등급

        # 부위별 등급 분석
        upper_body = [muscle_grades.get("왼팔", ""), muscle_grades.get("오른팔", "")]
        trunk = muscle_grades.get("몸통", "")
        lower_body = [muscle_grades.get("왼다리", ""), muscle_grades.get("오른다리", "")]

        imbalances = []

        # 상체 vs 하체
        upper_weak = any("부족" in g or "표준미만" in g for g in upper_body)
        lower_weak = any("부족" in g or "표준미만" in g for g in lower_body)

        if upper_weak and not lower_weak:
            imbalances.append("상체 근육 발달이 상대적으로 부족한 경향")
        elif lower_weak and not upper_weak:
            imbalances.append("하체 근육 발달이 상대적으로 부족한 경향")

        # 몸통
        if "부족" in trunk or "표준미만" in trunk:
            imbalances.append("복부 및 몸통 근육 강화 필요")

        # 좌우 불균형
        left_right_diff = False
        if muscle_grades.get("왼팔") != muscle_grades.get("오른팔"):
            left_right_diff = True
        if muscle_grades.get("왼다리") != muscle_grades.get("오른다리"):
            left_right_diff = True

        if left_right_diff:
            imbalances.append("좌우 근육 발달 불균형")

        if not imbalances:
            return "특별한 불균형 없음"

        return ", ".join(imbalances)

    def _generate_key_risks(
        self,
        measurements: InBodyMeasurements,
        seeds: List[Tuple[str, str, str]]
    ) -> List[str]:
        """주요 위험 요소 생성 (seed tag 포함)"""
        seed_ids = [s[0] for s in seeds]
        risks = []

        if "visceral_fat_high" in seed_ids:
            risks.append(format_seed_tag("내장지방 과다로 인한 대사질환 위험", "visceral_fat_high"))

        if "skeletal_muscle_low" in seed_ids:
            risks.append(format_seed_tag("근육량 부족", "skeletal_muscle_low"))

        if "age_sarcopenia_risk" in seed_ids:
            risks.append(format_seed_tag("근감소증 위험 연령대", "age_sarcopenia_risk"))

        if "abdominal_obesity" in seed_ids:
            risks.append(format_seed_tag("복부비만 패턴", "abdominal_obesity"))

        if "bmi_overweight" in seed_ids:
            risks.append(format_seed_tag("과체중", "bmi_overweight"))

        if not risks:
            risks.append("특별한 건강 위험 요소 없음")

        return risks

    def _generate_priority_focus(
        self,
        measurements: InBodyMeasurements,
        seeds: List[Tuple[str, str, str]]
    ) -> str:
        """우선 개선 방향 생성"""
        seed_ids = [s[0] for s in seeds]

        priorities = []

        if "skeletal_muscle_low" in seed_ids:
            priorities.append("근육량 보완")

        if "visceral_fat_high" in seed_ids or "abdominal_obesity" in seed_ids:
            priorities.append("내장지방 및 복부지방 관리")

        if "body_fat_high" in seed_ids:
            priorities.append("체지방 감소")

        if not priorities:
            return "현재 체형 유지 및 균형 잡힌 운동·식단 관리"

        return " + ".join(priorities) + "가 가장 우선적인 과제로 보입니다."
