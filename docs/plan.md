# 상세 구현 계획 — OPC Mask CD Oscillation 설명 애니메이션

- 버전: 0.2 (검토용) · 작성일: 2026-10-28
- 기준 문서: PRD v0.2 (2026-10-28). 단, 전달받은 것은 부록 A 말미와 부록 B(변경 이력)뿐이며 본문 목록화된 FR·게이트·리스크는 미수령
- 단계: PRD → **PRD 검토/계획(현재)** → 구현/테스트 → 커밋 검토

---

## 0. PRD 검토 결과 (구현 전 해결 필요)

| # | 항목 | 내용 | 제안 |
|---|------|------|------|
| R1 | 표 누락 | v0.2에서 목록으로 재작성되었다고 하나 해당 본문은 미수령 | 본문 재전달. 없으면 §3·§6 제안값 사용 |
| R2 | 이론 원문 | **해결.** LaTeX 원고를 [theory/Discrete_OPC_Oscillation_Theory_EN.tex](theory/Discrete_OPC_Oscillation_Theory_EN.tex)로 저장(그림 validation_portrait.png 미수령). 기준값 c=0.22, M=9: A₀=1.35087026E, γ=0.10720785/µm, L=1.06184467µm, 연속 극한 L≈1.398897R_c, γ≈0.159433/R_c를 8자리까지 재현 ([theory_baseline_check.py](theory/theory_baseline_check.py)) | 경계 행렬 풀이를 독립 오라클로 테스트에 사용 |
| R3 | M=9→12 반례 조건 | **v0.2 반영·재현 완료.** 지배근 분기에서 γ(M=9)=γ(M=12) 교차점 c≈0.22046339. M=9 안정 한계와 교차점 사이(0.22 포함)에서만 M=12 감쇠가 더 강함. c=0.25: γ 0.690250 / 0.532470 /µm | presenter notes 부록 A 전용, 본편 제외 |
| R4 | S6 M=13→18→24 추세 | a/b=0.25 고정 시 L 1.52→2.08→2.75 µm, γ 0.494→0.364→0.276 /µm로 PRD 서술과 일치 | 그대로 채택 |
| R5 | git | **해결.** `mano_test/`에서 단독 `git init` (main) | — |
| R6 | 환경 | **해결.** conda env `mano` 생성(python 3.12.16, manim 0.19.1, numpy 2.5.4, scipy 1.18.1, ffmpeg 포함), 한글 Text 렌더 확인. LaTeX 없음 | `Text`만 사용. Axes 눈금 숫자도 기본 MathTex 대신 Text로 직접 생성 |

검산 스크립트: [feasibility_roots_check.py](feasibility_roots_check.py)

---

### v0.2 반영 사항
- 기준선·range sweep a/b=0.25, damping sweep a=0.25/0.30/0.40 (b=1, M=9)
- 수렴 기준 기본값: 최종 잔차 1e-12 nm (806회); 1e-10 nm(631회)도 검증 보고서에 기록
- 본편 캡션: "이 예에서는 범위가 클수록 주기가 길고 감쇠가 느립니다" — 모든 유한 stencil에 대한 일반 법칙으로 표현하지 않음

## 1. 디렉터리 구조

```
mano_test/
├── README.md               # 실행법, 환경, 산출물 목록
├── HISTORY.md              # 변경 이력
├── environment.yml         # 고정 버전 (python, manim, numpy, scipy, pytest)
├── docs/
│   ├── PRD.md              # 전달받은 PRD 원문
│   ├── plan.md             # 이 문서
│   ├── storyboard.md       # 장면별 타이밍·카피·키프레임 목록
│   ├── presenter_notes_ko.md
│   ├── validation_report.md   # scripts/validate.py가 생성
│   └── completion_report.md
├── opc_osc/                # 수치 계층 (Manim import 금지)
│   ├── model.py            # 연산자 A, P-iteration, banded direct solve, CG
│   ├── scenarios.py        # 시나리오 정의(dataclass) + config hash
│   ├── metrics.py          # 잔차, 윈도우 ptp, 특성근 예측, tail fit
│   └── store.py            # npz + json 저장/로드, 스키마 검증
├── scripts/
│   ├── generate_data.py    # 시나리오 → data/*.npz, *.json
│   ├── validate.py         # 게이트 검사 → validation_report.md
│   └── render_all.sh       # 장면 렌더 + ffmpeg/PyAV concat
├── scenes/                 # Manim 계층 (data/*.npz만 읽음)
│   ├── style.py            # 색, 폰트, 안전영역, 축 팩토리
│   ├── widgets.py          # 막대 schematic, 이산 샘플 플롯, 증거 라벨
│   └── s1_measured.py … s8_action.py
├── tests/
│   ├── test_model.py  test_metrics.py  test_scenarios.py
│   ├── test_flow.py        # config → arrays → metrics → scene input
│   └── test_render.py      # @slow: 실제 저화질 렌더 + 메타데이터 확인
├── data/                   # 생성물 (작은 npz/json은 커밋)
└── out/                    # 영상, 클립, keyframe PNG (git 제외)
```

