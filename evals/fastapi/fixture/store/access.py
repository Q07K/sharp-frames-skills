from fastapi import HTTPException


def visibility_clause(actor):
    if actor.role == 'manager':
        return 'tenant_id = ?', (actor.tenant_id,)
    return 'tenant_id = ? AND owner_id = ?', (actor.tenant_id, actor.id)


def require_visible_order(connection, actor, order_id: int):
    clause, values = visibility_clause(actor)
    row = connection.execute(f"SELECT * FROM orders WHERE id = ? AND ({clause})", (order_id, *values)).fetchone()
    if row is None:
        raise HTTPException(404, "Order not found")
    return row
