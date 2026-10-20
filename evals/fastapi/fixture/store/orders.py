from dataclasses import asdict
from fastapi import HTTPException
from .settlement import price_basket


def create_order(connection, actor, basket):
    with connection:
        totals = price_basket(connection, actor, basket)
        cursor = connection.execute('INSERT INTO orders(tenant_id, owner_id, status, total_won) VALUES (?, ?, ?, ?)', (actor.tenant_id, actor.id, 'paid', totals.total_won))
        order_id = cursor.lastrowid
        for line in basket.lines:
            changed = connection.execute('UPDATE products SET stock = stock - ? WHERE sku = ? AND stock >= ?', (line.quantity, line.sku, line.quantity)).rowcount
            if changed != 1:
                raise HTTPException(409, 'Insufficient stock')
            connection.execute('INSERT INTO order_lines VALUES (?, ?, ?)', (order_id, line.sku, line.quantity))
        return {'id': order_id, **asdict(totals)}
