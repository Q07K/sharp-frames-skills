# FastAPI 게시글 API: 첫 구현과 구조 정리

이 대화의 AI가 만든 실행 가능한 설명용 예제입니다. 먼저 한 파일의 `before`를 작성해
공통 계약 9개가 통과하는 것을 확인한 뒤, Sharp Frames의 재사용·정책 소유자·동작 보존
기준으로 `after`를 구성했습니다. 두 독립 모델의 스킬 사용/미사용 실험은 아닙니다.
기존 평가 fixture나 grader를 고친 비교도 아닙니다.

## 같은 API 계약

| 요청 | 동작 | 권한 |
| --- | --- | --- |
| `POST /auth/register` | 회원가입, 중복 이름은 409 | 공개 |
| `POST /auth/login` | JSON 아이디·비밀번호로 1시간 Bearer 토큰 발급 | 공개 |
| `GET /posts` | ID 순 목록, limit 1~100·offset 0 이상 | 공개 |
| `GET /posts/{id}` | 게시글 조회, 없으면 404 | 공개 |
| `POST /posts` | 게시글 작성 | 로그인 필요 |
| `PUT /posts/{id}` | 제목·본문 전체 수정 | 작성자만 허용 |
| `DELETE /posts/{id}` | 게시글 삭제, 성공 시 204 | 작성자만 허용 |

인증 실패는 401, 다른 작성자의 수정·삭제는 403입니다. 제목은 공백 제거 후 1~120자,
본문은 1~5,000자이며 작성자 ID는 클라이언트가 지정할 수 없습니다.
회원 비밀번호는 Argon2 해시로, 무작위 세션 토큰은 SHA-256 지문과 만료 시각으로
SQLite에 저장합니다. 로그인은 JSON 요청이며 OAuth2 폼/JWT 예제는 아닙니다.

## 실행

Python 3.12 이상과 저장소 전체가 필요합니다. 저장소 루트에서 실행합니다.
requirements는 기존 FastAPI 평가 환경의 버전 고정을 재사용하고 pwdlib·Uvicorn을 추가합니다.

```sh
python -m pip install -r examples/fastapi-board/requirements.txt
python -m uvicorn main:app --app-dir examples/fastapi-board/before --port 8001
```

다른 터미널에서 정리한 버전을 실행합니다.

```sh
python -m uvicorn board_api.main:app --app-dir examples/fastapi-board/after --port 8002
```

uv가 있으면 pip 설치 대신 다음처럼 실행할 수도 있습니다.

```sh
uv run --with-requirements examples/fastapi-board/requirements.txt uvicorn board_api.main:app --app-dir examples/fastapi-board/after --port 8002
```

각 서버의 `/docs`에서 회원가입 → 로그인 → 응답의 access_token을 Authorize에 입력 →
게시글 CRUD를 사용할 수 있습니다. 기본 DB는 실행 폴더의 `board-before.sqlite3`와
`board-after.sqlite3`로 분리됩니다. `BOARD_DB_PATH` 환경 변수로 경로를 바꿀 수 있습니다.

이 작은 예제의 범위는 로컬 API·SQLite입니다. 운영 배포·브라우저 로그인·메일 인증·
비밀번호 재설정·요청 제한·세션 정리 작업은 구현하지 않았습니다.

## 무엇을 옮겼나

| 첫 구현의 위치 | 정리 후 위치 | 이유 |
| --- | --- | --- |
| `main.py`의 앱 생성·시작 처리 | `board_api/main.py` | 앱 구성과 라우터 연결을 한눈에 확인 |
| 테이블 정의·요청별 연결 | `board_api/db.py` | DB 연결의 생성·종료 책임을 모음 |
| 요청·응답 모델 | `board_api/schemas.py` | 공개 API 계약을 라우터끼리 공유 |
| 비밀번호·세션 검증 | `board_api/auth.py` | 인증 판단과 토큰 지문 생성을 모음 |
| 수정·삭제의 조회/작성자 검사 | `board_api/post_access.py` | 두 경로가 같은 소유권 정책을 사용 |
| 회원·게시글 엔드포인트 | `board_api/routers/` | 기능별 HTTP 진입점을 찾기 쉽게 분리 |

수정·삭제 모두 `get_owned_post`를 사용하고, 그 안에서 `get_post`를 재사용합니다.
나머지 작은 SQL 작업은 라우터에 둡니다. 이 예제에서는 별도 Service/Repository 계층이나
추상 인터페이스가 필요하지 않았습니다. 이 폴더 수가 모든 FastAPI 프로젝트의 정답은 아닙니다.

## 같은 검사로 확인

```sh
python examples/fastapi-board/tests/test_contract.py
# 한쪽만 확인할 때: --variant before 또는 --variant after
```

uv 대체 명령:

```sh
uv run --with-requirements examples/fastapi-board/requirements.txt python examples/fastapi-board/tests/test_contract.py
```

두 버전은 [같은 계약 검사](tests/test_contract.py)를 사용합니다.
요구·사용자 흐름과 연결한 [케이스 목록](tests/CASE_MATRIX.md)을 참고하세요.
각 검사마다 별도 임시 SQLite DB를 사용하며 실제 로그인 토큰과 API 경로로 검증합니다.
인증·작성자 검사·DB를 성공 mock으로 대체하지 않습니다.

2026-10-21, Windows·Python 3.13.8·고정된 requirements 환경에서 before 9개, after 9개가
통과했습니다. 기능 결과는 동률이고, 파일별 책임과 정책 중복의 변화가 비교 대상입니다.
문서의 Uvicorn 진입점도 두 버전에서 실제로 시작해 `/docs`, 회원가입, 로그인, 게시글
작성을 확인한 뒤 종료했습니다.
초기 실행에서는 테스트 보조 코드의 SQLite 연결 미종료로 정리가 실패했고, 연결을 닫도록
수정한 뒤 기준 버전부터 재확인했습니다. API 기대값을 약화하지 않았습니다.
고정된 Starlette/httpx 조합은 TestClient deprecation 경고를 출력했지만 검사는 통과했습니다.

이는 한 작성자의 설명용 사례입니다. 개발 시간·유지보수 시간·성능·운영 보안 수준이나
스킬의 인과적 품질 향상은 측정하지 않았습니다. 구조 정리에도 코드·파일을 추가하는
비용이 있고, 더 작은 프로그램은 한 파일을 유지하는 편이 나을 수 있습니다.

구현 API 참고: [FastAPI 비밀번호 해시·인증](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/),
[요청별 SQLite 연결](https://fastapi.tiangolo.com/tutorial/sql-databases/).
