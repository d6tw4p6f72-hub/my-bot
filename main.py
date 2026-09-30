import datetime
import os
import random

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from content import CHALLENGES, SECTIONS, TIPS, WORKOUTS

CHANNEL_URL = os.environ.get("CHANNEL_URL", "https://t.me/pitaisyasgolovoi")
GROUP_URL = os.environ.get("GROUP_URL")
ADMIN_ID = os.environ.get("ADMIN_ID")
CHANNEL_ID = os.environ.get("CHANNEL_ID") or os.environ.get("GROUP_ID")
GROUP_CHAT_ID = os.environ.get("GROUP_CHAT_ID")
WATER_GOAL = 2000

ACTIVITY = {1: 1.2, 2: 1.375, 3: 1.55, 4: 1.725}


def to_chat_id(value):
    return int(value) if value.lstrip("-").isdigit() else value


# ---------- Меню ----------

def main_menu():
    rows = [
        [InlineKeyboardButton(s["title"], callback_data=f"s:{key}")]
        for key, s in SECTIONS.items()
    ]
    rows.append(
        [
            InlineKeyboardButton("💡 Совет дня", callback_data="tip"),
            InlineKeyboardButton("🏃 Тренировка дня", callback_data="workout"),
        ]
    )
    rows.append(
        [
            InlineKeyboardButton("🧮 Калории", callback_data="info:calc"),
            InlineKeyboardButton("💧 Вода", callback_data="info:water"),
        ]
    )
    links = [InlineKeyboardButton("📢 Наш канал", url=CHANNEL_URL)]
    if GROUP_URL:
        links.append(InlineKeyboardButton("💬 Наша группа", url=GROUP_URL))
    rows.append(links)
    return InlineKeyboardMarkup(rows)


def section_menu(key):
    rows = [
        [InlineKeyboardButton(a["title"], callback_data=f"a:{key}:{i}")]
        for i, a in enumerate(SECTIONS[key]["articles"])
    ]
    rows.append([InlineKeyboardButton("⬅️ Назад", callback_data="menu")])
    return InlineKeyboardMarkup(rows)


def back_button(data="menu"):
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data=data)]])


HELP = (
    "Что я умею:\n"
    "/start — меню с разделами\n"
    "/tip — совет дня\n"
    "/workout — тренировка дня\n"
    "/calc — расчёт калорий\n"
    "/water — учёт воды\n"
    "/goal, /goals, /done, /cleargoals — цели\n"
    "/id — показать ID чата"
)

CALC_USAGE = (
    "Формат: /calc пол возраст рост вес активность\n"
    "Пример: /calc м 30 178 80 3\n\n"
    "Активность: 1 — сидячий образ жизни, 2 — 1–3 тренировки в неделю, "
    "3 — 3–5 тренировок, 4 — ежедневные нагрузки."
)

WATER_USAGE = (
    f"Учёт воды (цель {WATER_GOAL} мл в день).\n"
    "/water 250 — добавить 250 мл\n"
    "/water — показать, сколько выпито сегодня"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот про тренировки, питание и цели.\nВыберите раздел:",
        reply_markup=main_menu(),
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP)


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data

    if data == "menu":
        await q.edit_message_text("Выберите раздел:", reply_markup=main_menu())
    elif data == "tip":
        await q.edit_message_text("💡 " + random.choice(TIPS), reply_markup=back_button())
    elif data == "workout":
        await q.edit_message_text(random.choice(WORKOUTS), reply_markup=back_button())
    elif data == "info:calc":
        await q.edit_message_text(CALC_USAGE, reply_markup=back_button())
    elif data == "info:water":
        await q.edit_message_text(WATER_USAGE, reply_markup=back_button())
    elif data.startswith("s:"):
        key = data[2:]
        await q.edit_message_text(
            SECTIONS[key]["title"] + "\nВыберите статью:", reply_markup=section_menu(key)
        )
    elif data.startswith("a:"):
        _, key, i = data.split(":")
        art = SECTIONS[key]["articles"][int(i)]
        await q.edit_message_text(
            f"{art['title']}\n\n{art['text']}", reply_markup=back_button(f"s:{key}")
        )


async def tip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💡 " + random.choice(TIPS))


async def workout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(WORKOUTS))


# ---------- Калькулятор калорий ----------

async def calc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        sex, age, height, weight, act = context.args
        age = int(age)
        height = float(height.replace(",", "."))
        weight = float(weight.replace(",", "."))
        act = int(act)
        male = sex.lower() in ("м", "m", "муж", "male")
        female = sex.lower() in ("ж", "f", "жен", "female")
        if not (male or female) or act not in ACTIVITY:
            raise ValueError
        if not (100 <= height <= 250 and 30 <= weight <= 300):
            raise ValueError
    except ValueError:
        await update.message.reply_text(CALC_USAGE)
        return

    if not (18 <= age <= 80):
        await update.message.reply_text("Калькулятор рассчитан на взрослых от 18 до 80 лет.")
        return

    base = 10 * weight + 6.25 * height - 5 * age + (5 if male else -161)
    maintain = round(base * ACTIVITY[act])
    await update.message.reply_text(
        f"🧮 Примерная суточная норма: {maintain} ккал (поддержание веса).\n\n"
        f"Ориентир для плавного снижения: около {round(maintain * 0.9)}–{round(maintain * 0.85)} ккал.\n"
        f"Для набора массы: около {round(maintain * 1.1)} ккал.\n\n"
        "Это оценка по формуле Миффлина — Сан-Жеора, а не медицинская рекомендация."
    )


