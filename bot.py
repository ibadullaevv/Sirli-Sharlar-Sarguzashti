from __future__ import annotations

import asyncio
import logging
import time

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN, ADMIN_IDS, STAGES, ROUTE_VARIANTS, GAME_DURATION_MINUTES
import database as db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
router = Router()
dp.include_router(router)


# ============================================================
# FSM States
# ============================================================

class Registration(StatesGroup):
    waiting_team_name = State()
    waiting_members = State()


class Submission(StatesGroup):
    waiting_photo = State()
    waiting_video = State()
    waiting_code = State()


class AdminReject(StatesGroup):
    waiting_reason = State()


# ============================================================
# Helpers
# ============================================================

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def format_time(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def get_current_stage(team: dict) -> dict | None:
    idx = team["current_stage_index"]
    if idx >= len(team["route"]):
        return None
    stage_num = team["route"][idx]
    return STAGES[stage_num]


def get_current_stage_number(team: dict) -> int | None:
    idx = team["current_stage_index"]
    if idx >= len(team["route"]):
        return None
    return team["route"][idx]


async def send_stage_info(chat_id: int, team: dict):
    stage = get_current_stage(team)
    if stage is None:
        return
    stage_num = get_current_stage_number(team)
    idx = team["current_stage_index"]
    text = (
        f"{'='*30}\n"
        f"{stage['tasks']}\n"
        f"{'='*30}\n\n"
        f"📊 Bosqich: {idx + 1}/5\n"
        f"🏆 Joriy ball: {team['score']}/12\n\n"
        f"Tayyor bo'lgach, selfi yuboring 📸"
    )
    await bot.send_message(chat_id, text)


def build_leaderboard(teams: list[dict]) -> str:
    if not teams:
        return "Hali jamoalar ro'yxatdan o'tmagan."

    medals = ["🥇", "🥈", "🥉"]
    lines = ["🏆 <b>NATIJALAR JADVALI</b>\n"]
    for i, t in enumerate(teams):
        medal = medals[i] if i < 3 else f"{i+1}."
        elapsed = ""
        if t["is_finished"]:
            elapsed = f" — {format_time(t['finished_at'] - t['started_at'])}"
        elif t["started_at"]:
            elapsed = f" — {format_time(time.time() - t['started_at'])}"

        status = "✅" if t["is_finished"] else f"📍{t['current_stage_index']}/5"
        lines.append(
            f"{medal} <b>{t['name']}</b> — {t['score']} ball {status}{elapsed}"
        )
    return "\n".join(lines)


# ============================================================
# JAMOA KOMANDALARI
# ============================================================

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    team = await db.get_team_by_chat(message.chat.id)
    if team:
        await message.answer(
            f"Siz allaqachon <b>{team['name']}</b> jamoasi sifatida ro'yxatdan o'tgansiz.\n"
            f"Joriy ball: {team['score']}/12"
        )
        return

    await message.answer(
        "🎮 <b>SIRLI SHARLAR SARGUZASHTI</b>ga xush kelibsiz!\n\n"
        "Jamoangiz nomini kiriting:"
    )
    await state.set_state(Registration.waiting_team_name)


@router.message(Registration.waiting_team_name)
async def process_team_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2 or len(name) > 50:
        await message.answer("Jamoa nomi 2-50 belgi orasida bo'lishi kerak. Qaytadan kiriting:")
        return

    existing = await db.get_team_by_chat(message.chat.id)
    if existing:
        await message.answer("Siz allaqachon ro'yxatdan o'tgansiz!")
        await state.clear()
        return

    await state.update_data(team_name=name)
    await message.answer(
        f"Jamoa nomi: <b>{name}</b>\n\n"
        "Endi jamoa a'zolari ismlarini kiriting (vergul bilan):\n"
        "Misol: <i>Ali, Vali, Sardor, Nodira</i>"
    )
    await state.set_state(Registration.waiting_members)


@router.message(Registration.waiting_members)
async def process_members(message: Message, state: FSMContext):
    members = [m.strip() for m in message.text.split(",") if m.strip()]
    if len(members) < 3 or len(members) > 5:
        await message.answer("Jamoa 3-5 kishidan iborat bo'lishi kerak. Qaytadan kiriting:")
        return

    data = await state.get_data()
    team_name = data["team_name"]

    team_count = await db.get_team_count()
    route = ROUTE_VARIANTS[team_count % len(ROUTE_VARIANTS)]

    team_id = await db.register_team(message.chat.id, team_name, route)
    await db.set_team_members(message.chat.id, members)

    members_text = "\n".join(f"  • {m}" for m in members)
    await message.answer(
        f"✅ <b>{team_name}</b> jamoasi ro'yxatdan o'tdi!\n\n"
        f"A'zolar:\n{members_text}\n\n"
        f"Jamoa ID: <b>#{team_id}</b>\n"
        f"Marshrut: {' → '.join(str(s) for s in route)}\n\n"
        f"⏳ O'yin boshlanishini kuting...\n"
        f"Admin /startgame buyrug'ini bergach, sizga 1-topshiriq yuboriladi."
    )
    await state.clear()

    # Admin'larga xabar
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"🆕 Yangi jamoa ro'yxatdan o'tdi!\n"
                f"Nom: <b>{team_name}</b>\n"
                f"A'zolar: {', '.join(members)}\n"
                f"ID: #{team_id}"
            )
        except Exception:
            pass


