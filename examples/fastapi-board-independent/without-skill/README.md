# 게시판 API (FastAPI + SQLite)

`REQUIREMENTS.md`의 회원가입·로그인·게시글 CRUD API 구현입니다.

## 실행

```bash
# 프로젝트 루트에서
.venv/Scripts/python.exe -m uvicorn main:app            # http://127.0.0.1:8000, 문서: /docs

# 설정 지정 예 (bash)
BOARD_DB_PATH=./data/board.db SESSION_TTL_SECONDS=1800 .venv/Scripts/python.exe -m uvicorn main:app
```

PowerShell에서는 `$env:BOARD_DB_PATH = "data\board.db"`처럼 환경 변수를 지정한 뒤 실행합니다.

| 환경 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `BOARD_DB_PATH` | `<프로젝트 루트>/board.db` | SQLite 파일 경로. 상위 폴더가 없으면 만듭니다. 상대 경로는 실행 위치 기준입니다. |
| `SESSION_TTL_SECONDS` | `3600` | 세션 수명(초). 양의 정수(ASCII 숫자)만 받으며, 잘못된 값이면 서버가 시작되지 않습니다. |

스키마는 시작할 때 `CREATE TABLE IF NOT EXISTS`로 만들어지므로 따로 마이그레이션할 필요가 없습니다.

## 구조

```
main.py            uvicorn 진입점 (app = create_app())
board/config.py    환경 변수 → Settings
board/db.py        SQLite 연결·스키마 (users, sessions, posts)
board/security.py  Argon2 비밀번호 해시(pwdlib), 토큰 생성·SHA-256 지문
board/schemas.py   Pydantic 입력/출력 모델과 검증 규칙
board/deps.py      요청별 DB 연결, Bearer 인증 의존성
board/auth.py      /auth/register, /auth/login
board/posts.py     /posts CRUD
tests/             unittest 테스트
```

구현에서 정한 사항:

- 요청마다 SQLite 연결을 새로 열고 닫습니다. WAL 모드와 외래 키를 켭니다.
- 토큰은 `secrets.token_urlsafe(32)`로 만들고, DB에는 SHA-256 지문과 만료 시각(Unix 초)만 저장합니다.
  만료된 세션은 인증할 때 거절되고, 로그인할 때 일괄 삭제됩니다.
- `Authorization` 스킴은 대소문자를 구분하지 않습니다(`bearer`도 허용).
- 존재하지 않는 사용자로 로그인해도 더미 해시를 검증해서, 응답 시간으로 계정 존재 여부가 드러나지 않게 합니다.
- 수정·삭제는 `BEGIN IMMEDIATE` 트랜잭션 안에서 작성자를 확인한 뒤 수행합니다.
  403/404/422가 나는 경우에는 아무것도 쓰지 않습니다.
- 게시글 ID는 `AUTOINCREMENT`라서 삭제 후에도 재사용되지 않습니다.
- SQLite 정수 범위(2^63-1)를 넘는 `post_id`는 404, 범위를 넘는 `offset`은 422로 처리합니다.
- 인증이 필요한 API는 인증을 먼저 검사하므로, 토큰 없이 잘못된 본문을 보내면 422가 아니라 401이 납니다.

## 실행한 검사

```bash
.venv/Scripts/python.exe -m unittest discover -s tests -t . -v
```

환경에 pytest가 없어서 표준 `unittest`와 FastAPI `TestClient`를 사용했습니다. 결과는 **29개 모두 통과**했고,
같은 결과가 세 번 연속 재현되었습니다.

- `tests/test_api.py` (테스트마다 임시 DB 사용)
  - 회원가입: 201 응답 형태, 409 중복, username/password 경계값(3/32자, 8/128자)과 잘못된 문자·타입·`"abc\n"`에 대한 422
  - 비밀번호가 `$argon2…` 해시로 저장되고 응답에 나오지 않음
  - 로그인: 응답 형태, `expires_in` = 설정값(3600, 120), 잘못된 이름·비밀번호 401
  - 토큰마다 값이 다르고, DB 덤프에 토큰 원문이 없으며, 만료 시각이 TTL과 일치
  - 토큰 누락·형식 오류·위조·만료 시 401과 `WWW-Authenticate: Bearer` (POST/PUT/DELETE 모두)
  - 게시글: 공백 제거, 120/5000자 경계, 빈 값·공백만 있는 값·잘못된 타입·필드 누락·`author_id` 등 추가 필드에 대한 422,
    그리고 이때 DB가 바뀌지 않음
  - 목록: id 오름차순, 기본 limit 20, limit/offset 동작, 범위 밖 값 422
  - 수정·삭제: 작성자만 가능(200/204, 빈 본문), 다른 사용자는 403이고 DB 그대로, 없는 글은 404
  - 새 앱 인스턴스로 다시 열어도 회원·게시글·세션이 유지됨
  - `SESSION_TTL_SECONDS` 파싱(0, 음수, 소수, `+5`, `1_000`, 비ASCII 숫자는 거절)
- `tests/test_server.py`: 실제로 `python -m uvicorn main:app`을 하위 프로세스로 실행
  - `BOARD_DB_PATH`·`SESSION_TTL_SECONDS` 적용 확인, 서버를 끄고 다시 띄운 뒤 기존 토큰으로 수정 성공, 게시글·로그인 유지
  - `SESSION_TTL_SECONDS=0`이면 서버가 시작되지 않음

이 밖에 환경 변수 없이 직접 띄워서, 기본 경로에 `board.db`가 생기는 것과 회원가입·로그인·작성·401 헤더·목록 응답을 curl로 확인했습니다.
확인 후 그 DB 파일은 삭제했습니다.

## 남은 한계

- 로그아웃·토큰 폐기 API, 비밀번호 변경이 없습니다(요구 범위 밖). 세션은 만료될 때까지 유효합니다.
- username은 대소문자를 구분합니다(`Alice`와 `alice`는 서로 다른 계정).
- 요청 제한이 없어 로그인 무차별 대입에 대한 방어가 없습니다(요구 범위 밖). Argon2 검증이 CPU를 쓰므로 부하에도 취약할 수 있습니다.
- 사용자 삭제 기능이 없습니다. 스키마상 사용자를 지우면 그 사용자의 세션·게시글이 함께 삭제됩니다.
- 스키마 마이그레이션 도구가 없습니다. 테이블 구조를 바꾸려면 기존 DB를 직접 옮겨야 합니다.
- SQLite 단일 파일을 쓰므로 여러 서버 인스턴스로 수평 확장하는 용도에는 맞지 않습니다.
  동시 쓰기는 SQLite 잠금(timeout 10초)에 맡깁니다.
- 만료 판정은 서버 시계(`time.time()`)를 따르므로, 시계가 바뀌면 세션 수명도 함께 영향을 받습니다.
- `TestClient`를 import하면 Starlette의 httpx 관련 DeprecationWarning이 출력되지만 동작에는 영향이 없습니다.
