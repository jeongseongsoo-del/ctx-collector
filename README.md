# CTX Collector

FastAPI 기반 상품 상세 스크래퍼 서비스입니다. `itemCd` 값을 받아 CTX 상세 페이지를 방문하고, 사양/배송/상세 HTML을 JSON 형태로 반환합니다.

## 로컬 실행

```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 예시 요청

```http
GET /scrape-item?itemCd=3353216&compCd=C
```

## ChromeDriver 이슈 해결

`webdriver-manager`가 루트 영역인 `/.wdm` 경로에 캐시를 만들려다 권한 문제로 실패할 수 있습니다. 이 프로젝트는 컨테이너에 설치된 시스템 Chrome/ChromeDriver를 직접 사용하도록 변경되어 있습니다.

Docker 환경에서는 아래 환경 변수를 그대로 사용합니다.

```bash
CHROME_BIN=/usr/bin/chromium
CHROMEDRIVER_BIN=/usr/bin/chromedriver
```

## Cloudtype 배포

1. GitHub 저장소를 Cloudtype에 연결합니다.
2. Python 또는 Docker 기반으로 배포합니다.
3. 포트 번호를 `8000`으로 설정합니다.
4. 시작 명령은 아래를 사용합니다.

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

또는 Dockerfile 기반 배포를 사용할 수 있습니다.
