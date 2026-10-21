# Case matrix

Personas: **anonymous** (no token), **author** (owns the post), **other user** (logged in, not owner).

## Auth

| Requirement | Persona / precondition | Expected | Test |
| --- | --- | --- | --- |
| Signup stores hashed password, public shape only | anonymous | 201, no hash in body, `$argon2` in DB | `test_auth.py::test_signup_returns_public_user_and_stores_hashed_password` |
| Username unique, case-insensitive | existing `alice` | 409, still 1 row | `test_signup_rejects_duplicate_username_case_insensitively` |
| Input bounds (username 3–30 `[A-Za-z0-9_]`, password 8–128) | anonymous | 422 | `test_signup_validates_input` |
| Login issues bearer token usable on `/auth/me` | registered user | 200 + token | `test_login_issues_token_usable_for_me` |
| Only token digest persisted | registered user | raw token absent from DB | `test_login_stores_only_token_hash` |
| Wrong password / unknown user indistinguishable | anonymous | 401, same body | `test_login_failure_is_indistinguishable` |
| Missing / unknown / non-Bearer token | anonymous | 401 + `WWW-Authenticate: Bearer` | `test_me_requires_valid_bearer_token` |
| Expired token rejected | user, session expiry in past | 401 | `test_expired_token_is_rejected` |
| Logout revokes current token only | user with 2 sessions | 204; first 401, second 200; 1 row left | `test_logout_revokes_only_that_token` |

## Posts

| Requirement | Persona / precondition | Expected | Test |
| --- | --- | --- | --- |
| Create → read → partial update → delete, persisted each step | author | 201/200/200/204, then 404; DB matches | `test_posts.py::test_author_crud_workflow_persists_each_step` |
| Author comes from token, client `author_id` ignored | author sends other's id | author = token user | `test_author_is_taken_from_token_not_request_body` |
| Only author may update/delete | other user | 403, DB unchanged | `test_other_user_cannot_modify_or_delete_post` |
| Writes need auth | anonymous | 401, DB unchanged | `test_writes_require_authentication` |
| Logged-out token cannot write | user after logout | 401 | `test_logged_out_token_cannot_write` |
| Missing post | any | 404 (GET/PATCH/DELETE) | `test_missing_post_returns_404` |
| Create validation (title trimmed 1–200, content 1–10000) | author | 422 | `test_create_validates_input` |
| Update needs ≥1 non-null valid field | author | 422 | `test_update_validates_input` |
| Public list, newest first, paginated with total | anonymous | ordered pages | `test_list_is_public_newest_first_and_paginated`, `test_list_empty` |
| Pagination bounds (limit 1–100, offset ≥ 0) | anonymous | 422 | `test_list_rejects_out_of_range_pagination` |

## Known gaps

- Concurrent update/delete races are handled by `WHERE id = ? AND author_id = ?` + rowcount, but no
  concurrency test exercises them. Revisit if a multi-worker deployment or stronger guarantees are needed.
- No rate limiting / brute-force lockout on login; expired session rows are not purged.
