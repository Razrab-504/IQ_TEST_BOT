from typing import Optional
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from src.bot.filters.admin_filter import IsAdmin
from src.bot.keyboards import admin_keyboards as kb
from src.db import crud
from src.db.database import session
from src.bot.keyboards.admin_keyboards import inline_tests
import re


class CreateTest(StatesGroup):
    title = State()
    description = State()


class CreateQuastions(StatesGroup):
    quastion = State()


admin_router = Router()
admin_router.message.filter(IsAdmin())


@admin_router.message(CommandStart())
async def start_cmd(message: Message):
    await message.answer(f"Привет админ {message.from_user.full_name}", reply_markup=kb.menu_kbd)



@admin_router.callback_query(F.data == "create_tests")
async def create_test_cmd(callback: CallbackQuery, state: FSMContext):
    await callback.answer("Создать Тест ")
    await callback.message.edit_text("Хорошо давайте создадим новый тест. Введите пожалуйста название теста")
    await state.set_state(CreateTest.title)
    

@admin_router.message(CreateTest.title)
async def title_cmd(message: Message, state: FSMContext):
    new_title = message.text
    
    async with session() as db:
        titles = await crud.get_all_tests_title(db)
    
    if titles and any(new_title== t for t in titles):    
        await message.answer("Тест с таким названием уже существует. Пожалуйста поменяйте его")
        return
    
    await message.answer("Теперь напиши описания ... или /skip")
    await state.update_data(title=new_title)
    await state.set_state(CreateTest.description)


@admin_router.message(CreateTest.description)
async def description_cmd(message: Message, state: FSMContext):
    description = message.text

    if description.strip().lower() == "/skip":
        await state.update_data(description=None)
    else:
        await state.update_data(description=description)
    

    data = await state.get_data()
    
    
    async with session() as db:
        test_id = await crud.create_tests(
            db,
            title=data['title'],
            description=data['description']
        )
        
    
    
    await state.update_data(test_id=test_id, question_count=0)
    await state.set_state(CreateQuastions.quastion)
    
    await message.answer(
        "Пожалуйста отправляйте вопрос в 3 строки как показано:\n"
        "1) Вопрос\n2) Варианты: A) ... B) ... C) ...\n3) Правильный ответ: A")


@admin_router.message(CreateQuastions.quastion)
async def create_quastion(message: Message, state: FSMContext):
    data = await state.get_data()
    question_count = data.get("question_count", 0)
    text = message.text.strip()
    test_id = data.get("test_id")
    
    if text.lower() == "/done":
        if question_count < 5:
            await message.answer("Слишком мало вопросов, нужно минимум 5.")
            return
        await state.clear()
        await message.answer("Вы завершили добавление вопросов ✅")
        return
    
    lines = text.split("\n")
    
    if len(lines) != 3:
        await message.answer(
            "Пожалуйста отправляйте вопрос в 3 строки как показано:\n"
            "1) Вопрос\n2) Варианты: A) ... B) ... C) ...\n3) Правильный ответ: A)"
        )
        return
    
    question_text = lines[0].strip()
    
    async with session() as db:
        questions = await crud.get_all_quastions(db=db, test_id=test_id)
        for q in questions:
            if q.text == question_text:
                await message.answer("Такой вопрос уже ты писал")
                return
    
    correct_choice_line = lines[2].strip()
    if not correct_choice_line.lower().startswith("правильный ответ:"):
        await message.answer("Третья строка должна начинаться с 'Правильный ответ:'")
        return

    correct_choice = correct_choice_line.split(":", 1)[1].strip().upper()
    valid_choices = ['A)', 'B)', 'C)']

    if correct_choice not in valid_choices:
        await message.answer("Правильный ответ может быть только A), B) или C)")
        return

    variants_line = lines[1].strip()
    if not variants_line.lower().startswith("варианты:"):
        await message.answer("Вторая строка должна начинаться с 'Варианты:'")
        return

    variants_text = variants_line.split(":", 1)[1].strip()
    found_choices = re.findall(r'[A-Z]\)', variants_text.upper())

    if found_choices != ['A)', 'B)', 'C)']:
        await message.answer(
            "Нужно указать ровно 3 варианта в порядке: A), B), C)\n"
            "Без лишних вариантов (D, E и т.д.)"
        )
        return
    
    if not test_id:
        await message.answer("Ошибка: test_id не найден. Начните с создания теста.")
        await state.clear()
        return
    
    choices_data = []
    for match in re.finditer(r'([A-C])\)\s*(.+?)(?=\s*[A-C]\)|$)', variants_text):
        label = match.group(1) + ")"
        choice_text = match.group(2).strip()
        choices_data.append({
            "label": label,
            "text": choice_text,
            "is_correct": label == correct_choice
        })
    
    async with session() as db:
        question = await crud.create_quastion(
            db=db,
            test_id=test_id,
            text=question_text
        )
        
        for choice in choices_data:
            await crud.create_choice(
                db=db,
                question_id=question,
                label=choice["label"],
                text=choice["text"],
                is_correct=choice["is_correct"]
            )
    
    question_count += 1
    await state.update_data(question_count=question_count)
    await message.answer(
        f"Вопрос добавлен ✅ Всего вопросов: {question_count}\n"
        "Чтобы завершить — отправьте /done"
    )
            
            

@admin_router.callback_query(F.data=="not_titles")
async def not_titles(callback: CallbackQuery):
    await callback.answer("Пока что тестов нет", show_alert=True)


@admin_router.callback_query(F.data == "delete_tests")
async def delete_test_cmd(callback: CallbackQuery):
    await callback.answer("Удалить тест")
    
    tests = await inline_tests()
    
    if not tests:
        await callback.message.edit_text("Пока что тестов нету")
        return
    
    await callback.message.edit_text("Выберите один из следующих тестов который хотите удалить", reply_markup=await inline_tests())
    
    

@admin_router.callback_query(F.data.endswith("_delete_tests"))
async def delete_test(callback: CallbackQuery):
    await callback.answer()
    data = callback.data
    title = data[:-13] if data.endswith("_delete_tests") else data
    
    async with session() as db:
        await crud.delete_test_by_title(db=db, title=title)
        
        
    await callback.message.answer(f"Тест: {title} был удален")



@admin_router.callback_query(F.data.endswith("_tests"))
async def admin_statistics(callback: CallbackQuery):
    async with session() as db:
        stats = await crud.get_tests_statistics(db=db)
    
    if not stats:
        await callback.message.answer("Пока нет статистики по тестам")
        return
    
    text = "📊 Статистика по тестам:\n\n"
    
    for stat in stats:
        test_title, total_attempts, unique_users, avg_score, max_score = stat
        text += (
            f"📝 {test_title}\n"
            f"Всего попыток: {total_attempts}\n"
            f"Уникальных пользователей: {unique_users}\n"
            f"Средний балл: {avg_score:.1f}/{max_score}\n\n"
        )
    
    await callback.message.answer(text)