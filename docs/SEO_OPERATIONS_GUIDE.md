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
