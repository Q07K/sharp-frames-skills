"""`python -m uvicorn main:app` 진입점."""

from board.app import create_app

app = create_app()
