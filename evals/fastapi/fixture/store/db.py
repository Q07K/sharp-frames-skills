import sqlite3
from contextlib import contextmanager
from pathlib import Path


def connect(path: str):
    connection = sqlite3.connect(path, timeout=10, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def session(path: str):
    connection = connect(path)
    try:
        yield connection
    finally:
        connection.close()


def initialize(path: str):
    with session(path) as connection:
        connection.executescript("""
        CREATE TABLE users(id INTEGER PRIMARY KEY, tenant_id INTEGER NOT NULL,
            role TEXT NOT NULL, tier TEXT NOT NULL, token TEXT UNIQUE NOT NULL);
        CREATE TABLE products(sku TEXT PRIMARY KEY, price_won INTEGER NOT NULL,
            stock INTEGER NOT NULL CHECK(stock >= 0));
        CREATE TABLE orders(id INTEGER PRIMARY KEY, tenant_id INTEGER NOT NULL,
            owner_id INTEGER NOT NULL REFERENCES users(id), status TEXT NOT NULL,
            total_won INTEGER NOT NULL);
        CREATE TABLE order_lines(order_id INTEGER NOT NULL REFERENCES orders(id),
            sku TEXT NOT NULL REFERENCES products(sku), quantity INTEGER NOT NULL);
        CREATE TABLE stock_movements(id INTEGER PRIMARY KEY, order_id INTEGER NOT NULL,
            sku TEXT NOT NULL, quantity INTEGER NOT NULL, reason TEXT NOT NULL);
        CREATE TABLE cancel_requests(user_id INTEGER NOT NULL, request_key TEXT NOT NULL,
            order_id INTEGER NOT NULL, response_json TEXT NOT NULL,
            PRIMARY KEY(user_id, request_key));
        INSERT INTO users VALUES
            (1, 101, 'member', 'vip', 'alice'),
            (2, 202, 'member', 'regular', 'bob'),
            (3, 101, 'manager', 'regular', 'manager'),
            (4, 101, 'member', 'regular', 'charlie');
        INSERT INTO products VALUES ('A', 1001, 10), ('B', 2503, 8);
        INSERT INTO orders VALUES
            (10, 101, 1, 'paid', 8000), (11, 101, 1, 'paid', 9000),
            (12, 101, 4, 'paid', 7000), (20, 202, 2, 'paid', 6000);
        INSERT INTO order_lines VALUES (10, 'A', 2), (11, 'B', 1),
            (12, 'A', 1), (20, 'A', 1);
        """)
