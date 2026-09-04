# SEO Operations Guide

이 문서는 deadends.dev의 주요 페이지 SEO 점검을 반복 가능하게 수행하기 위한 운영 가이드입니다.

## 1) 템플릿 정적 점검

```bash
python - <<'PY'
from pathlib import Path
files=[
  'generator/templates/index.html',
  'generator/templates/domain.html',
  'generator/templates/error_summary.html',
  'generator/templates/page.html',
  'generator/templates/search.html',
  'generator/templates/dashboard.html',
]
required=[
  '<title',
  'meta name="description"',
  'meta name="robots"',
  'link rel="canonical"',
  'meta property="og:title"',
  'meta name="twitter:card"',
]
for f in files:
    txt=Path(f).read_text()
    missing=[r for r in required if r not in txt]
    print(f'✅ {f}' if not missing else f'❌ {f} missing: {", ".join(missing)}')
PY
```

## 2) 빌드 산출물 확인

```bash
python -m generator.build_site
python -m http.server -d public 8080
```

브라우저 확인 포인트:
- `http://localhost:8080/`
- `http://localhost:8080/search/`
- `http://localhost:8080/dashboard/`
- 각 페이지 `view-source`에서 canonical, OG/Twitter, JSON-LD 확인

## 3) 구조화 데이터 검증

- Google Rich Results Test
- Schema.org Validator

## 4) 배포 전 최종 체크리스트

- [ ] canonical URL이 절대 경로/중복 없이 생성되는가
- [ ] noindex 페이지 정책이 의도대로 적용되는가
- [ ] JSON-LD가 문법 오류 없이 렌더링되는가
- [ ] sitemap/robots가 배포 산출물과 일치하는가

## 5) "색인 생성됨: 1페이지" 진단 (Google Search Console)

젊은(생성 3~4개월) 대규모 프로그램 생성 사이트에서 흔한 패턴이다.
GSC 리포트 카테고리별 실제 의미:

| GSC 카테고리 | 수치 | 실제 원인 / 조치 |
| --- | --- | --- |
| `NOINDEX 태그에 의해 제외됨` | ~440 | **정상.** 단일 환경 canon의 `/{domain}/{slug}/{env}/` 리디렉션 스텁이다. summary 페이지로 canonical + noindex 처리한 의도된 중복 제거. 조치 불필요. |
| `robots.txt에 의해 차단됨` | ~222 | **과거 잔재.** 현재 `robots.txt`는 전부 `Allow: /`. 재크롤 시 해소. GSC에서 `유효성 검사 시작`. |
| `크롤링됨 - 현재 색인이 생성되지 않음` | ~2,459 | **핵심.** 상당수는 HTML이 아니라 `/api/v1/*.json` 2,400여 개(JSON은 웹검색 색인 불가 → 항상 이 버킷에 쌓임)로 추정된다. 웹검색 크롤러의 `/api/v1/` 차단으로 해소(아래 참조). 나머지 HTML 몫은 도메인 신뢰도/연식 게이트로, 아래 조치로 가속. |
| `색인 생성됨` | 1 | 시간이 지나며 위 대기열에서 전환됨. |

### 사실 확인
- 기술 SEO는 이미 우수(canonical, sitemap, 구조화 데이터, 내부 링크 완비).
- Bing은 정상 색인(IndexNow ping 작동 → `site:deadends.dev` 검색 시 다수 노출).
- 즉, **Google 전용 신뢰도/연식 문제**이며 코드만으로 즉시 강제 색인은 불가능하다.

### 조치 (영향 큰 순서)
1. **GSC에서 sitemap 재제출** (`https://deadends.dev/sitemap.xml`) 후
   `페이지 색인 생성` 리포트의 각 오류 카테고리에서 **`유효성 검사 시작`** 클릭.
2. **URL 검사 → 색인 생성 요청**을 핵심 허브(홈, 상위 도메인/국가 허브 20~30개)에
   우선 적용(일 10건 제한). 허브가 먼저 색인되면 크롤 에퀴티가 상세 페이지로 전달된다.