원칙: `scenes/`는 `opc_osc.store.load()`로 검증된 배열만 소비. 장면 코드 안에서 sin/exp로 곡선을 만들지 않음(포락선 오버레이는 metrics의 특성근 결과만 사용, "근사" 라벨).

---

## 2. 수치 계약 (PRD §6 구현)

- 부호: `e = E − A u`, `u ← u + η e`, `e(n+1) = e(n) − A Δu(n)`. 원문 부호(`e_old=−e, E_old=−E`) 변환은 `model.py` docstring과 README에 기록.
- `W_M`: 중심 포함 (2M+1) 평균, 영역 밖 0, 경계 renormalize·periodic wrap 없음. 대각 감도 `a + b/(2M+1)`.
- 영역: N=4096, d=80 nm(toy 가정). 표시 영역은 0–10 µm.
- 평형해: `scipy.linalg.solve_banded` (독립 오라클). CG는 별도 보조 검증, 별도 라벨.
- P-iteration: `u(0)=0`, `η=1/(a+b)`. 수렴 판정 `max|e| ≤ tol`, 최종 반복 인덱스는 실제 판정에서 기록.
- 저장 반복: 0–10 전체 + 이후 선택 상태(예: 20, 50, 100, 200, …, final). 각 상태에 `u`, `e`, `Δu` 저장.
- 오른쪽 경계 영향: N=4096 vs 8192 결과 차이를 표시 창에서 측정해 보고.

### 특성근 / 지표
- `a + b/(2M+1) Σ r^ℓ = 0` → 2M차 다항식 근, 단위원 내부의 지배 켤레쌍에서 `L = 2πd/|θ|`, `γ = −log ρ / d`.
- 경계 행렬(원고 §4): 감쇠근 M개로 `B C = −E e₀`를 풀어 모드 합 `u_j = Σ C_ν r_ν^j`를 구성 → 직접해와 독립 비교(검산 결과 j<200에서 차 2.6e-13), A₀ = 2|C_*|.
- 원고 부호 변환: 원고 `e_old = E_old δ + A u`, `u ← u − η e_old`. PRD `e = E − A u`, `u ← u + η e`. `E_old = −E`, `e_old = −e`이면 동일한 u. 원고의 C_ν는 PRD 부호에서 그대로 쓰되 E 자리에 `−E`를 넣음(`B C = E e₀`).
- tail fit: 경계 다중모드 영역 제외(예: x ≥ 2·R_c) 후 극값 간격·로그 포락선 기울기로 L, γ 측정 → 근 예측과 비교.
- Mask variation: `max(u) − min(u)` over 0.8–8.0 µm (모든 진폭 비교에서 고정).

---

## 3. 시나리오 프리셋 (제안, 검산 완료)

| ID | 목적 | a | b | M | 강제항 E | L (µm) | γ (1/µm) | 비고 |
|----|------|---|---|---|----------|--------|----------|------|
| `main` | S1–S4 | 0.25 | 1 | 9 | E₀=+1 nm @ j=0, 그 외 0 | 1.07 | 0.69 | P 수렴: 1e-10 nm → 631회, 1e-12 nm → 806회(재현). u₀≈3.96 nm, ptp(0.8–8µm)=0.914 nm |
| `scale_k` | S5 | 〃 | 〃 | 9 | k·E₀, k∈{0.5,1,2} (선택: −1) | 동일 | 동일 | 전 배열 정확히 k배 |
| `bg` | S5 확장 | 〃 | 〃 | 9 | E_bulk·1 + δE, 배경해 별도 계산 | — | — | `u − u_bg` 비교 |
| `range_13/18/24` | S6 | 0.25 | 1 | 13/18/24 | E₀ | 1.52/2.08/2.75 | 0.494/0.364/0.276 | b 총합 고정, 이웃당 가중치는 b/(2M+1) |
| `damp_025/030/040` | S6 | 0.25/0.30/0.40 | 1 | 9 | E₀ | 1.066/1.073/1.085 | 0.690/1.101/1.602 | v0.2 반영. 진폭·감쇠 동시 변화 표시 |
| `counter_9_12` | 노트 전용 | 0.22 | 1 | 9→12 | E₀ | 1.06→1.40 | 0.107→0.121 | 교차점 c≈0.22046 이하에서만 성립, 본편 제외 |

