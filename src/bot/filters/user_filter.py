from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

ADMIN_ID = int(os.getenv("ADMIN_ID"))

class IsUser(BaseFilter):
    async def __call__(self, events: Message | CallbackQuery) -> bool:
        return events.from_user.id != ADMIN_ID