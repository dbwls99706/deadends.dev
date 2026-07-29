# Google Search Console API 연동 (1회 설정)

`generator/gsc_report.py`가 색인 상태를 조회하고 사이트맵을 재제출하려면
서비스 계정이 필요하다. 아래는 한 번만 하면 되는 설정이다.

전체 10분.

## 0. 프로젝트 선택

서비스 계정은 **프로젝트에 귀속되는 리소스**다. 조직(`yujinhong-org`,
ID `56145778260`)에는 직접 만들 수 없고, 조직 아래 프로젝트가 하나 필요하다.

`yujinhong-org` 아래에서 쓸 프로젝트를 정하거나 새로 만든 뒤, 아래 단계의
`<PROJECT_ID>`를 그 프로젝트 ID로 바꿔서 진행한다.

- 프로젝트 목록: https://console.cloud.google.com/cloud-resource-manager?organizationId=56145778260
- 새로 만들 때 **위치(조직)** 를 `yujinhong-org`로 지정할 것

**기존 프로젝트(예: `sortzen`)에 얹어도 된다.** 이 서비스 계정에는 GCP IAM
역할을 하나도 부여하지 않기 때문에, 같은 프로젝트에 있어도 그 프로젝트의
리소스에는 접근할 수 없다. 권한은 전적으로 Search Console 쪽에서 나온다.
전용 프로젝트를 따로 파면 정리·감사가 깔끔해지는 정도의 이점이 있을 뿐이다.

단, 얹는 경우 아래 두 가지는 지킬 것:

- 서비스 계정 생성 시 **역할을 절대 부여하지 말 것.** 습관적으로 `편집자`나
  `소유자`를 고르면 그 순간 프로젝트 전체 접근 권한이 생긴다.
- 프로젝트를 삭제하면 서비스 계정도 같이 사라져 이 리포트가 멈춘다.

## 1. Search Console API 활성화

1. `https://console.cloud.google.com/apis/library?project=<PROJECT_ID>`
2. **Google Search Console API** 검색 → **사용 설정**

> Indexing API는 활성화하지 않아도 된다. 그쪽은 JobPosting / BroadcastEvent
> 전용이라 이 사이트에는 쓸 수 없다.

## 2. 서비스 계정 생성

1. `https://console.cloud.google.com/iam-admin/serviceaccounts?project=<PROJECT_ID>`
2. **서비스 계정 만들기**
   - 이름: `gsc-reporter`
   - 역할: **없음** (GCP IAM 역할은 필요 없다. 권한은 Search Console 쪽에서 준다)
3. 생성된 계정 클릭 → **키** 탭 → **키 추가 → 새 키 만들기 → JSON** → 다운로드
4. 계정 이메일을 복사해 둔다. 형태:
   `gsc-reporter@<PROJECT_ID>.iam.gserviceaccount.com`

## 3. Search Console에 서비스 계정 추가

1. https://search.google.com/search-console → 속성 `deadends.dev` 선택
2. **설정 → 사용자 및 권한 → 사용자 추가**
3. 위에서 복사한 서비스 계정 이메일 붙여넣기
4. 권한: **전체** (사이트맵 제출에 필요. 조회만 할 거면 `제한됨`도 가능)

## 4. 키를 환경변수로 등록

Claude Code 웹 → 환경 편집 다이얼로그 → 환경변수에 추가:

| 변수 | 값 |
| --- | --- |
| `GSC_SA_KEY` | 다운로드한 JSON 파일 **전체 내용**을 그대로 붙여넣기 |
| `GSC_PROPERTY` | `https://deadends.dev/` (기본값과 같으면 생략 가능) |

로컬에서 돌릴 때는 파일 경로만 줘도 된다:

```bash
export GSC_SA_KEY_FILE=~/keys/gsc-reporter.json
```

> JSON 키는 비밀값이다. 리포지토리에 커밋하지 말 것. `.gitignore`에 이미
> `*.json` 예외가 없으므로 키 파일은 리포 바깥에 두는 것을 권장한다.

## 5. 동작 확인

```bash
pip install -e ".[seo]"
python -m generator.build_site          # 사이트맵이 있어야 URL 목록을 뽑는다
python -m generator.gsc_report --dry-run --limit 12   # 자격증명 없이 계획만 확인
python -m generator.gsc_report --limit 20            # 실제 조회
```

정상이면 이런 출력이 나온다:

```
  Inspected: 20
  Indexed:   3
  Not yet:   17
  Change since last run: +2

  Not-indexed breakdown:
     14  Crawled - currently not indexed
      3  Discovered - currently not indexed

  Request indexing by hand in Search Console (URL Inspection),
  highest value first - Google caps this at ~10/day:

     1. https://deadends.dev/
     2. https://deadends.dev/visa/
     ...
```

## 자동화 범위

| 작업 | 자동 | 비고 |
| --- | --- | --- |
| 사이트맵 재제출 | O | `--submit-sitemap` |
| URL별 색인 상태 조회 | O | URL Inspection API, 일 2,000건 / 분 600건 |
| IndexNow (Bing·Yandex) | O | 배포 워크플로에 이미 포함 |
| **색인 생성 요청** | **X** | Indexing API가 JobPosting / BroadcastEvent 전용이라 불가. 스크립트가 뽑아주는 10개 목록을 GSC UI에서 직접 클릭해야 한다 |
| **유효성 검사 시작** | **X** | API 없음, UI 전용 |

색인 요청은 Google이 하루 10건 정도로 제한한다. 스크립트가 허브 페이지를
우선으로 정렬해 주는 이유가 이것이다 — 허브가 먼저 색인되어야 크롤 에퀴티가
상세 페이지로 내려간다. 자세한 배경은
[`SEO_OPERATIONS_GUIDE.md`](SEO_OPERATIONS_GUIDE.md) 5절 참고.

## 결과 파일

`data/seo/gsc_report.json`에 매 실행 결과가 저장된다. 다음 실행 때
`Change since last run` 계산에 쓰이므로 커밋해 두면 주간 추이가 남는다.
