from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from config import ADMIN_IDS
from database.db import get_session
from database.models import User, Video, Task, Dispute
from sqlalchemy import select

router = Router()

@router.message(Command("admin"))
async def admin_dashboard(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("Access denied.")
        return
    # Show basic admin stats
    async for session in get_session():
        users = (await session.execute(select(User))).scalars().all()
        videos = (await session.execute(select(Video))).scalars().all()
        tasks = (await session.execute(select(Task))).scalars().all()
        disputes = (await session.execute(select(Dispute))).scalars().all()
        stats = (
            f"Admin Dashboard\n\n"
            f"Total Users: {len(users)}\n"
            f"Total Videos: {len(videos)}\n"
            f"Total Tasks: {len(tasks)}\n"
            f"Open Disputes: {len([d for d in disputes if not d.resolved])}"
        )
        await msg.answer(stats)
    # Add more admin features as needed