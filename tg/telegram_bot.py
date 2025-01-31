from dotenv import load_dotenv
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, filters, MessageHandler, CallbackContext
import aiohttp
import os
import json
from db import is_user_in_whitelist
import re

load_dotenv()

TG_BOT_TOKEN = str(os.getenv('TG_BOT_TOKEN'))
ACCESS_TOKEN = os.getenv('TOKENS', '').split(',')[0]

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())

def is_valid_imei(imei: str) -> bool:
    if not re.fullmatch(r"\d{15}", imei):
        return False
    
    def luhn_checksum(imei: str) -> bool:
        total = 0
        for i, digit in enumerate(reversed(imei)):
            n = int(digit)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9
            total += n
        return total % 10 == 0
    
    return luhn_checksum(imei)

async def start(update: Update, context: CallbackContext) -> None:
    if update.message:
        await update.message.reply_text('Привет! Я асинхронный бот на python-telegram-bot!')

async def echo(update: Update, context: CallbackContext) -> None:
    if update.message:
        user_id = update.message.from_user.id # type: ignore
        if not is_user_in_whitelist(user_id):
            await update.message.reply_text('Ваш ID не в whitelist. Доступ запрещен.')
            return
        
        if update.message.text is None:
            await update.message.reply_text('Некорректное сообщение.')
            return
        
        if not is_valid_imei(update.message.text):
            await update.message.reply_text('Некорректный imei.')
            return
        
        response = await get_imei_data(update.message.text)
        await update.message.reply_text(json.dumps(response, indent=4, ensure_ascii=True))

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
