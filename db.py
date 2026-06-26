import re
import asyncpg

_SAFE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


async def update_status(
    dsn: str,
    table: str,
    column: str,
    value: str | int,
    record_id: int,
) -> bool:
    """
    UPDATE {table} SET {column} = $1 WHERE id = $2.
    Returns True when the record was found and updated, False when not found.
    Table/column names are validated against a safe-identifier pattern.
    Values and IDs are always parameterised — no SQL injection risk.
    """
    if not _SAFE.match(table):
        raise ValueError(f"Unsafe table name: {table!r}")
    if not _SAFE.match(column):
        raise ValueError(f"Unsafe column name: {column!r}")

    conn = await asyncpg.connect(dsn)
    try:
        result = await conn.execute(
            f"UPDATE {table} SET {column} = $1 WHERE id = $2",
            value,
            record_id,
        )
        # asyncpg returns "UPDATE <n>" where n is the number of affected rows
        return result == "UPDATE 1"
    finally:
        await conn.close()
