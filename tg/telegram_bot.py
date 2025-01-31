from dotenv import load_dotenv
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, filters, MessageHandler, CallbackContext
import aiohttp
import os
import json
from db import is_user_in_whitelist

load_dotenv()

TG_BOT_TOKEN = str(os.getenv('TG_BOT_TOKEN'))
ACCESS_TOKEN = os.getenv('TOKENS', '').split(',')[0]

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())

async def start(update: Update, context: CallbackContext) -> None:
    if update.message:
        await update.message.reply_text('Привет! Я асинхронный бот на python-telegram-bot!')

async def echo(update: Update, context: CallbackContext) -> None:
    if update.message:
        user_id = update.message.from_user.id # type: ignore
        
        if update.message.text is None:
            await update.message.reply_text('Некорректное сообщение.')
            return
        
        if not '!' in update.message.text and not is_user_in_whitelist(user_id):
            await update.message.reply_text('Ваш ID не в whitelist. Доступ запрещен. (В рамках тестирования, добавьте "!" в сообщение и эта проверка будет игнорироваться)')
            return
        
        response = await get_imei_data(update.message.text.replace('!', ''))
        await update.message.reply_text(json.dumps(response, indent=4, ensure_ascii=False))

async def get_imei_data(imei:str) -> dict|list:
    async with aiohttp.ClientSession() as session:
        payload = {
            'token':ACCESS_TOKEN,
            'imei':imei,
        }
        async with session.post('http://web:8000/api/check-imei', json=payload) as response:
            response_json = await response.json()
            return response_json

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.warning('Обработана ошибка: "%s"', context.error)

def main() -> None:
    application = Application.builder().token(TG_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    application.add_error_handler(error_handler)
    application.run_polling()

if __name__ == '__main__':
    main()
