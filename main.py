import os
import random

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TIPS = [
    "Пей воду в течение дня: стакан сразу после пробуждения.",
    "Белок в каждом приёме пищи помогает восстановлению.",
    "Лучшая тренировка та, которую ты реально делаешь регулярно.",
    "Сон 7–9 часов важен не меньше, чем тренировки.",
    "Ставь маленькие цели на неделю, а не только на год.",
]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот про тренировки, питание и цели.\n"
        "/tip — совет дня\n"
        "/goal <текст> — записать цель"
    )


async def tip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(TIPS))


async def goal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("Напиши цель после команды: /goal пробежать 5 км")
        return
    goals = context.user_data.setdefault("goals", [])
    goals.append(text)
    await update.message.reply_text(f"Цель записана ✅ Всего целей: {len(goals)}")


def main():
    app = Application.builder().token(os.environ["BOT_TOKEN"]).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("tip", tip))
    app.add_handler(CommandHandler("goal", goal))
    app.run_polling()


if __name__ == "__main__":
    main()