# ---------- Вода ----------

async def water(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.date.today().isoformat()
    w = context.user_data.get("water")
    if not w or w["date"] != today:
        w = {"date": today, "ml": 0}

    if context.args:
        try:
            amount = int(context.args[0])
            if not 0 < amount <= 2000:
                raise ValueError
        except ValueError:
            await update.message.reply_text(WATER_USAGE)
            return
        w["ml"] += amount

    context.user_data["water"] = w
    done = min(w["ml"] * 10 // WATER_GOAL, 10)
    bar = "🟦" * done + "⬜" * (10 - done)
    await update.message.reply_text(f"💧 Сегодня: {w['ml']} из {WATER_GOAL} мл\n{bar}")


# ---------- Цели ----------

async def goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("Напиши цель после команды: /goal пробежать 5 км")
        return
    context.user_data.setdefault("goals", []).append({"text": text, "done": False})
    await update.message.reply_text("Цель записана ✅ Список: /goals")


async def goals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    items = context.user_data.get("goals", [])
    if not items:
        await update.message.reply_text("Целей пока нет. Добавь: /goal ...")
        return
    lines = [
        f"{n}. {'✅' if g['done'] else '⬜'} {g['text']}" for n, g in enumerate(items, 1)
    ]
    await update.message.reply_text(
        "Твои цели:\n" + "\n".join(lines) + "\n\nОтметить выполненной: /done 1"
    )


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    items = context.user_data.get("goals", [])
    try:
        n = int(context.args[0])
        items[n - 1]["done"] = True
    except (ValueError, IndexError):
        await update.message.reply_text("Укажи номер цели: /done 1")
        return
    await update.message.reply_text("Отлично, так держать! 🎉")


async def cleargoals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["goals"] = []
    await update.message.reply_text("Список целей очищен.")


# ---------- Группа и служебное ----------

async def show_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"ID этого чата: {update.effective_chat.id}\n"
        f"Ваш ID: {update.effective_user.id}"
    )


async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.is_bot:
            continue
        await update.message.reply_text(
            f"Привет, {member.first_name}! 👋 Добро пожаловать в группу.\n"
            "Напиши /tip за советом или /workout за тренировкой дня. "
            "Расскажи в чате, какая у тебя цель!"
        )


async def post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Только для администратора: /post channel Текст  или  /post group Текст"""
    if not ADMIN_ID or str(update.effective_user.id) != ADMIN_ID:
        return
    parts = update.message.text.split(maxsplit=2)
    if len(parts) < 3 or parts[1] not in ("channel", "group"):
        await update.message.reply_text("Формат: /post channel Текст  или  /post group Текст")
        return
    target = CHANNEL_ID if parts[1] == "channel" else GROUP_CHAT_ID
    if not target:
        await update.message.reply_text("Этот чат не настроен в переменных Railway.")
        return
    await context.bot.send_message(chat_id=to_chat_id(target), text=parts[2])
    await update.message.reply_text("Опубликовано ✅")


# ---------- Автопубликации ----------

async def channel_autopost(context: ContextTypes.DEFAULT_TYPE):
    section = random.choice(list(SECTIONS.values()))
    art = random.choice(section["articles"])
    text = f"{section['title']}\n\n{art['title']}\n\n{art['text']}"
    await context.bot.send_message(chat_id=context.job.data, text=text)


async def group_daily(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=context.job.data, text="💡 Совет дня\n\n" + random.choice(TIPS)
    )


async def group_weekly(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.data
    await context.bot.send_message(
        chat_id=chat_id, text="🔥 Челлендж недели\n\n" + random.choice(CHALLENGES)
    )
    await context.bot.send_poll(
        chat_id=chat_id,
        question="Какая у тебя главная цель на эту неделю?",
        options=[
            "Тренироваться 3+ раза",
            "Питаться без срывов",
            "Больше воды и сна",
            "Просто не бросать",
        ],
        is_anonymous=False,
    )


def main():
    app = Application.builder().token(os.environ["BOT_TOKEN"]).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("tip", tip))
    app.add_handler(CommandHandler("workout", workout))
    app.add_handler(CommandHandler("calc", calc))
    app.add_handler(CommandHandler("water", water))
    app.add_handler(CommandHandler("goal", goal))
    app.add_handler(CommandHandler("goals", goals))
    app.add_handler(CommandHandler("done", done))
    app.add_handler(CommandHandler("cleargoals", cleargoals))
    app.add_handler(CommandHandler("id", show_id))
    app.add_handler(CommandHandler("post", post))
    app.add_handler(CallbackQueryHandler(on_button))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))

    hour = int(os.environ.get("POST_HOUR_UTC", "6"))
    when = datetime.time(hour=hour, tzinfo=datetime.timezone.utc)

    if CHANNEL_ID:
        app.job_queue.run_daily(channel_autopost, time=when, data=to_chat_id(CHANNEL_ID))
    if GROUP_CHAT_ID:
        gid = to_chat_id(GROUP_CHAT_ID)
        app.job_queue.run_daily(group_daily, time=when, data=gid)
        # Каждый понедельник (в PTB 0 = воскресенье, 1 = понедельник)
        app.job_queue.run_daily(group_weekly, time=when, days=(1,), data=gid)

    app.run_polling()


if __name__ == "__main__":
    main()
