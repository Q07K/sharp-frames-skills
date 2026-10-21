# Board API

로그인(세션 토큰)과 게시글 CRUD를 제공하는 FastAPI 서비스. 저장소는 SQLite(표준 `sqlite3`).

## 실행

```sh
DATABASE_PATH=app.db .venv/Scripts/python.exe -m uvicorn app.main:create_app_from_env --factory --reload
```

API 문서: http://127.0.0.1:8000/docs

## 테스트

```sh
.venv/Scripts/python.exe -m pytest
```

케이스 목록은 [tests/CASE_MATRIX.md](tests/CASE_MATRIX.md).

## API

| Method | Path | 인증 | 설명 |
| --- | --- | --- | --- |
| POST | `/auth/signup` | - | 회원가입 `{username, password}` → 201, 중복 409 |
| POST | `/auth/login` | - | `{username, password}` → `{access_token, token_type, expires_at}`, 실패 401 |
| POST | `/auth/logout` | Bearer | 현재 토큰만 폐기 → 204 |
| GET | `/auth/me` | Bearer | 현재 사용자 |
| GET | `/posts?limit=20&offset=0` | - | 최신순 목록 `{items, total, limit, offset}` (limit 1–100) |
| GET | `/posts/{id}` | - | 단건 조회, 없으면 404 |
| POST | `/posts` | Bearer | `{title, content}` → 201. 작성자는 토큰의 사용자 |
| PATCH | `/posts/{id}` | Bearer | 부분 수정. 작성자만(403), 없으면 404 |
| DELETE | `/posts/{id}` | Bearer | 작성자만(403) → 204 |

## 설계 메모

- **토큰**: JWT 라이브러리가 환경에 없어, 32바이트 랜덤 불투명 토큰을 발급하고 DB에는 SHA-256
  digest만 저장한다. 서버 측 세션이라 로그아웃 시 즉시 폐기된다. 유효기간 기본 24시간
  (`create_app(token_ttl=...)`).
- **비밀번호**: `pwdlib` Argon2. 존재하지 않는 사용자 로그인도 동일한 해시 검증 비용을 치러
  응답 시간으로 가입 여부가 드러나지 않게 한다.
- **로그인 바디는 JSON**: `python-multipart`가 없어 OAuth2 form 로그인은 쓰지 않는다.
  따라서 Swagger UI의 "Authorize" 버튼에는 로그인 응답의 토큰을 직접 붙여 넣는다.
- 사용자명은 대소문자 무시 유일(`UNIQUE COLLATE NOCASE`) — DB 제약이 동시 가입 경쟁을 막는다.
- 읽기는 공개, 쓰기는 인증 필요, 수정·삭제는 작성자 본인만 가능하다(관리자 역할 없음).
