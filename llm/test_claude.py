import os
from anthropic import Anthropic
import json
from pathlib import Path
from dotenv import load_dotenv

SAMPLE_DIR = Path(__file__).parent / "json"
sample_path = SAMPLE_DIR / "sample8.json"

with open(sample_path, "r", encoding="utf-8") as f:
    sample_input = json.load(f)
    
input_json_str = json.dumps(
    sample_input,
    ensure_ascii=False,
    indent=2
)



client = Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

prompt = """
역할:
너는 규칙기반 체형 분석 결과를 입력으로 받아
운동 계획과 식단을 생성하는 생성 전용 모듈이다.

입력 설명:
아래 입력 JSON은 규칙기반 알고리즘을 통해 생성된 결과이다.
stage1_type, stage2_type, stage3는 이미 확정된 값이며,
이를 수정하거나 재해석해서는 안 된다.

금지 규칙:
- 체형 재분류 금지
- 입력 값 수정 금지
- 의학적 진단 또는 치료 표현 금지
- 자연어 설명을 JSON 외부에 출력 금지

출력 규칙:
- 반드시 JSON만 출력
- 아래 출력 스키마를 정확히 따를 것

출력 스키마:
{
  "exercise_plan": {
    "weekly_goal": string,
    "weekly_schedule": [
      {
        "day": string,
        "focus": string,
        "exercises": [
          {
            "name": string,
            "sets": number,
            "reps": number,
            "note": string
          }
        ]
      }
    ]
  },
  "diet_plan": {
    "daily_calorie_target": number,
    "macros": {
      "carbs": string,
      "protein": string,
      "fat": string
    },
    "guidelines": [string]
  },
  "explanation": string
}


입력:
{input_json_str}
"""

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=2000,
    messages=[{"role": "user", "content": prompt}]
)


output_text = response.content[0].text

OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

json_path = OUTPUT_DIR / "sample8_output.json"
raw_path = OUTPUT_DIR / "sample8_output_raw.txt"

try:
    output_json = json.loads(output_text)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output_json, f, ensure_ascii=False, indent=2)

    print(f"JSON 저장 성공: {json_path}")

except json.JSONDecodeError:
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write(output_text)

    print(f"JSON 파싱 실패 → raw 저장: {raw_path}")
 
 
 #pull reqest 테스트 