3. **외부 백링크 확보** — Google 색인 결정의 지배적 요인. GitHub README, 관련 커뮤니티,
   AI 에이전트/개발자 도구 디렉터리에 신뢰도 있는 링크 확보.
4. **허브 페이지 콘텐츠 강화** — `/{domain}/` 허브에 도메인별 고유 서문 + 데이터 기반 FAQ +
   "가장 흔한 dead end" 섹션 추가(구현 완료, `generator/domains.py::DOMAIN_INTROS`,
   `build_site.py::_build_domain_faq`). thin list 페이지 프로필을 제거해 색인 확률을 높인다.
5. **시간** — 신규 사이트는 대기열 → 색인 전환에 수 주~수 개월 소요. 주기적으로 1~2번 조치 반복.

### /api/v1/ 크롤 정책 (중요한 구분)
- **웹검색 크롤러(Googlebot, GoogleOther, Bingbot)만** `/api/v1/` 차단:
  JSON은 웹페이지로 색인될 수 없으므로 2,400+ JSON 크롤은 크롤 버짓 낭비이자
  "크롤링됨 - 색인 안 됨" 노이즈의 주범. 이 URL들의 "robots.txt에 의해 차단됨"은
  **의도된 정상 상태**다.
- **AI 크롤러(GPTBot, ClaudeBot, PerplexityBot 등)와 `User-agent: *`는 전부 허용 유지** -
  이 사이트의 존재 이유가 AI 소비다.
- 경로는 반드시 `/api/v1/`(`/api/` 아님) - `/api/{slug}/`는 "api" 에러 도메인의
  HTML 페이지라서 크롤 가능해야 한다.

### 웹검색 크롤러 제외 목록 (Googlebot / GoogleOther / Bingbot 전용)
`/api/v1/` 외에 아래 경로도 웹검색 크롤러에게만 `Disallow`한다. 전부 이미
canonical HTML 페이지가 있는 콘텐츠의 **원문 복제본**이라, 웹 색인이 크롤하면
실제 페이지와 경쟁하는 중복 문서가 되고 "크롤링됨 - 색인 안 됨" 노이즈만 쌓인다.
AI 크롤러와 `User-agent: *`는 전부 허용 유지.

| 경로 | 정체 |
| --- | --- |
| `/search-data.json` | `/search/`가 첫 입력 때 lazy-fetch하는 클라이언트 검색 인덱스(약 1.5MB) |
| `/llms.txt`, `/llms-full*.txt` | 전 canon 요약/전문 플레인텍스트 덤프(0.9MB / 4MB) |
| `/country/*/llms.txt`, `/country/*/AGENTS.md` | 국가 페이지의 플레인텍스트 복제 |
| `/indexnow-urls.txt` | IndexNow 제출용 URL 목록 |

### 2026-09 기술 점검에서 고친 것 (색인 품질 게이트 대응)
"크롤링됨 - 현재 색인이 생성되지 않음"은 Google이 페이지를 **봤지만 품질/중복
판정으로 보류**한 상태다. 아래는 그 판정에 불리하게 작용하던 사이트 자체 결함.

