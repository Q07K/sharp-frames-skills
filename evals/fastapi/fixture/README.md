# Store API evaluation fixture

Small existing FastAPI application with SQLite. This is synthetic, not production.
Create databases with `store.db.initialize(path)` and apps with `store.api.create_app(path)`.
Bearer alice/bob/manager/charlie are fixture tokens; no external services.
Run `python -m unittest discover -s tests -v` with the supplied dependency path.
Keep existing API contracts and unrelated behavior. Add implementation and useful checks.