E₀ 크기(1 nm)는 설명용. 보고된 실험값(~2 nm, <0.5 nm)과 의도적으로 맞추지 않음.

---

## 4. 장면 계획 (총 270 s, 1920×1080 @ 30 fps)

| 장면 | 시간 | 핵심 | 데이터 |
|------|------|------|--------|
| S1 측정 대상 | 20 s | 직선 막대 폭 변화(확대 배율 라벨), 상단 `Mask correction (nm)` / 하단 `Remaining error (nm)` | `main` final |
| S2 결합 | 30 s | 첫 control 강조, 국소(굵은)·이웃(가는) 화살표, R 브래킷(투명 밴드), 왼쪽 창 잘림 표시 | `main` A 열 0 |
| S3 인과 반복 | 75 s | 0→1, 1→2, 2→3 상세(읽기→Δu 점선 미리보기→적용→오차 재계산→라벨 증가), 3–10(6,7,8,9 포함) 가속, "중간 반복 생략" 후 선택 상태 → 실제 final | `main` 반복 상태 |
| S4 두 감쇠 | 30 s | 좌: `Iteration n` vs max|e| (log), 우: `Distance from left edge (µm)` vs u | `main` |
| S5 대비 | 30 s | 같은 모양, 크기만 변경 → 동일 y축에서 비례; 배경 확장은 `u−u_bg` | `scale_k`, `bg` |
| S6 고정 변수 | 40 s | Changed / Held fixed 카드, 주기 = 등위상 간격, 감쇠 = 포락선; Normalized/비정규 둘 다 | `range_*`, `damp_*` |
| S7 보고 관측 | 25 s | `Reported observation` 카드 2장(Reduced / Returned), 보정·타깃 레이아웃 구분, 숫자는 기본 비표시 | 없음(정성) |
| S8 행동 | 20 s | PRD §5 S8 한국어 3줄, 8 s 이상 정지 | 없음 |

공통 스타일: 밝은 배경, 진한 글자, 마스크 보정 = 청색 계열 실선+원 마커, 오차 = 주황 계열 점선+사각 마커(색 외 선형·마커로도 구분). 본문 ≥34 px, 축 ≥26 px, 5% 안전영역, 하단 고정 캡션 영역. 반복 시퀀스 내 y축 고정, 작은 오차는 고정 배율 inset.

---

## 5. 환경

- conda env `mano` (conda-forge): python 3.12, manim 0.19.x, numpy, scipy, pytest. 설치 후 실제 버전을 `environment.lock.yml`로 고정.
- LaTeX 미사용 → TeX 의존성 없음. 폰트 `Noto Sans CJK KR`.
- 인코더: Manim 내장 PyAV. 최종 concat은 PyAV 또는 conda ffmpeg.

---

## 6. 검증 게이트 (PRD §12.1 표 누락에 대한 제안값)

| 게이트 | 기준 |
|--------|------|
| 직접해 잔차 | `max|E − A u*|` ≤ 1e-12 nm |
| P 최종 vs 직접해 | `max|u_final − u*|` ≤ 1e-8 nm |
| CG vs 직접해 | ≤ 1e-8 nm |
| 오차 갱신 항등식 | 저장된 모든 반복에서 `e(n+1)` 재계산 차 ≤ 1e-12 |
| 스케일링 | `u(kE) − k·u(E)` 상대오차 ≤ 1e-12; 부호반전 동일 |
| 오른쪽 경계 | N=4096 vs 8192, 0–10 µm에서 차 ≤ 1e-12 nm |
| 주기/감쇠 tail fit | L 오차 ≤ 2%, γ 오차 ≤ 5% (신뢰 불가 시 사유 기록, 기준 완화 금지) |
| local-only | b=0이면 u = E/a, 진동 없음 |
| 장면 데이터 대응 | 장면 입력 배열 해시 = data 파일 해시 |

테스트 레벨: Unit(위 항목 + 잘못된 파라미터 예외), Flow(config→arrays→metrics→scene input), Job(`-ql` 실제 렌더 + 길이/해상도 메타 확인), Visual(장면별 keyframe PNG + S3 상세 단계 전부 수동 검토).

---

## 7. 작업 순서

1. env 생성·버전 고정, `git init`
2. `opc_osc/` + unit tests → `generate_data.py` → `validate.py` (게이트 통과 확인)
3. `scenes/style.py`, `widgets.py` → S1, S3 먼저(핵심 인과) → S2, S4 → S5, S6 → S7, S8
4. 저화질 렌더로 keyframe 검토 → 1080p 최종 렌더 → concat
5. storyboard, presenter notes, validation/completion report, README/HISTORY
6. 커밋 검토 (push 없음)
