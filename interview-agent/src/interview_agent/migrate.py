"""One-shot migration: users.json → SQLite."""

import json
import logging
from pathlib import Path

from interview_agent.db import create_user, get_db, init_db

logger = logging.getLogger(__name__)

_JSON_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "users.json"
_BAK_PATH = _JSON_PATH.with_suffix(".json.bak")


async def migrate_users_if_needed() -> None:
    if not _JSON_PATH.is_file():
        return

    await init_db()

    db = await get_db()
    try:
        async with db.execute("SELECT COUNT(*) as cnt FROM users") as cursor:
            row = await cursor.fetchone()
            if row and row["cnt"] > 0:
                logger.info("migrate: users table already has %d rows, skip", row["cnt"])
                return
    finally:
        await db.close()

    data = json.loads(_JSON_PATH.read_text(encoding="utf-8"))
    if not data:
        logger.info("migrate: users.json is empty, skip")
        return

    imported = 0
    for username, info in data.items():
        password_hash = info.get("password_hash", "")
        if not password_hash:
            logger.warning("migrate: skip user=%s (no password_hash)", username)
            continue
        try:
            await create_user(username, password_hash)
            imported += 1
        except Exception:
            logger.warning("migrate: failed to import user=%s", username, exc_info=True)

    if imported:
        _JSON_PATH.rename(_BAK_PATH)
        logger.info("migrate: imported %d users, backed up to %s", imported, _BAK_PATH)
    else:
        logger.info("migrate: no users imported")
