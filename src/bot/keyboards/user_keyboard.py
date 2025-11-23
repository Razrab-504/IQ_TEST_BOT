from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from src.db import crud
from src.db.database import session

show_test_btn = KeyboardButton(text="📝 Показать все тесты")
show_results_btn = KeyboardButton(text="📊 Мои результаты")
hellp_btn = KeyboardButton(text="ℹ️ Помощь")


show_test_keyboard = ReplyKeyboardMarkup(
    keyboard=[[show_test_btn, show_results_btn], [hellp_btn]],
    resize_keyboard=True
)

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
        keyboard.add(InlineKeyboardButton(text=title, callback_data=f"{title}_test"))
    
    return keyboard.adjust(2).as_markup()


A_choice = KeyboardButton(text="A")
B_choice = KeyboardButton(text="B")
C_choice = KeyboardButton(text="C")


choice_kbd = ReplyKeyboardMarkup(keyboard=[
    [A_choice, B_choice],
    [C_choice]
], resize_keyboard=True)


async def results_keyboard(completed_tests):
    keyboard = InlineKeyboardBuilder()
    
    for test in completed_tests:
        test_id, title, score, total, started_at = test
        button_text = f"{title} ({score}/{total})"
        keyboard.add(InlineKeyboardButton(
            text=button_text, 
            callback_data=f"result_{test_id}"
        ))
    
    return keyboard.adjust(1).as_markup()