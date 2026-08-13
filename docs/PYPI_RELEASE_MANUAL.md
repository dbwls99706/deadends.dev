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
검증한다. 그래서 순서가 중요하다 - 마커가 들어간 배포본이 PyPI에 먼저 올라가
있어야 한다.

### 9-1) publisher 설치 (최초 1회)

```bash
# Linux
curl -L "https://github.com/modelcontextprotocol/registry/releases/latest/download/mcp-publisher_linux_amd64.tar.gz" | tar xz mcp-publisher
sudo mv mcp-publisher /usr/local/bin/

# macOS (Homebrew가 있는 경우)
brew install mcp-publisher

mcp-publisher --help
```

### 9-2) server.json 검증

```bash
python -m pytest tests/test_release_metadata.py -q   # 버전/전송타입 사전 점검
mcp-publisher validate
```

`remotes[].type`은 `streamable-http` 또는 `sse`만 허용된다. `transportType`은
이 스키마의 필드가 아니다. `tests/test_release_metadata.py`가 같은 것을
검사하므로 보통 여기서 먼저 걸린다.

### 9-3) DNS 키 생성과 TXT 레코드 (최초 1회)

`server.json`의 이름이 `dev.deadends/...`이므로 GitHub이 아니라 **도메인 인증**을
쓴다. 키 페어를 만들고 공개키를 DNS에 올린다.

```bash
MY_DOMAIN="deadends.dev"

openssl genpkey -algorithm Ed25519 -out key.pem      # key.pem은 절대 커밋하지 말 것
PUBLIC_KEY="$(openssl pkey -in key.pem -pubout -outform DER | tail -c 32 | base64)"
echo "${MY_DOMAIN}. IN TXT \"v=MCPv1; k=ed25519; p=${PUBLIC_KEY}\""
```

출력된 TXT 레코드를 DNS에 추가한다. **반드시 도메인 apex(`deadends.dev`)에
넣는다** - `_mcp-auth.deadends.dev` 같은 셀렉터 아래에 두면 레지스트리가 찾지
못하고 서명 오류로 실패한다. 키를 교체할 때는 기존 레코드를 먼저 지운다.
남아 있으면 그쪽이 먼저 시도되어 검증이 깨진다.

전파 확인:

```bash
dig +short TXT deadends.dev | grep MCPv1
```

macOS 기본 `openssl`은 LibreSSL이라 Ed25519를 지원하지 않는다. `brew install
openssl@3` 후 그 경로의 바이너리를 직접 호출한다.

### 9-4) 로그인과 게시

```bash
PRIVATE_KEY="$(openssl pkey -in key.pem -noout -text | grep -A3 "priv:" | tail -n +2 | tr -d ' :\n')"
mcp-publisher login dns --domain deadends.dev --private-key "${PRIVATE_KEY}"
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
| `dev.deadends/deadends-dev` | DNS (deadends.dev 소유 증명) - **이쪽을 유지** |
| `io.github.dbwls99706/deadends-dev` | GitHub 계정 |

`server.json`은 DNS 쪽을 쓴다. 둘 다 `active`로 남아 있으면 검색 결과에 같은
서버가 두 번 뜨므로, GitHub 네임스페이스 쪽은 `mcp-publisher status`로
deprecated 처리하는 것이 좋다.
