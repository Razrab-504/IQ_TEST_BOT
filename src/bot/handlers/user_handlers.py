from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext


from src.bot.keyboards.user_keyboard import show_test_keyboard, choice_kbd
from src.db.database import session
from src.db import crud
from src.bot.filters.user_filter import IsUser
from src.bot.keyboards.user_keyboard import inline_tests, results_keyboard

user_router = Router()
user_router.message.filter(IsUser())


class DoTest(StatesGroup):
    answer_quastion = State()


@user_router.message(CommandStart())
async def start_cmd(message: Message):
    
    async with session() as db:
        await crud.create_user(
            db,
            name=message.from_user.full_name,
            telegram_id=message.from_user.id,
        )
        

        await message.answer(f"Привет {message.from_user.full_name}, давай проверим твой IQ! Нажми на любую из следующих кнопок", reply_markup=show_test_keyboard)
  
  
@user_router.callback_query(F.data=="not_titles")
async def not_titles(callback: CallbackQuery):
    await callback.answer("Пока что тестов нет", show_alert=True)
    
  

@user_router.message(F.text == "📝 Показать все тесты")
async def get_tests_cmd(message: Message):
    
    async with session() as db:
        all_tests = await crud.get_all_tests(db)
    
    if not all_tests:
        await message.answer("К сожелению на данный момент тестов нет 📝")
    
    else:
        await message.answer("Вот ваши тесты", reply_markup=await inline_tests())


"""Пишем то как будет USER отвечать на вопросы"""
@user_router.callback_query(F.data.endswith("_test"))
async def do_test(callback: CallbackQuery, state: FSMContext):
    data = callback.data
    title = data[:-5] if data.endswith("_test") else data
    
    async with session() as db:
        test_id = await crud.get_test_id(db=db, title=title)
        quastions = await crud.get_all_quastions(db=db, test_id=test_id)
        
    
    if not quastions:
        await callback.message.answer("У этого теста нет вопросов")
        return

    
    quastions_ids = [q.id for q in quastions]
    quastion_number = 0
    
    async with session() as db:
        quastion = await crud.get_question_by_id(db=db, question_id=quastions_ids[quastion_number])
        choices = await crud.get_choices_by_question_id(db=db, question_id=quastions_ids[quastion_number])
        
    
    choices_text = "\n".join([f"{c.label} {c.text}" for c in choices])
    
    await callback.message.answer(
        f"Вопрос №{quastion_number + 1}:\n\n"
        f"{quastion.text}\n\n"
        f"{choices_text}",
        reply_markup=choice_kbd
    )
    
    async with session() as db:
        user = await crud.get_user_by_telegram_id(db=db, telegram_id=callback.from_user.id)
        user_id = user.id
        
        existing_attempt = await crud.get_in_progress_attempt(db=db, user_id=user_id, test_id=test_id)
        
        if existing_attempt:
            await crud.delete_attempt(db=db, attempt_id=existing_attempt.id)
        
        attempt = await crud.create_attemp(
            db=db,
            user_id=user_id,
            test_id=test_id,
            score=0,
            total=len(quastions_ids),
            status="in_progress"
        )
        attempt_id = attempt.id
    
    await state.update_data(
        quastions_ids=quastions_ids, 
        current_index=quastion_number,
        score=0, 
        test_id=test_id,
        attempt_id=attempt_id,
        user_id=user_id
    )
    
    await state.set_state(DoTest.answer_quastion)
    

"""НАДО ПРОДОЛЖИТЬ ТО КАК БУДЕТ ОТПРАВЛЯТЬ ОТВЕТЫ USER"""

@user_router.message(DoTest.answer_quastion, F.text.in_(["A", "B", "C"]))
async def process_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    questions_ids = data["quastions_ids"]
    current_index = data["current_index"]
    score = data["score"]
    test_id = data["test_id"]
    attempt_id = data["attempt_id"]
    user_id = data["user_id"]
    
    user_answer = message.text + ')'
    
    async with session() as db:
        correct = await crud.get_correct_choice(db=db, question_id=questions_ids[current_index])
        choice = await crud.get_choice_by_label(db=db, label=user_answer, question_id=questions_ids[current_index])
        
        
    async with session() as db:
        await crud.create_answer(
            db=db,
            attempt_id=attempt_id,
            user_id=user_id,
            question_id=questions_ids[current_index],
            selected_choice_id=choice.id if choice else None
        )
    
    if correct and correct.label == user_answer:
        score += 1
        await message.answer("✅ Правильно!")
    else:
        await message.answer(f"❌ Неправильно. Правильный ответ: {correct.label}")
    
    current_index += 1
    
    if current_index >= len(questions_ids):
        
        async with session() as db:
            await crud.update_attempt(
                db=db,
                id=attempt_id,
                score=score,
                status="finished"
            )
        
        total = len(questions_ids)
        
        
        await message.answer(
            f"🎉 Тест завершён!\n\n"
            f"Ваш результат: {score}/{total}",
            reply_markup=show_test_keyboard
        )
        await state.clear()
        return
    
    async with session() as db:
        question = await crud.get_question_by_id(db=db, question_id=questions_ids[current_index])
        choices = await crud.get_choices_by_question_id(db=db, question_id=questions_ids[current_index])
    
    choices_text = "\n".join([f"{c.label} {c.text}" for c in choices])
    
    await message.answer(
        f"Вопрос №{current_index + 1}:\n\n"
        f"{question.text}\n\n"
        f"{choices_text}",
        reply_markup=choice_kbd
    )
    
    await state.update_data(current_index=current_index, score=score)


@user_router.message(F.text == "📊 Мои результаты")
async def get_all_attempts(message: Message):
    async with session() as db:
        user = await crud.get_user_by_telegram_id(db=db, telegram_id=message.from_user.id)
        user_id = user.id
        
        if not user:
            await message.answer("Пользователь не найден")
            return
        
        completed_tests = await crud.get_completed_tests_by_user(db=db, user_id=user_id)
    
    if not completed_tests:
        await message.answer("Вы еще не прошли никаких тестов 📊")
    else:
        await message.answer(
            "Выберите тест для просмотра результатов:", 
            reply_markup=await results_keyboard(completed_tests)
        )
        

@user_router.callback_query(F.data.startswith("result_"))
async def show_tests_results(callback: CallbackQuery):
    await callback.answer()
    test_id = int(callback.data.split("_")[1])
    
    async with session() as db:
        user = await crud.get_user_by_telegram_id(db=db, telegram_id=callback.from_user.id)
        user_id = user.id
        attempts = await crud.get_user_attempts_by_test(db=db, test_id=test_id, user_id=user_id)
        
        
    if not attempts:
        await callback.message.answer("Не было найдено попыток решения этого теста")
    
    result_text = "📊 Ваши результаты:\n\n"
    for i, attempt in enumerate(attempts, 1):
        result_text += (
            f"Попытка {i}:\n"
            f"Результат: {attempt.score}/{attempt.total}\n"
            f"Дата: {attempt.started_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        )
        
    await callback.message.edit_text(result_text)
        


@user_router.message(F.text == "ℹ️ Помощь")
async def hellp_cmd(message: Message):
    text = (
    "Это Бот, в котором вы можете проверить уровень вашего IQ.\n"
    "Вам нужно нажать на кнопку **📝 Показать все тесты**,\n"
    "затем выбрать любой тест и пройти его.\n\n"
    "Вы можете посмотреть свои результаты,\n"
    "нажав на кнопку **ℹ️ Помощь**."
)
    
    await message.answer(text)
    