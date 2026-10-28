# History

## 2026-10-28
- PRD v0.1/v0.2 검토, 상세 계획(docs/plan.md), 이론 원고 저장 및 기준값 재현
- conda env `mano` (manim 0.19.1) 구성, git init
- 수치 계층 `opc_osc/` 구현: 연산자, P 반복, banded direct, CG, 특성근·경계 행렬, tail fit, 시나리오 14종, 저장/검증
- 테스트 40개, 검증 게이트 96개 통과 (docs/validation_report.md)
- 장면 S1–S4 구현(scenes/): 공통 스타일·고정 축 Panel, S1 측정 대상, S2 이웃 결합, S3 인과 반복(0→3 상세, 3→10 가속, 806 수렴), S4 두 감쇠
- 승인된 설계: S3 고정 확대 축(u ±0.6 nm, e ±0.06 nm, 범위 밖 값은 부호와 함께 표시), S1 0–0.8 µm 보정 폭 생략(점선 = nominal 윤곽, ×50은 u에만), 최종 표기 max|e| < 10⁻¹² nm
- data에 단일 control 응답(A의 열) 추가, 검증 게이트 99개 통과
