# CTX Collector

FastAPI 기반 CTX 스크래퍼 서비스입니다. 상품 상세 페이지와 CTX JSON 데이터를 수집해 JSON 형태로 반환합니다.

주요 엔드포인트:
- GET /health
- GET /ctx/product?prodCd=2090849
- GET /scrape-item?itemCd=1265795&compCd=C
- GET /scrape-prod?prodCd=2090849

## 로컬 실행

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

브라우저 기반 스크래핑은 Playwright를 사용하므로, 최초 1회 브라우저 바이너리를 설치해야 합니다.

```bash
python -m playwright install chromium
```

## API 예시

상품 상세 스크래핑:

```bash
curl "http://localhost:8000/scrape-item?itemCd=1265795&compCd=C"
```

상품 정보 조회:

```bash
curl "http://localhost:8000/ctx/product?prodCd=2090849"
```

## Docker 실행

이 저장소의 Dockerfile은 Python 3.11 slim 기반이며, Playwright Chromium을 설치하도록 구성되어 있습니다.

```bash
docker build -t ctx-collector .
docker run -p 8000:8000 ctx-collector
```

접속 확인:

```bash
curl http://localhost:8000/health
```

## Cloudtype 배포

Cloudtype에 배포할 때는 Docker 기반으로 올리는 방식을 권장합니다.

1. GitHub 저장소를 Cloudtype에 연결
2. Docker 서비스로 프로젝트 선택
3. 포트 8000 설정
4. 시작 명령:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

또는 Dockerfile 기반 실행을 선택해도 됩니다.

### 권장사항
- 무료 티어에서는 브라우저 스크래핑이 항상 안전하게 동작하는 것은 아니므로, 사용량과 타이밍을 제한하는 구조가 좋습니다.
- 실제 운영에서는 동시성 제한, 타임아웃, 재시도 로직을 추가하는 것이 안전합니다.
- 현재 구조는 소규모 크롤링/조회 용도에 적합합니다.

## Git 동기화

```bash
git status
git add .
git commit -m "업데이트"
git pull --rebase origin main
git push origin main
```

## 참고

- Playwright는 컨테이너 환경에서 `--no-sandbox` 설정이 필요합니다.
- `--with-deps` 는 Debian font 의존성 문제로 인해 피하는 편이 안전합니다.
- 이번 구조는 라우터와 서비스 분리를 적용해 유지보수성을 높인 상태입니다.
- 현재 로컬 검증에서 핵심 엔드포인트는 모두 200 응답을 확인했습니다.
