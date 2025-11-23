from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from src.db import crud
from src.db.database import session
import asyncio


menu_kbd = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📝 Создать Тест", callback_data="create_tests")],
    [InlineKeyboardButton(text="🗑️ Удалить Тест", callback_data="delete_tests"),
    InlineKeyboardButton(text="📊 Посмотреть статистику тестов", callback_data="statistics_tests")
    ]
])

async def get_all_tests_title():
    async with session() as db:
        titles = await crud.get_all_tests_title(db)
        
    return titles


async def inline_tests():
    titles = await get_all_tests_title()
    keyboard = InlineKeyboardBuilder()
    
    if not titles:
        keyboard.add(InlineKeyboardButton(text="Тестов пока что нет", callback_data="not_titles"))
        return
    
    for title in titles:
        keyboard.add(InlineKeyboardButton(text=title, callback_data=f"{title}_delete_tests"))
    
    return keyboard.adjust(2).as_markup()