# 공통 API 계약과 사용자 흐름

두 버전에 같은 요구를 적용합니다. 아래 ID는 test_contract.py의 unittest 메서드 이름입니다.
단순한 상태 코드 확인 외에 후속 조회와 저장 상태를 확인합니다.

| ID | 사용자·연속 행동 | 기대 계약 |
| --- | --- | --- |
| `test_register_login_and_wrong_password` | 가입 → 로그인 → 중복 가입·잘못된 로그인 → 기존 토큰으로 작성 | 201/200, 중복 409, 실패 401, 공개 응답에 비밀번호 없음, DB에는 비밀번호 해시·토큰 지문 |
| `test_author_crud_workflow` | 로그인 → 작성 → 목록·상세 조회 → 수정 → 재조회 → 삭제 → 재조회 | 작성자 ID 유지, 공백 정리, 수정 내용 저장, 삭제 204/빈 본문, 이후 404·빈 목록 |
| `test_anonymous_writes_are_rejected` | 작성된 글에 익명 작성·수정·삭제 시도 → 재조회 | 쓰기 401, 기존 글 보존 |
| `test_other_author_is_denied_without_side_effects` | Alice 작성 → Bob 로그인 → 수정·삭제 시도 → 재조회 → Alice 삭제 | Bob 403, 내용 보존, Alice 삭제 가능 |
| `test_invalid_and_expired_tokens` | 위조 토큰 작성 → 기존 세션 만료 → 삭제 시도 → 재조회 | 401, 게시글 보존 |
| `test_input_validation_and_pagination` | 빈 값·길이 초과·author_id 주입 → 목록 → 정상 두 글 → 페이지 조회 | 422, 잘못된 입력 미저장, 순서·페이지 경계 보존 |
| `test_missing_post_is_not_found` | 존재하지 않는 ID를 조회·수정·삭제 | 404 |
| `test_database_survives_app_restart` | 가입·작성 → 같은 DB로 새 앱 시작 → 조회·삭제 | 글과 유효한 세션 유지 |
| `test_failed_write_does_not_persist_and_retry_works` | DB 트리거로 INSERT 실패 주입 → 목록 → 장애 제거 → 재시도 | 500, 부분 저장 없음, 재시도 성공 |

실행일·환경·결과와 미측정 항목은 [예제 설명](../README.md)에 기록합니다.
브라우저·실제 운영 DB 동시성·인증 제공자·운영 배포를 검증하는 테스트는 아닙니다.