| 결함 | 조치 |
| --- | --- |
| `/search/`가 2.3MB HTML(검색 인덱스 JSON 인라인). 사이트맵 priority 0.9인데 색인 거부 | 인덱스를 `/search-data.json`으로 분리, 첫 입력 시 fetch. 페이지 25KB |
| 국가 canon 제목이 `Fix AI tells a tourist they can open a UAE bank… \| deadends.dev`처럼 잘리고 서로 중복(33쌍) | 제목·H1을 슬러그+국가로 생성: `Account needs residence visa in the United Arab Emirates`. 오답 문장은 H1 아래 "AI dead end" 라인으로 표시 |
| 코드 canon 제목이 70자에서 잘려 동일해지는 그룹(`An error occurred (AccessDenied)…` ×3, `cuda/nccl-timeout` vs `pytorch/nccl-timeout`) | 충돌 그룹만 `(S3 access denied)`, `(CUDA)`처럼 구분자 부착 (`title_disambiguators`) |
| 멀티 env 페이지 제목에서 환경 컨텍스트가 길면 통째로 탈락 → summary 페이지와 제목 동일 | 짧은 환경 라벨(`cpython 3.11 · linux`)로 항상 유지, 라벨까지 같으면 env id 사용 |
| `og:image`가 SVG - X/Facebook/LinkedIn/Slack 어느 곳도 SVG 카드를 렌더하지 않음 | Pillow로 도메인별·국가별·사이트 PNG 카드 생성(`/og/{domain}.png`, `/country/{cc}/og.png`). Pillow 없으면 단색 PNG 폴백 |
| TechArticle JSON-LD `description`이 "N environments, N dead ends…" 사이트 공통 템플릿 문자열 | verdict summary(페이지 고유)로 교체, `author`/`mainEntityOfPage` 추가. 국가 canon은 `Article` + `about: Country` |
| GSC 리포트의 수동 색인 요청 목록이 `/search/`, `/sitemap/`, `/dashboard/` 등 유틸리티 페이지부터 | 홈 → 규모 큰 도메인/국가 허브 순으로 정렬 (`gsc_report.rank_key`) |

빌드 산출물 자체는 정합 상태다(사이트맵 2,818 URL 전부 canonical 일치·lastmod 존재,
noindex 페이지 0건 포함, 라이브 사이트 robots/301/CNAME 정상). 즉 남은 변수는
Google의 신뢰도 게이트이며, 아래 재제출 절차와 백링크가 그 다음 조치다.

### 사이트맵 삭제 → 재제출 절차 (GSC)
1. 이 변경이 `main`에 배포된 뒤 `https://deadends.dev/sitemap.xml`을 열어
   `<lastmod>`가 갱신됐는지 확인한다(GitHub Pages 캐시 10분).
2. GSC → **Sitemaps** → 기존 `sitemap.xml` 항목의 ⋮ → **사이트맵 삭제**.
3. 같은 화면에서 `sitemap.xml`을 다시 입력해 **제출**. 하위 사이트맵 55개
   (`sitemap-main.xml` + 도메인별)는 인덱스에서 자동 발견된다. 개별 제출 불필요.
4. **페이지 색인 생성** 리포트에서 `robots.txt에 의해 차단됨`(과거 `/api/` 차단
   잔재)과 `크롤링됨 - 현재 색인이 생성되지 않음` 각각 **유효성 검사 시작**.
   - `/api/v1/*`, `/llms*.txt`, `/search-data.json`이 "차단됨"으로 남는 것은 정상.
5. **URL 검사 → 색인 생성 요청**을 아래 순서로, 하루 10건씩:
   `python -m generator.gsc_report --dry-run --limit 20` 출력 순서 = 홈 →
   `/country/` → 규모 큰 도메인 허브(`/culture/`, `/python/`, `/docker/` ...).
6. 1~2주 후 `data/seo/gsc_report.json`(주간 Actions 자동 갱신)의
   `indexed_count` 추이 확인. 허브가 색인되기 시작하면 상세 페이지가 뒤따른다.

### 하지 말 것
- 리디렉션 스텁 noindex 제거(의도된 중복 제거이므로 유지).
- lastmod를 매 배포마다 현재 시각으로 위조(Google이 신뢰도 하락으로 취급).
- `/api/` 전체 또는 전 크롤러 대상 차단(AI 에이전트 소비까지 끊김 - 위의
  "웹검색 크롤러만 /api/v1/" 정책과 혼동 금지).
- `og:image`를 다시 SVG로 되돌리기(소셜 카드가 통째로 사라진다).
- 검색 인덱스 JSON을 HTML에 다시 인라인하기.
