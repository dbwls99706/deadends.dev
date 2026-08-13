# PyPI Release Manual (Copy/Paste)

## 0) 사전 준비

```bash
python -m pip install --upgrade pip build twine
```

## 1) 최신 코드 동기화 및 테스트

```bash
git pull --rebase
python -m pytest -q
```

## 2) 버전 업데이트 확인

```bash
rg '^version\\s*=\\s*".*"' pyproject.toml
```

필요하면 `pyproject.toml`의 version을 올린 뒤 커밋합니다.

## 3) 배포 파일 생성

```bash
rm -rf dist/ build/ *.egg-info
python -m build
```

## 4) 업로드 전 패키지 유효성 검사

```bash
python -m twine check dist/*
```

## 5) TestPyPI 먼저 업로드(권장)

```bash
python -m twine upload --repository testpypi dist/*
```

## 6) TestPyPI 설치 검증

```bash
python -m venv .venv-testpypi
source .venv-testpypi/bin/activate
python -m pip install -U pip
python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple deadends-dev
deadends "ModuleNotFoundError: No module named 'torch'"
deactivate
```

## 7) 실제 PyPI 업로드

```bash
python -m twine upload dist/*
```

## 8) PyPI 설치 최종 검증

```bash
python -m venv .venv-release-check
source .venv-release-check/bin/activate
python -m pip install -U pip
python -m pip install deadends-dev
deadends "CUDA error: out of memory"
deactivate
```

## 9) MCP Registry 갱신

PyPI 업로드까지만 하고 여기서 멈추면 레지스트리가 옛 버전을 계속 광고한다.
실제로 그렇게 6개월간 0.3.2가 노출됐다. **PyPI 업로드 다음에 반드시 이어서
수행한다.**

레지스트리는 PyPI 패키지 설명(= README)에서 `mcp-name:` 문자열을 찾아 소유권을
검증한다. 그래서 순서가 중요하다 — README 마커가 들어간 배포본이 PyPI에 먼저
올라가 있어야 한다.

```bash
# 버전 일치 확인 (pyproject.toml == server.json == packages[].version)
python -m pytest tests/test_release_metadata.py -q

# publisher 설치 (최초 1회)
brew install mcp-publisher
# 또는
curl -L "https://github.com/modelcontextprotocol/registry/releases/latest/download/mcp-publisher_$(uname -s | tr '[:upper:]' '[:lower:]')_$(uname -m | sed 's/x86_64/amd64/;s/aarch64/arm64/').tar.gz" | tar xz mcp-publisher && sudo mv mcp-publisher /usr/local/bin/

mcp-publisher validate
mcp-publisher login dns --domain deadends.dev   # dev.deadends/* 네임스페이스용
mcp-publisher publish
```

게시 확인:

```bash
curl -s "https://registry.modelcontextprotocol.io/v0/servers?search=deadends" \
  | python -m json.tool | grep -E '"name"|"version"'
```

### 중복 엔트리 주의

레지스트리에 두 개가 등록되어 있다:

| 이름 | 인증 방식 |
| --- | --- |
| `dev.deadends/deadends-dev` | DNS (deadends.dev 소유 증명) — **이쪽을 유지** |
| `io.github.dbwls99706/deadends-dev` | GitHub 계정 |

`server.json`은 DNS 쪽을 쓴다. 둘 다 `active`로 남아 있으면 검색 결과에 같은
서버가 두 번 뜨므로, GitHub 네임스페이스 쪽은 `mcp-publisher status`로
deprecated 처리하는 것이 좋다.
