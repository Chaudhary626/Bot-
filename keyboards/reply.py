from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def agreement_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="✅ I Agree")]
    ], resize_keyboard=True)

def video_upload_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Upload Video Details")]
    ], resize_keyboard=True)

def next_task_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Next Task")]
    ], resize_keyboard=True)

def proof_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 I Watched the Complete Video", callback_data="watched_video")]
    ])

def accept_reject_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Accept", callback_data="accept_proof"),
         InlineKeyboardButton(text="❌ Reject", callback_data="reject_proof")],
    ])

def step_confirm_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Yes, I completed all steps", callback_data="steps_yes"),
         InlineKeyboardButton(text="⚠ I skipped some steps", callback_data="steps_skipped")]
    ])
