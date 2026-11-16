# 쌤이다 총괄보고 (내부용 · 비공개)

- `index.html` — 대시보드 (할 일 · 이슈 · 일자별 보고 · 산출물)
- `reports/YYYY-MM-DD.html` — 그날 3명 합본 보고
- `data/YYYY-MM-DD.json` — 원본 데이터 (보고 1일 = 파일 1개)
- `files/YYYY-MM-DD/` — 산출물 원본. HTML 속 이미지는 `img/`로 분리해 둠
- `files/YYYY-MM-DD/originals/` — 각자 제출한 워드 원본 (지원자 실명이 든 원본은 올리지 않음)
- 모바일: 갤럭시 폴드 커버(344~412px)·메인(884px) 화면 기준 점검. build.py가 산출물 HTML에 모바일 보정 CSS를 자동 삽입

## 매일 흐름
1. 신상준 · 김상현 · 신우성 → 일일업무보고(워드 양식 등) 제출
2. Claude가 `data/날짜.json` 작성 → `python build.py` → push
3. 전날 할 일 중 끝난 것은 그날 보고의 `closed`에 id를 넣으면 대시보드에서 빠짐. 안 넣으면 "N일째 이월"로 남음