@router.message(Command("myscore"))
async def cmd_myscore(message: Message):
    team = await db.get_team_by_chat(message.chat.id)
    if not team:
        await message.answer("Siz hali ro'yxatdan o'tmagan. /start bosing.")
        return

    elapsed = ""
    if team["started_at"]:
        if team["is_finished"]:
            elapsed = format_time(team["finished_at"] - team["started_at"])
        else:
            elapsed = format_time(time.time() - team["started_at"])

    stage_info = ""
    if team["is_finished"]:
        stage_info = "✅ Barcha bosqichlar tugatildi!"
    else:
        stage = get_current_stage(team)
        if stage:
            stage_info = f"📍 Joriy: {stage['name']}"

    await message.answer(
        f"📊 <b>{team['name']}</b>\n\n"
        f"Ball: <b>{team['score']}/12</b>\n"
        f"Bosqich: {team['current_stage_index']}/5\n"
        f"{stage_info}\n"
        f"Vaqt: {elapsed or 'Boshlanmagan'}"
    )


@router.message(Command("leaderboard"))
async def cmd_leaderboard(message: Message):
    teams = await db.get_all_teams()
    await message.answer(build_leaderboard(teams))


@router.message(Command("time"))
async def cmd_time(message: Message):
    team = await db.get_team_by_chat(message.chat.id)
    if not team or not team["started_at"]:
        await message.answer("O'yin hali boshlanmagan.")
        return

    elapsed = time.time() - team["started_at"]
    remaining = max(0, GAME_DURATION_MINUTES * 60 - elapsed)

    if remaining == 0:
        await message.answer("⏰ Vaqt tugagan!")
    else:
        await message.answer(
            f"⏱ O'tgan vaqt: {format_time(elapsed)}\n"
            f"⏳ Qolgan vaqt: {format_time(remaining)}"
        )


@router.message(Command("help"))
async def cmd_help(message: Message):
    if is_admin(message.from_user.id):
        await message.answer(
            "👨‍💼 <b>ADMIN BUYRUQLARI:</b>\n"
            "/startgame — O'yinni boshlash\n"
            "/endgame — O'yinni yakunlash\n"
            "/pending — Kutayotgan topshiriqlar\n"
            "/standings — To'liq natijalar\n"
            "/broadcast [xabar] — Hammaga xabar\n\n"
            "👥 <b>JAMOA BUYRUQLARI:</b>\n"
            "/start — Ro'yxatdan o'tish\n"
            "/myscore — Ballaringiz\n"
            "/leaderboard — Natijalar jadvali\n"
            "/time — Qolgan vaqt\n"
            "/submit — Topshiriq yuborish\n"
            "/help — Yordam"
        )
    else:
        await message.answer(
            "🎮 <b>BUYRUQLAR:</b>\n\n"
            "/start — Ro'yxatdan o'tish\n"
            "/myscore — Ballaringiz\n"
            "/leaderboard — Natijalar jadvali\n"
            "/time — Qolgan vaqt\n"
            "/submit — Topshiriq yuborish\n"
            "/help — Yordam"
        )


# ============================================================
# TOPSHIRIQ YUBORISH
# ============================================================

