# FastAPI 게시글 API

작은 게시판 API를 새로 구현해 주세요. 실제로 실행되고 SQLite에 저장돼야 합니다.
Python 3.12 이상, FastAPI, Pydantic, SQLite와 제공된 requirements 환경을 사용합니다.
폴더 구조와 내부 구현은 작업 크기에 맞게 선택하세요.

## 실행·설정

- 프로젝트 루트에서 `python -m uvicorn main:app`로 시작합니다.
- `BOARD_DB_PATH` 환경 변수로 SQLite 파일 경로를 지정합니다. 기본값도 제공하세요.
- `SESSION_TTL_SECONDS`는 양의 정수이며 세션 수명입니다. 기본은 3600초입니다.
- 서버를 재시작해도 회원·게시글·만료되지 않은 세션은 유지돼야 합니다.
- 프로젝트의 실행법과 확인한 검사·남은 한계를 README에 적어 주세요.

## 회원과 세션

- `POST /auth/register`: JSON `{username, password}`. username은 영문·숫자·밑줄 3~32자,
  password는 8~128자입니다. 성공은 201 `{id, username}`, 중복 이름은 409입니다.
- `POST /auth/login`: 같은 JSON 입력. 성공은 200
  `{access_token, token_type: "bearer", expires_in}`이며 expires_in은 설정한 세션 수명입니다.
- 잘못된 이름/비밀번호는 401입니다. 비밀번호는 Argon2 해시로 저장하고 공개하지 않습니다.
- 무작위 Bearer 세션 토큰을 발급하며 DB에는 토큰 원문 대신 지문과 만료 시각을 저장합니다.
- 쓰기 API는 `Authorization: Bearer <access_token>`으로 인증합니다.
  누락·위조·만료 토큰은 401이며 `WWW-Authenticate: Bearer` 헤더를 보냅니다.
- 작성자 ID는 인증한 사용자로 정하고 클라이언트가 지정할 수 없습니다.

## 게시글

게시글 공개 응답은 `{id, title, content, author_id}`입니다. ID는 정수입니다.
제목은 앞뒤 공백 제거 후 1~120자, 본문은 앞뒤 공백 제거 후 1~5000자입니다.
작성·수정 입력은 `{title, content}`이며 `author_id` 등 추가 필드는 422로 거절합니다.

| API | 응답·권한 |
| --- | --- |
| `POST /posts` | 로그인 필요. 201과 생성된 게시글 |
| `GET /posts` | 공개. 게시글 배열. id 오름차순, limit 기본 20/1~100, offset 기본 0/0 이상 |
| `GET /posts/{post_id}` | 공개. 200과 게시글, 없으면 404 |
| `PUT /posts/{post_id}` | 작성자만 제목·본문 전체 수정. 200과 수정된 게시글 |
| `DELETE /posts/{post_id}` | 작성자만 삭제. 204, 빈 응답 본문 |

로그인한 다른 작성자의 수정·삭제는 403이며 데이터가 바뀌면 안 됩니다.
로그인한 사용자가 존재하지 않는 게시글을 수정·삭제하면 404입니다.
잘못된 입력·페이지 범위는 422이며 저장 상태에 영향을 주면 안 됩니다.

## 범위

회원가입·로그인·CRUD·작성자 권한·입력 검증·저장과 재시작이 이번 범위입니다.
브라우저 UI, 외부 인증 제공자, 이메일 인증, 비밀번호 재설정, 배포, 요청 제한은 범위 밖입니다.
필요한 검사를 직접 작성·실행해 주세요. 제공된 요구사항·requirements는 변경하지 마세요.
