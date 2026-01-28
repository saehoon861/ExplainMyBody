## OCR Model Selection

여러 OCR 모델을 비교한 결과 PaddleOCR을 사용하였다.

### Reason
- InBody 결과지에서 표 구조 인식 성능이 안정적
- 한글 + 숫자 혼합 인식 정확도 우수

### Failure Cases
- 특정 레이아웃에서 체지방률 인식 오류
- PDF 스캔본에서 수치 누락 발생

### Decision
- OCR 결과를 사용자에게 먼저 노출
- 사용자 보정 단계를 필수로 포함