@router.message(Command("submit"))
async def cmd_submit(message: Message, state: FSMContext):
    game_active = await db.get_game_active()
    if not game_active:
        await message.answer("⏳ O'yin hali boshlanmagan. Kuting...")
        return

    team = await db.get_team_by_chat(message.chat.id)
    if not team:
        await message.answer("Avval /start bilan ro'yxatdan o'ting.")
        return

    if team["is_finished"]:
        await message.answer("✅ Siz barcha bosqichlarni tugatgansiz! Natijalarni kuting.")
        return

    stage = get_current_stage(team)
    stage_num = get_current_stage_number(team)
    await state.update_data(stage_number=stage_num, team_id=team["id"])

    await message.answer(
        f"📸 <b>{stage['name']}</b> uchun selfi/rasm yuboring.\n"
        f"(Agar selfi kerak bo'lmasa, /skip_photo yozing)"
    )
    await state.set_state(Submission.waiting_photo)


@router.message(Submission.waiting_photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_file_id=photo_id)
    await message.answer(
        "📸 Selfi qabul qilindi!\n\n"
        "🎥 Endi video yuboring.\n"
        "(Agar video kerak bo'lmasa, /skip_video yozing)"
    )
    await state.set_state(Submission.waiting_video)


@router.message(Submission.waiting_photo, Command("skip_photo"))
async def skip_photo(message: Message, state: FSMContext):
    await state.update_data(photo_file_id=None)
    await message.answer(
        "🎥 Video yuboring.\n"
        "(Agar video kerak bo'lmasa, /skip_video yozing)"
    )
    await state.set_state(Submission.waiting_video)


@router.message(Submission.waiting_video, F.video | F.video_note)
async def process_video(message: Message, state: FSMContext):
    video_id = message.video.file_id if message.video else message.video_note.file_id
    await state.update_data(video_file_id=video_id)
    await message.answer(
        "🎥 Video qabul qilindi!\n\n"
        "🔑 Endi maxfiy kodni yozing (Marbleverse'dan topgan kodingiz):"
    )
    await state.set_state(Submission.waiting_code)


@router.message(Submission.waiting_video, Command("skip_video"))
async def skip_video(message: Message, state: FSMContext):
    await state.update_data(video_file_id=None)
    await message.answer("🔑 Maxfiy kodni yozing (Marbleverse'dan topgan kodingiz):")
    await state.set_state(Submission.waiting_code)


@router.message(Submission.waiting_code, F.text)
async def process_code(message: Message, state: FSMContext):
    data = await state.get_data()
    team_id = data["team_id"]
    stage_number = data["stage_number"]
    secret_code = message.text.strip().upper()

    # Maxfiy kodni tekshirish
    expected_code = STAGES[stage_number]["secret_code"]
    if secret_code != expected_code:
        await message.answer(
            "❌ Maxfiy kod noto'g'ri! Qaytadan tekshirib yozing:\n"
            "(Marbleverse AR sharini toping va ichidagi kodni kiriting)"
        )
        return

    submission_id = await db.create_submission(
        team_id=team_id,
        stage_number=stage_number,
        photo_file_id=data.get("photo_file_id"),
        video_file_id=data.get("video_file_id"),
        secret_code=secret_code,
    )

    team = await db.get_team_by_id(team_id)
    stage = STAGES[stage_number]

    await message.answer(
        "✅ Topshiriq yuborildi! Admin tekshirmoqda...\n"
        "⏳ Biroz kuting."
    )

    # Admin'larga yuborish
    approve_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Tasdiqlash",
                callback_data=f"approve:{submission_id}"
            ),
            InlineKeyboardButton(
                text="❌ Rad etish",
                callback_data=f"reject:{submission_id}"
            ),
        ]
    ])

    for admin_id in ADMIN_IDS:
        try:
            admin_text = (
                f"📥 <b>YANGI TOPSHIRIQ</b>\n\n"
                f"Jamoa: <b>{team['name']}</b> (#{team_id})\n"
                f"Bosqich: {stage_number} — {stage['name']}\n"
                f"Kod: <code>{secret_code}</code> ✅\n"
                f"Yuborish ID: #{submission_id}"
            )
            await bot.send_message(admin_id, admin_text, reply_markup=approve_kb)

            if data.get("photo_file_id"):
                await bot.send_photo(admin_id, data["photo_file_id"],
                                     caption=f"📸 #{team['name']} — Bosqich {stage_number}")
            if data.get("video_file_id"):
                await bot.send_video(admin_id, data["video_file_id"],
                                     caption=f"🎥 #{team['name']} — Bosqich {stage_number}")
        except Exception as e:
            logger.error(f"Admin {admin_id} ga yuborishda xato: {e}")

    await state.clear()


