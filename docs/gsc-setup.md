# Google Search Console API 연동 (1회 설정)

`generator/gsc_report.py`가 색인 상태를 조회하고 사이트맵을 재제출하려면
Google 인증이 필요하다.

**키는 만들지 않는다.** 이 조직에는 `iam.disableServiceAccountKeyCreation`
정책이 걸려 있어 서비스 계정 키를 생성할 수 없고, 애초에 그게 더 안전하다.
대신 Workload Identity Federation(WIF)으로 GitHub Actions의 OIDC 토큰을
단기 Google 자격증명으로 교환한다. 유출될 장기 비밀이 존재하지 않는다.

전체 15분. 아래 명령은 브라우저에서 바로 열리는
[Cloud Shell](https://shell.cloud.google.com)에 붙여넣으면 된다 (로컬 gcloud
설치 불필요).

## 1. GCP 설정 (Cloud Shell)

`PROJECT_ID`만 본인 프로젝트로 바꾸고 통째로 실행한다. 기존 프로젝트에 얹어도
된다 — 이 서비스 계정에는 GCP IAM 역할을 부여하지 않으므로 그 프로젝트의
리소스에는 접근하지 못한다.

```bash
PROJECT_ID=sortzen-500101
REPO=dbwls99706/deadends.dev
SA=gsc-reporter

gcloud config set project "$PROJECT_ID"
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')

gcloud services enable \
  searchconsole.googleapis.com \
  iamcredentials.googleapis.com \
  sts.googleapis.com

gcloud iam service-accounts create "$SA" \
  --display-name="Search Console reporter"
SA_EMAIL="$SA@$PROJECT_ID.iam.gserviceaccount.com"

gcloud iam workload-identity-pools create github \
  --location=global --display-name="GitHub Actions"

gcloud iam workload-identity-pools providers create-oidc github \
  --location=global \
  --workload-identity-pool=github \
  --display-name="GitHub OIDC" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository=='$REPO'"

gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/github/attribute.repository/$REPO"

echo
echo "GCP_SA_EMAIL      = $SA_EMAIL"
echo "GCP_WIF_AUDIENCE  = //iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/github/providers/github"
```

마지막 두 줄 출력을 복사해 둔다.

> `--attribute-condition`이 이 리포지토리에서 온 요청만 받도록 제한한다.
> 이게 없으면 GitHub의 **아무** 리포지토리나 이 서비스 계정을 가장할 수 있다.
> 절대 빼지 말 것.

## 2. Search Console에 권한 부여

1. https://search.google.com/search-console → 속성 `deadends.dev` 선택
2. **설정 → 사용자 및 권한 → 사용자 추가**
3. 위 `GCP_SA_EMAIL` 값 붙여넣기
4. 권한: **전체** (사이트맵 제출에 필요. 조회만 할 거면 `제한됨`도 가능)

`deadends.dev`는 URL-접두어 속성이 아니라 **도메인 속성**이다(속성 전환 드롭다운에
`https://` 없이 `deadends.dev`로만 표시됨). 그래서 API 호출의 `siteUrl`은 반드시
`sc-domain:deadends.dev` 형식이어야 한다 - `https://deadends.dev/`를 쓰면 권한이
있어도 모든 호출이 `403 You do not own this site`로 실패한다. `generator/gsc_report.py`의
`DEFAULT_PROPERTY`와 `gsc-report.yml`의 `GSC_PROPERTY` 기본값이 이미 이 형식으로
맞춰져 있으니, 이후 `GSC_PROPERTY`를 오버라이드할 일이 있으면 이 형식을 유지할 것.

GCP IAM이 아니라 여기서 권한이 나온다. 그래서 서비스 계정을 다른 프로젝트에
얹어도 안전하다.

## 3. GitHub 시크릿 등록

리포지토리 → **Settings → Secrets and variables → Actions → New repository secret**

| 이름 | 값 |
| --- | --- |
| `GCP_SA_EMAIL` | 1단계 출력의 `GCP_SA_EMAIL` |
| `GCP_WIF_AUDIENCE` | 1단계 출력의 `GCP_WIF_AUDIENCE` |

둘 다 없으면 워크플로가 조용히 건너뛴다(실패하지 않는다).

## 4. 동작 확인

리포지토리 → **Actions → Weekly Search Console Report → Run workflow**

성공하면 잡 요약(Job Summary)에 이런 출력이 붙는다:

```
  Inspected: 120
  Indexed:   3
  Not yet:   117
  Change since last run: +2

  Not-indexed breakdown:
     94  Crawled - currently not indexed
     23  Discovered - currently not indexed

  Request indexing by hand in Search Console (URL Inspection),
  highest value first - Google caps this at ~10/day:

     1. https://deadends.dev/
     2. https://deadends.dev/visa/
     ...
```

## 실행 주기

| 무엇 | 언제 | 하는 일 |
| --- | --- | --- |
| `gsc-report.yml` (GitHub Actions) | 일요일 22:00 UTC = **월요일 07:00 KST** | 사이트맵 재제출, 색인 상태 조회, `data/seo/gsc_report.json` 커밋 |
| 주간 SEO Routine (Claude) | **월요일 09:00 KST** | 위 리포트를 읽고 출처 검증 + 백링크 PR |

Actions가 먼저 돌아야 Routine이 최신 데이터를 읽는다.

## 로컬에서 돌릴 때

키를 만들 수 없으므로 로컬 실행은 기본적으로 지원하지 않는다. 자격증명 없이
URL 선정 로직만 확인하려면:

```bash
pip install -e ".[seo]"
python -m generator.build_site
python -m generator.gsc_report --dry-run --limit 12
```

정책 예외로 키를 발급받은 경우에만 `GSC_SA_KEY_FILE`로 실제 조회가 가능하다.

## 자동화 범위

| 작업 | 자동 | 비고 |
| --- | --- | --- |
| 사이트맵 재제출 | O | `--submit-sitemap` |
| URL별 색인 상태 조회 | O | URL Inspection API, 일 2,000건 / 분 600건 |
| IndexNow (Bing·Yandex) | O | 배포 워크플로에 이미 포함 |
| **색인 생성 요청** | **X** | Indexing API가 JobPosting / BroadcastEvent 전용이라 불가. 리포트가 뽑아주는 10개 목록을 GSC UI에서 직접 클릭해야 한다 |
| **유효성 검사 시작** | **X** | API 없음, UI 전용 |

색인 요청은 Google이 하루 10건 정도로 제한한다. 리포트가 허브 페이지를
우선으로 정렬해 주는 이유가 이것이다 — 허브가 먼저 색인되어야 크롤 에퀴티가
상세 페이지로 내려간다. 다만 이건 2순위 조치이고,
[`SEO_OPERATIONS_GUIDE.md`](SEO_OPERATIONS_GUIDE.md) 5절은 **백링크**를
색인 결정의 지배적 요인으로 지목한다. 그쪽은 자동화되어 있다.

## 결과 파일

`data/seo/gsc_report.json`에 매 실행 결과가 저장되고, 다음 실행 때
`Change since last run` 계산에 쓰인다. Actions가 자동 커밋한다.
