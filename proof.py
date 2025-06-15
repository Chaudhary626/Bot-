from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from keyboards.reply import proof_keyboard, accept_reject_keyboard, step_confirm_keyboard
from utils.ai_moderation import moderate_proof
from database.models import Task, Video, User, Proof, TaskStatus
from database.db import get_session
from sqlalchemy import select, and_
from config import TASK_TIMEOUT_MINUTES

router = Router()

@router.message(F.text == "Next Task")
@router.message(Command("next"))
async def assign_task(msg: Message):
    user_id = msg.from_user.id
    async for session in get_session():
        user = await session.scalar(select(User).where(User.tg_user_id == user_id))
        # Find an open video, not owned by this user, not currently processing, not already given to this user
        video = (await session.execute(
            select(Video).where(
                and_(
                    Video.owner_id != user.id,
                    Video.is_open == True,
                    Video.is_processing == False
                )
            )
        )).scalars().first()
        if not video:
            await msg.answer("No available tasks right now. Try again later.")
            return
        # Mark as processing
        video.is_processing = True
        # Create a new Task
        task = Task(
            video_id=video.id,
            giver_id=user.id,
            receiver_id=video.owner_id,
            status=TaskStatus.pending
        )
        session.add(task)
        await session.commit()
        # Send video details to user
        actions = video.target_actions.replace(",", ", ")
        await msg.answer_photo(
            video.thumbnail_file_id,
            caption=f"Title: {video.title}\nLink: {video.video_link}\nDuration: {video.duration}s\nDiscovery: {video.discovery_type.value}\nActions: {actions}\n\nAfter watching, click below:",
            reply_markup=proof_keyboard()
        )

@router.callback_query(F.data == "watched_video")
async def watched_video_callback(call: CallbackQuery, state: FSMContext):
    await call.message.answer("Upload screen recording or screenshot as proof you watched and completed all steps.")
    await state.set_data({"awaiting_proof": True})

@router.message(lambda m, state: state.get_data().get("awaiting_proof", False))
async def handle_proof_upload(msg: Message, state: FSMContext):
    # Only accept photo/video as proof
    if not (msg.photo or msg.video):
        await msg.answer("Send a screenshot or screen recording as proof (photo/video).")
        return
    file_id = msg.photo[-1].file_id if msg.photo else msg.video.file_id
    if not moderate_proof(file_id):
        await msg.answer("Proof failed AI moderation. Please send valid proof.")
        return
    # Find user's pending task
    async for session in get_session():
        user = await session.scalar(select(User).where(User.tg_user_id == msg.from_user.id))
        task = (await session.execute(
            select(Task).where(
                and_(Task.giver_id == user.id, Task.status == TaskStatus.pending)
            )
        )).scalars().first()
        if not task:
            await msg.answer("No pending task found.")
            await state.clear()
            return
        # Save proof
        proof = Proof(
            task_id=task.id,
            file_id=file_id,
            submitted_by=user.id
        )
        session.add(proof)
        task.status = TaskStatus.proof_submitted
        await session.commit()
        # Notify video owner for review
        receiver = await session.scalar(select(User).where(User.id == task.receiver_id))
        await msg.bot.send_message(
            receiver.tg_user_id,
            f"User submitted proof for your video.\nReview and accept/reject within {TASK_TIMEOUT_MINUTES} min.",
            reply_markup=accept_reject_keyboard()
        )
    await msg.answer("Proof submitted. Waiting for video owner review.")
    await state.clear()

@router.callback_query(F.data.in_(["accept_proof", "reject_proof"]))
async def owner_review_proof(call: CallbackQuery):
    # Get the task and proof
    async for session in get_session():
        # For simplicity, get most recent proof submitted for this owner
        user = await session.scalar(select(User).where(User.tg_user_id == call.from_user.id))
        task = (await session.execute(
            select(Task).where(
                and_(Task.receiver_id == user.id, Task.status == TaskStatus.proof_submitted)
            )
        )).scalars().first()
        if not task:
            await call.message.answer("No pending proofs to review.")
            return
        if call.data == "accept_proof":
            task.status = TaskStatus.accepted
            task.video.is_processing = False
            await session.commit()
            # Notify both users
            giver = await session.scalar(select(User).where(User.id == task.giver_id))
            await call.message.bot.send_message(giver.tg_user_id, "Your proof was accepted! You earned a view.")
            await call.message.answer("Proof accepted. Task completed.")
        else:
            task.status = TaskStatus.rejected
            task.video.is_processing = False
            await session.commit()
            giver = await session.scalar(select(User).where(User.id == task.giver_id))
            await call.message.bot.send_message(giver.tg_user_id, "Your proof was rejected. Reason required.\nUse /report if unfair.")
            await call.message.answer("Proof rejected. Please specify which step was skipped or issue.")

# Add more: /close, /open, /myvideos, /delete, /report, step confirmations, etc.