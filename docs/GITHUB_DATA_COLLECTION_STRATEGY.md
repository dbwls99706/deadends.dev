# GitHub 기반 이슈/해결 방안 데이터 자동 수집 전략

Repository: https://github.com/dbwls99706/deadends.dev

## 목표

- GitHub의 **Issues / PR / Discussions / Commit 메시지**에서 에러 시그니처와 해결 방안을 자동 수집
- 수집 데이터를 `dead_ends`, `workarounds`, `transition_graph` 후보로 정규화
- 사람 검수(maintainer review)와 자동 점수화(신뢰도/재현성)를 결합해 품질 유지

## 1) 수집 대상과 우선순위

1. **Issues (bug / question / troubleshooting)**
   - 에러 원문, 재현 조건, 환경 정보 수집에 가장 유리
2. **Pull Requests**
   - 실제 수정 코드 + 커밋으로 “무엇이 해결했는지” 추적 가능
3. **Discussions**
   - 초기 트러블슈팅 아이디어 탐색용
4. **Commit 메시지**
   - `fix`, `resolve`, `workaround`, `hotfix`, `OOM`, `forbidden` 같은 키워드 추출

## 2) GitHub에서 자동 수집하는 방법

### A. Scheduled GitHub Actions + API 수집

- 주기: 6시간 또는 1일
- 방식:
  - GitHub REST API Search (`issues`, `pulls`)
  - GraphQL API로 코멘트/라벨/머지 상태/관련 파일 메타까지 수집
- 산출물:
  - `data/raw/github/<date>/issues.ndjson`
  - `data/raw/github/<date>/prs.ndjson`

권장 검색 키워드 예시:
- `"error" OR "exception" OR "failed" OR "crash" OR "OOM" OR "forbidden"`
- 언어/도메인별: `python`, `docker`, `kubernetes`, `cuda`, `redis`, `tensorflow` 등

### B. Event-driven (Webhook) 수집

- 트리거 이벤트:
  - `issues.opened`, `issues.edited`, `issue_comment.created`
  - `pull_request.opened`, `pull_request.closed`, `pull_request_review.submitted`
- 장점:
  - 실시간 반영 가능
- 주의:
  - 스팸/노이즈 필터 필수 (유사도, 템플릿 충족 여부, 계정 신뢰도)

## 3) 데이터 정규화 파이프라인

1. **텍스트 파싱**
   - 에러 시그니처 후보 추출 (regex + 룰 기반)
2. **환경 추출**
   - OS / 런타임 / 버전 / 프레임워크
3. **행동 분류**
   - 실패 행동 → `dead_ends[]`
   - 성공 행동 → `workarounds[]`
4. **증거 링크화**
   - PR/Issue URL을 `sources[]`에 저장
5. **신뢰도 점수화**
   - merged PR 가중치 > issue comment
   - 재현 보고 수, 반박 여부, 최신성 반영

## 4) GitHub 운영 설계 (권장)

- 라벨 표준화:
  - `error-signature`
  - `workaround-confirmed`
  - `dead-end-confirmed`
  - `needs-repro`
  - `needs-domain-review`
- 이슈 템플릿 강제:
  - 에러 원문(필수)
  - 환경 정보(필수)
  - 시도한 것(실패/성공 분리)
  - 참고 링크
- PR 템플릿:
  - 어떤 에러 ID를 업데이트했는지 명시
  - 근거 링크(issues / docs / release note)

## 5) 품질 안전장치

- 자동 생성 데이터는 바로 publish하지 않고 **staging dataset**에 적재
- 기준 미달(신뢰도 낮음, 근거 부족)은 `candidate` 상태로 유지
- 배포 전 검증:
  - 스키마 검증
  - 중복/충돌 검증
  - 회귀 검증(기존 high-confidence 항목 악화 여부)

## 6) GitHub Actions 구성 제안

1. `collect_github_signals.yml` (schedule + workflow_dispatch)
2. `normalize_candidates.yml` (raw → candidate json)
3. `score_candidates.yml` (confidence / evidence score)
4. `publish_curated.yml` (review 통과본만 본 데이터 반영)

### 현재 저장소에 반영된 최소 자동화

- Workflow: `.github/workflows/collect-github-signals.yml`
  - 6시간마다 자동 실행 + 수동 실행(workflow_dispatch)
  - 기본 주기: `cron: 17 */6 * * *` (하루 4회)
- Script: `scripts/collect_github_signals.py`
  - 최근 N일 이슈/PR을 GitHub API로 수집
  - 단일 레포가 아닌 다중 레포(`--repos owner/repo1,owner/repo2`) 수집 지원
  - `--min-score` 기반 1차 품질 필터(기본 2점)
  - `data/raw/github/<YYYY-MM-DD>/issues.ndjson`, `prs.ndjson` 생성
  - 결과를 Actions artifact로 업로드

정확도 원칙:
- 자동 수집 결과는 **후보(candidate)** 입니다.
- `quality_score`(closed/comment/label/error-context) 기준을 통과한 항목만 우선 수집합니다.
- 최종 반영은 maintainer 검수 + 스키마 검증 + 충돌 검증을 거친 뒤 진행합니다.

## 7) 바로 시작할 최소 실행안 (MVP)

1. GitHub Issue/PR 템플릿에 필수 필드 강화
2. 일 1회 Action으로 최근 24시간 이슈/PR 수집
3. `data/raw/github/`에 NDJSON 적재
4. 상위 confidence 20개만 maintainer review 큐로 자동 이관
5. 승인된 것만 `data/canons/` 갱신

---

핵심 원칙: **자동 수집은 후보 생성까지, 최종 반영은 검수 기반**.
