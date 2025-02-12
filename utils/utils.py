from loader import db


async def is_admin(user_id: int) -> bool:
    admin = db.get_admin(user_id)
    return admin is not None
