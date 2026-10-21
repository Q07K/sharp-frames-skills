# Board API (FastAPI)

로그인(토큰 인증)과 게시글 CRUD를 제공하는 FastAPI 서버입니다. 저장소는 SQLite입니다.

## 실행

```bash
.venv/Scripts/python.exe -m uvicorn app.main:app --reload
```

- Swagger UI: http://127.0.0.1:8000/docs (우측 상단 **Authorize**에 로그인으로 받은 토큰 입력)
- 환경 변수
  - `DATABASE_PATH` (기본값 `app.db`)
  - `TOKEN_TTL_MINUTES` (기본값 `60`)

## 테스트

```bash
.venv/Scripts/python.exe -m pytest -q
```

## API

| Method | Path | 인증 | 설명 |
|---|---|---|---|
| POST | `/auth/signup` | - | 회원가입 `{username, password}` |
| POST | `/auth/login` | - | 로그인 → `{access_token, token_type, expires_at}` |
| POST | `/auth/logout` | Bearer | 현재 토큰 폐기 |
| GET | `/auth/me` | Bearer | 내 정보 |
| GET | `/posts?limit=&offset=&author_id=` | - | 목록 (최신순, 페이지네이션) |
| GET | `/posts/{id}` | - | 상세 |
| POST | `/posts` | Bearer | 작성 `{title, content}` |
| PATCH | `/posts/{id}` | Bearer (작성자) | 부분 수정 |
| DELETE | `/posts/{id}` | Bearer (작성자) | 삭제 |

인증 헤더: `Authorization: Bearer <access_token>`

## 설계 메모

- 비밀번호는 `pwdlib`(Argon2)로 해시합니다.
- 토큰은 JWT 대신 무작위 문자열(opaque token)이며, DB에는 SHA-256 해시만 저장합니다.
  덕분에 로그아웃 시 즉시 무효화됩니다.
- 수정·삭제는 작성자만 가능합니다(타인은 403).
