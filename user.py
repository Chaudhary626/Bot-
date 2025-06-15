from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from keyboards.reply import agreement_keyboard, next_task_keyboard, video_upload_keyboard
from utils.ai_moderation import moderate_text, moderate_image
from database.models import User, Video, DiscoveryType, TargetAction
from database.db import get_session
from sqlalchemy import select
from config import MAX_VIDEO_COUNT, MAX_VIDEO_DURATION

router = Router()

class VideoUploadFSM(StatesGroup):
    title = State()
    thumbnail = State()
    link = State()
    duration = State()
    discovery = State()
    actions = State()

@router.message(Command("start"))
async def start_cmd(msg: Message, state: FSMContext):
    await state.clear()
    text = (
        "Welcome to the YouTube Fair View Exchange Bot!\n\n"
        "Rules:\n"
        "- Only videos under 5 minutes are allowed.\n"
        "- Each user gets 20 minutes to complete tasks.\n"
        "- Give views to receive views (1:1, no cheating).\n"
        "- No fake proof, no misuse, no exceptions.\n\n"
        "Press ✅ I Agree to continue."
    )
    await msg.answer(text, reply_markup=agreement_keyboard())

@router.message(F.text == "✅ I Agree")
async def agree(msg: Message, state: FSMContext):
    # Register user if not exists
    async for session in get_session():
        u = await session.scalar(select(User).where(User.tg_user_id == msg.from_user.id))
        if not u:
            u = User(tg_user_id=msg.from_user.id, username=msg.from_user.username)
            session.add(u)
            await session.commit()
    await msg.answer("Please upload your YouTube video details.", reply_markup=video_upload_keyboard())
    await state.set_state(VideoUploadFSM.title)

@router.message(VideoUploadFSM.title)
async def video_title(msg: Message, state: FSMContext):
    if not moderate_text(msg.text):
        await msg.answer("Your title was blocked by AI moderation. Please use clean content.")
        return
    await state.update_data(title=msg.text)
    await msg.answer("Now send the video thumbnail image (required).")
    await state.set_state(VideoUploadFSM.thumbnail)

@router.message(VideoUploadFSM.thumbnail)
async def video_thumbnail(msg: Message, state: FSMContext):
    if not msg.photo:
        await msg.answer("Please send an image as thumbnail.")
        return
    file_id = msg.photo[-1].file_id
    if not moderate_image(file_id):
        await msg.answer("Thumbnail blocked by moderation, use a different image.")
        return
    await state.update_data(thumbnail=file_id)
    await msg.answer("Paste YouTube video link (or type 'skip').")
    await state.set_state(VideoUploadFSM.link)

@router.message(VideoUploadFSM.link)
async def video_link(msg: Message, state: FSMContext):
    link = msg.text if msg.text != "skip" else None
    await state.update_data(link=link)
    await msg.answer("How many seconds long is your video? (Max 300s)")
    await state.set_state(VideoUploadFSM.duration)

@router.message(VideoUploadFSM.duration)
async def video_duration(msg: Message, state: FSMContext):
    try:
        dur = int(msg.text)
    except Exception:
        await msg.answer("Please send duration as number of seconds (max 300).")
        return
    if dur > MAX_VIDEO_DURATION:
        await msg.answer("Video too long. Max allowed: 5 min (300s).")
        return
    await state.update_data(duration=dur)
    await msg.answer("How will users discover your video? (search/link/channel)")
    await state.set_state(VideoUploadFSM.discovery)

@router.message(VideoUploadFSM.discovery)
async def video_discovery(msg: Message, state: FSMContext):
    val = msg.text.lower()
    if val not in ['search', 'link', 'channel']:
        await msg.answer("Reply with one: search, link, channel.")
        return
    await state.update_data(discovery=val)
    await msg.answer("What actions should the viewer do? (like, comment, watch, subscribe; comma-separated)")
    await state.set_state(VideoUploadFSM.actions)

@router.message(VideoUploadFSM.actions)
async def video_actions(msg: Message, state: FSMContext):
    acts = [a.strip().lower() for a in msg.text.split(',')]
    allowed = {'like','comment','watch','subscribe'}
    if not set(acts).issubset(allowed):
        await msg.answer("Allowed actions: like, comment, watch, subscribe (comma-separated).")
        return
    data = await state.get_data()
    async for session in get_session():
        user = await session.scalar(select(User).where(User.tg_user_id == msg.from_user.id))
        videos = (await session.execute(select(Video).where(Video.owner_id == user.id))).scalars().all()
        if len(videos) >= MAX_VIDEO_COUNT:
            await msg.answer("You have reached the 5 video limit. Use /delete to remove a video before uploading.")
            await state.clear()
            return
        new_video = Video(
            owner_id=user.id,
            title=data['title'],
            thumbnail_file_id=data['thumbnail'],
            video_link=data['link'],
            duration=data['duration'],
            discovery_type=DiscoveryType[data['discovery']],
            target_actions=",".join(acts)
        )
        session.add(new_video)
        await session.commit()
    await msg.answer("Video saved! To receive views, complete someone else's task first. Click 'Next Task' when ready.", reply_markup=next_task_keyboard())
    await state.clear()

@router.message(Command("next"))
async def next_task(msg: Message, state: FSMContext):
    # Find an available video for the user (not their own, not their own previous tasks)
    # Set up a new task and send details
    await msg.answer("Task system coming soon...")  # Implemented in proof.py