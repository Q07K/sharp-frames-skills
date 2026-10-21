# Case matrix

Requirement source: `REQUIREMENTS.md`. All tests go through the real FastAPI app and a
temporary SQLite file; nothing in auth, validation or persistence is mocked. Session
expiry uses an injected clock (`create_app(clock=...)`) instead of sleeping.

| Requirement | Cases (boundaries / roles / state) | Tests |
| --- | --- | --- |
| Register 201 `{id, username}`, duplicate 409 | public shape only; duplicate leaves 1 row | `test_auth.RegisterTests` |
| username `[A-Za-z0-9_]` 3–32, password 8–128 | 3/32 vs 2/33, `-`, space, Hangul, 8/128 vs 7/129, missing, non-string → 422; no rows written | `RegisterTests.test_username_and_password_boundaries` |
| Argon2 hash, never exposed | stored value starts `$argon2`, response lacks it | `RegisterTests.test_register_returns_public_user_and_stores_argon2_hash` |
| Login 200 `{access_token, token_type, expires_in}` | expires_in = configured TTL; distinct tokens per login | `test_auth.LoginTests` |
| Token fingerprint + expiry stored, not raw token | DB row has sha256(token), not token; expires_at = now + TTL | `LoginTests.test_login_issues_bearer_token_and_stores_only_fingerprint` |
| Wrong name/password 401 | wrong password, unknown user; no session created | `LoginTests.test_wrong_password_or_unknown_user_is_401` |
| Missing/forged/expired token 401 + `WWW-Authenticate: Bearer` | no header, no scheme, Basic, empty, forged, altered; TTL-1s ok / TTL expired | `test_auth.BearerAuthTests`, `UpdateDeletePostTests.test_write_endpoints_require_authentication` |
| Author from token; client `author_id`/extra fields 422 | create sets author; `author_id`, `id` rejected on POST and PUT | `CreatePostTests`, `UpdateDeletePostTests.test_update_requires_full_body_and_rejects_extra_fields` |
| Title 1–120 / content 1–5000 after trim | whitespace-only, 0/121, 0/5001, padded max length ok, null, number, missing, malformed JSON | `CreatePostTests.test_title_and_content_length_boundaries_after_trimming`, `test_malformed_json_body_is_422` |
| `GET /posts` public, id asc, limit 1–100 default 20, offset ≥ 0 | 25 posts by 2 authors; default, 1, 100, offset middle/last/past end; 0, 101, -1, text, huge offset → 422 | `ReadPostTests` |
| `GET /posts/{id}` 200 / 404 | missing, 0, negative, beyond int64 → 404; non-integer → 422 | `ReadPostTests` |
| PUT/DELETE author only; other user 403 and unchanged; missing 404 | owner edits (persisted), owner deletes (204 empty body, then 404), other user 403 with DB unchanged, logged-in user on missing id 404 | `test_posts.UpdateDeletePostTests` |
| Invalid input does not change state | every 422/401/403 case compares DB rows before/after | throughout `test_posts`, `test_auth` |
| Restart keeps users, posts, unexpired sessions | two authors + visitor journey, app restarted on same DB, old token still works, expired-during-downtime token rejected | `test_workflow.TwoAuthorJourneyTests` |
| `python -m uvicorn main:app`, `BOARD_DB_PATH`, `SESSION_TTL_SECONDS` | real uvicorn process started twice on one DB file; settings defaults, env values, invalid TTL (0, negative, decimal, text, empty) | `test_workflow.UvicornEntryPointTests`, `test_workflow.SettingsTests` |

## Not covered

- Truly concurrent requests (e.g. delete racing an update); handled by the rowcount
  check in `board/posts.py`, but no test drives two simultaneous requests.
- Browser clients — the project has no UI.
