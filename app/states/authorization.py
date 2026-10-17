import reflex as rx
import logging
from reflex_enterprise.auth import AuthContext
from sqlalchemy import select
from app.models import StoreMember


async def is_admin(ctx: AuthContext) -> bool:
    try:
        subject = ctx.auth_user_state.userinfo.get("sub", "")
        if (
            not isinstance(subject, str)
            or not subject.strip()
            or len(subject) > 255
        ):
            return False
        async with rx.asession() as session:
            return (
                await session.scalar(
                    select(StoreMember.id)
                    .where(
                        StoreMember.subject == subject,
                        StoreMember.role == "admin",
                        StoreMember.admin_slot == 1,
                    )
                    .limit(1)
                )
                is not None
            )
    except Exception as e:
        logging.exception(f"Error: {e}")
        return False
