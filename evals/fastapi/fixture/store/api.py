from fastapi import Depends, FastAPI, Header
from . import access, orders
from .auth import authenticate
from .db import session
from .schemas import BasketInput


def create_app(database_path: str) -> FastAPI:
    app = FastAPI()

    def database():
        with session(database_path) as connection:
            yield connection

    def current_actor(authorization: str | None = Header(default=None), connection=Depends(database)):
        return authenticate(connection, authorization)

    @app.get('/orders/{order_id}')
    def get_order(order_id: int, actor=Depends(current_actor), connection=Depends(database)):
        return dict(access.require_visible_order(connection, actor, order_id))

    @app.post('/orders', status_code=201)
    def place_order(basket: BasketInput, actor=Depends(current_actor), connection=Depends(database)):
        return orders.create_order(connection, actor, basket)

    return app
