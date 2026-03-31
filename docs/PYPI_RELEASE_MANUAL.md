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