# ============================================================
# ADMIN: TASDIQLASH / RAD ETISH
# ============================================================

@router.callback_query(F.data.startswith("approve:"))
async def callback_approve(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Sizda ruxsat yo'q!", show_alert=True)
        return

    submission_id = int(callback.data.split(":")[1])
    submission = await db.get_submission(submission_id)

    if not submission:
        await callback.answer("Topshiriq topilmadi!", show_alert=True)
        return
    if submission["status"] != "pending":
        await callback.answer("Bu topshiriq allaqachon ko'rib chiqilgan!", show_alert=True)
        return

    stage_number = submission["stage_number"]
    stage = STAGES[stage_number]
    team = await db.get_team_by_id(submission["team_id"])

    await db.update_submission_status(submission_id, "approved")
    await db.advance_team(team["id"], stage["ball"])

    # Admin xabarini yangilash
    await callback.message.edit_text(
        callback.message.text + f"\n\n✅ <b>TASDIQLANDI</b> — +{stage['ball']} ball",
    )
    await callback.answer("Tasdiqlandi!")

    # Jamoaga xabar
    updated_team = await db.get_team_by_id(team["id"])
    if updated_team["is_finished"]:
        elapsed = format_time(updated_team["finished_at"] - updated_team["started_at"])
        await bot.send_message(
            team["chat_id"],
            f"🎉🎉🎉 <b>TABRIKLAYMIZ!</b> 🎉🎉🎉\n\n"
            f"Barcha bosqichlar muvaffaqiyatli tugatildi!\n\n"
            f"📊 Yakuniy ball: <b>{updated_team['score']}/12</b>\n"
            f"⏱ Umumiy vaqt: <b>{elapsed}</b>\n\n"
            f"Natijalar e'lon qilinishini kuting!"
        )
        # Admin'larga xabar
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(
                    admin_id,
                    f"🏁 <b>{team['name']}</b> barcha bosqichlarni tugatdi!\n"
                    f"Ball: {updated_team['score']}/12 | Vaqt: {elapsed}"
                )
            except Exception:
                pass
    else:
        await bot.send_message(
            team["chat_id"],
            f"✅ <b>{stage_number}-BOSQICH TASDIQLANDI!</b>\n"
            f"+{stage['ball']} ball — Jami: {updated_team['score']}/12\n"
            f"Vaqt: {format_time(time.time() - updated_team['started_at'])}\n\n"
            f"Keyingi bosqich yuklanmoqda..."
        )
        await send_stage_info(team["chat_id"], updated_team)


@router.callback_query(F.data.startswith("reject:"))
async def callback_reject(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Sizda ruxsat yo'q!", show_alert=True)
        return

    submission_id = int(callback.data.split(":")[1])
    submission = await db.get_submission(submission_id)

    if not submission or submission["status"] != "pending":
        await callback.answer("Bu topshiriq allaqachon ko'rib chiqilgan!", show_alert=True)
        return

    await state.update_data(reject_submission_id=submission_id)
    await callback.message.answer("❌ Rad etish sababini yozing:")
    await state.set_state(AdminReject.waiting_reason)
    await callback.answer()


@router.message(AdminReject.waiting_reason, F.text)
async def process_reject_reason(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()
    submission_id = data["reject_submission_id"]
    reason = message.text.strip()

    submission = await db.get_submission(submission_id)
    if not submission:
        await message.answer("Topshiriq topilmadi!")
        await state.clear()
        return

    await db.update_submission_status(submission_id, "rejected", reason)

    team = await db.get_team_by_id(submission["team_id"])
    stage_number = submission["stage_number"]

    await message.answer(
        f"❌ #{submission_id} rad etildi.\n"
        f"Jamoa: {team['name']}\n"
        f"Sabab: {reason}"
    )

    # Jamoaga xabar
    await bot.send_message(
        team["chat_id"],
        f"❌ <b>TOPSHIRIQ RAD ETILDI</b>\n\n"
        f"Bosqich: {stage_number}\n"
        f"Sabab: <i>{reason}</i>\n\n"
        f"Qaytadan /submit bilan yuboring!"
    )
    await state.clear()


# ============================================================
# ADMIN BUYRUQLARI
# ============================================================

@router.message(Command("startgame"))
async def cmd_startgame(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("Sizda ruxsat yo'q!")
        return

    await db.set_game_active(True)
    teams = await db.get_all_teams()

    if not teams:
        await message.answer("❌ Hech qanday jamoa ro'yxatdan o'tmagan!")
        return

    await message.answer(
        f"🚀 <b>O'YIN BOSHLANDI!</b>\n"
        f"Jamoalar soni: {len(teams)}\n"
        f"Vaqt: {GAME_DURATION_MINUTES} daqiqa"
    )

    for team in teams:
        await db.start_team_timer(team["chat_id"])
        updated_team = await db.get_team_by_chat(team["chat_id"])
        try:
            await bot.send_message(
                team["chat_id"],
                f"🚀 <b>O'YIN BOSHLANDI!</b>\n\n"
                f"Vaqt: {GAME_DURATION_MINUTES} daqiqa\n"
                f"Marshrut: {' → '.join(str(s) for s in team['route'])}\n\n"
                f"Marbleverse appni oching va birinchi nuqtaga yuring!"
            )
            await send_stage_info(team["chat_id"], updated_team)
        except Exception as e:
            logger.error(f"Jamoa {team['name']} ga yuborishda xato: {e}")


@router.message(Command("endgame"))
async def cmd_endgame(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("Sizda ruxsat yo'q!")
        return

    await db.set_game_active(False)
    teams = await db.get_all_teams()
    leaderboard = build_leaderboard(teams)

    result_text = (
        f"🏁 <b>O'YIN YAKUNLANDI!</b>\n\n"
        f"{leaderboard}\n\n"
    )

    if teams:
        winner = teams[0]
        result_text += f"🏆 G'olib: <b>{winner['name']}</b> — {winner['score']} ball!"

    # Hammaga yuborish
    for team in teams:
        try:
            await bot.send_message(team["chat_id"], result_text)
        except Exception:
            pass

    await message.answer(result_text)


@router.message(Command("pending"))
async def cmd_pending(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("Sizda ruxsat yo'q!")
        return

    submissions = await db.get_pending_submissions()
    if not submissions:
        await message.answer("✅ Kutayotgan topshiriqlar yo'q.")
        return

    for sub in submissions:
        stage = STAGES[sub["stage_number"]]
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve:{sub['id']}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject:{sub['id']}"),
            ]
        ])
        await message.answer(
            f"📥 #{sub['id']} — <b>{sub['team_name']}</b>\n"
            f"Bosqich: {sub['stage_number']} — {stage['name']}\n"
            f"Kod: <code>{sub['secret_code']}</code>",
            reply_markup=kb,
        )
        if sub["photo_file_id"]:
            await bot.send_photo(message.chat.id, sub["photo_file_id"])
        if sub["video_file_id"]:
            await bot.send_video(message.chat.id, sub["video_file_id"])


@router.message(Command("standings"))
async def cmd_standings(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("Sizda ruxsat yo'q!")
        return

    teams = await db.get_all_teams()
    if not teams:
        await message.answer("Hali jamoalar yo'q.")
        return

    lines = ["📊 <b>TO'LIQ NATIJALAR</b>\n"]
    for i, t in enumerate(teams, 1):
        elapsed = ""
        if t["is_finished"]:
            elapsed = format_time(t["finished_at"] - t["started_at"])
        elif t["started_at"]:
            elapsed = format_time(time.time() - t["started_at"])

        finished = "✅ TUGATDI" if t["is_finished"] else f"Bosqich {t['current_stage_index']}/5"
        members = ", ".join(t["members"]) if t["members"] else "—"
        lines.append(
            f"{i}. <b>{t['name']}</b>\n"
            f"   Ball: {t['score']}/12 | {finished}\n"
            f"   Vaqt: {elapsed or '—'}\n"
            f"   A'zolar: {members}\n"
        )
    await message.answer("\n".join(lines))


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("Sizda ruxsat yo'q!")
        return

    text = message.text.replace("/broadcast", "", 1).strip()
    if not text:
        await message.answer("Xabar matni kerak: /broadcast Xabar matni")
        return

    teams = await db.get_all_teams()
    sent = 0
    for team in teams:
        try:
            await bot.send_message(team["chat_id"], f"📢 <b>E'LON:</b>\n\n{text}")
            sent += 1
        except Exception:
            pass

    await message.answer(f"✅ {sent}/{len(teams)} jamoaga yuborildi.")


# ============================================================
# MAIN
# ============================================================

async def main():
    await db.init_db()
    logger.info("Bot ishga tushdi!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
