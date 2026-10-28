# OPC Mask CD Oscillation — Manim 설명 영상

이산 OPC toy model(`A = aI + b·W_M`, P-type correction)로 수렴 후 마스크 CD 진동이 남는 이유를 설명하는 Manim 영상 프로젝트.

- 요구사항: [docs/plan.md](docs/plan.md) (PRD v0.2 검토 및 상세 계획), 이론: [docs/theory/](docs/theory/)
- 구조: `opc_osc/`(수치, Manim 비의존) → `data/`(검증된 배열) → `scenes/`(Manim, 배열만 소비)

## 환경

```
conda env create -f environment.yml      # 정확한 버전: environment.lock.yml
```
LaTeX 불필요(모든 글자는 Pango `Text`, 폰트 Noto Sans CJK KR).

## 실행

```
PY=/home/kyp/miniconda/envs/mano/bin/python
$PY -m pytest                       # unit + flow
$PY scripts/generate_data.py        # data/<id>.npz, .json
$PY scripts/validate.py             # docs/validation_report.md (실패 시 exit 1)
$PY -m pytest -m slow               # 실제 Manim 렌더 (job level)
scripts/render_all.sh               # 1080p30 장면 렌더 + 연결 → out/opc_mask_cd_oscillation.mp4
QUALITY=preview scripts/render_all.sh   # 480p15 미리보기
```

## 산출물

- 영상: [deliverables/opc_mask_cd_oscillation.mp4](deliverables/opc_mask_cd_oscillation.mp4) (1080p30, 265 s, 커밋된 배포본) · 작업용 렌더는 `out/`(git 제외)
- 문서: [docs/storyboard.md](docs/storyboard.md), [docs/presenter_notes_ko.md](docs/presenter_notes_ko.md),
  [docs/validation_report.md](docs/validation_report.md), [docs/completion_report.md](docs/completion_report.md)

## 부호 규약

`e = E − A u`, `u ← u + η e` (PRD). 이론 원고의 `e_old = E_old δ + A u`, `u ← u − η e_old`와는 `e_old = −e`, `E_old = −E`로 같은 u를 기술.
