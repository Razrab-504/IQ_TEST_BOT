from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from src.db import models
from typing import Optional
import datetime
from sqlalchemy import func



async def create_user(db: AsyncSession, name: str, telegram_id: int, created_at: Optional[datetime.datetime] = None):
    result = await db.execute(
        select(models.UsersTable).where(models.UsersTable.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()

    if user:
        return user

    user = models.UsersTable(
        name=name,
        telegram_id=telegram_id,
        created_at=created_at
    )
    db.add(user)
    await db.flush()
    await db.commit()
    await db.refresh(user)
    return user



async def get_all_tests(db: AsyncSession):
    query = select(models.TestsTable)
    result = await db.execute(query)
    tests = result.scalars().all()
    return tests



async def get_all_attempts(db: AsyncSession):
    query = select(models.AttemptsTable)
    result = await db.execute(query)
    all_attempts = result.scalars()
    return all_attempts
    

async def create_tests(db: AsyncSession, title: str, description: Optional[str] = None, created_at: Optional[datetime.datetime] = None):
    stmt = models.TestsTable(
        title=title,
        description=description,
        created_at=created_at
    )
    db.add(stmt)
    await db.flush()
    await db.commit()
    await db.refresh(stmt)
    return stmt.id 
        

async def get_all_tests_title(db: AsyncSession):
    query = select(models.TestsTable.title)
    result = await db.execute(query)
    titles = result.scalars().all()
    return titles


async def delete_test_by_title(db: AsyncSession, title: str):
    await db.execute(delete(models.TestsTable).where(models.TestsTable.title == title))
    await db.commit()
        
        

async def create_quastion(db: AsyncSession, test_id: int, text: str):
    question = models.QuestionTable(
        test_id=test_id,
        text=text,
    )
    db.add(question)
    await db.flush()
    await db.commit()
    await db.refresh(question)
    return question.id


async def get_all_quastions(db: AsyncSession, test_id: int):
    quary = select(models.QuestionTable).where(models.QuestionTable.test_id==test_id)
    result = await db.execute(quary)
    return result.scalars().all()


async def get_test_id(db: AsyncSession, title: str):
    quary = select(models.TestsTable).where(models.TestsTable.title==title)
    result = await db.execute(quary)
    test = result.scalar_one_or_none()
    test_id = test.id
    return test_id



async def create_attemp(
    db: AsyncSession, status: str, user_id: int, 
    test_id: Optional[int] = None, score: Optional[int] = None, 
    total: Optional[int] = None 
    ):
    stmt = models.AttemptsTable(
        user_id=user_id,
        test_id=test_id,        
        score=score,
        total=total,
        status=status
    )
    
    db.add(stmt)
    await db.flush()
    await db.commit()
    await db.refresh(stmt)
    return stmt
    
    

async def get_question_by_id(db: AsyncSession, question_id):
    query = select(models.QuestionTable).where(models.QuestionTable.id==question_id)
    result = await db.execute(query)
    question = result.scalar_one_or_none()
    return  question


async def create_choice(db: AsyncSession, question_id: int, label: str, text: str, is_correct: bool):
    stmt = models.ChoicesTable(
        question_id=question_id,
        label=label,
        text=text,
        is_correct=is_correct
    )
    db.add(stmt)
    await db.flush()
    await db.commit()
    await db.refresh(stmt)
    
    
async def get_choices_by_question_id(db: AsyncSession, question_id: int):
    query = select(models.ChoicesTable).where(
        models.ChoicesTable.question_id == question_id
    ).order_by(models.ChoicesTable.label)
    result = await db.execute(query)
    return result.scalars().all()


async def get_correct_choice(db: AsyncSession, question_id: int):
    query = select(models.ChoicesTable).where(
        models.ChoicesTable.question_id == question_id,
        models.ChoicesTable.is_correct == True
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()



async def get_user_by_telegram_id(db: AsyncSession, telegram_id: int):
    query = select(models.UsersTable).where(models.UsersTable.telegram_id==telegram_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    return user


async def get_choice_by_label(db: AsyncSession, label: str, question_id: int):
    query = select(models.ChoicesTable).where(
        models.ChoicesTable.question_id == question_id,
        models.ChoicesTable.label == label
        )
    
    result = await db.execute(query)
    choice = result.scalar_one_or_none()
    return choice


async def create_answer(db: AsyncSession, attempt_id: int, user_id: int, question_id: int, selected_choice_id: int):
    stmt = models.AnswersTable(
        attempt_id=attempt_id,
        user_id=user_id,
        question_id=question_id,
        selected_choice_id=selected_choice_id
    )
    
    db.add(stmt)
    await db.flush()
    await db.commit()
    await db.refresh(stmt)
    return stmt


async def update_attempt(db: AsyncSession, score: int, status: str, id: int):
    stmt = update(models.AttemptsTable).where(models.AttemptsTable.id==id).values(score=score, status=status)
    result = await db.execute(stmt)
    await db.commit()
    
    return result


async def get_in_progress_attempt(db: AsyncSession, user_id: int, test_id: int):
    query = select(models.AttemptsTable).where(
        models.AttemptsTable.user_id == user_id,
        models.AttemptsTable.test_id == test_id,
        models.AttemptsTable.status == "in_progress"
    )
    
    result = await db.execute(query)
    attempt = result.scalar_one_or_none()
    return attempt


async def delete_attempt(db: AsyncSession, attempt_id: int):
    delete(models.AttemptsTable).where(models.AttemptsTable.id == attempt_id)
    await db.commit()
    
    

async def get_completed_tests_by_user(db: AsyncSession, user_id: int):
    query = select(
        models.AttemptsTable.test_id,
        models.TestsTable.title,
        models.AttemptsTable.score,
        models.AttemptsTable.total,
        models.AttemptsTable.started_at
    ).join(
        models.TestsTable, 
        models.AttemptsTable.test_id == models.TestsTable.id
    ).where(
        models.AttemptsTable.user_id == user_id,
        models.AttemptsTable.status == "finished"
    ).order_by(models.AttemptsTable.started_at.desc())
    
    result = await db.execute(query)
    return result.all()


async def get_user_attempts_by_test(db: AsyncSession, test_id: int, user_id: int):
    query = select(models.AttemptsTable).where(
        models.AttemptsTable.user_id == user_id,
        models.AttemptsTable.test_id == test_id,
        models.AttemptsTable.status == "finished"
    ).order_by(models.AttemptsTable.started_at.desc())
    
    result = await db.execute(query)
    return result.scalars().all()



async def get_tests_statistics(db: AsyncSession):
    
    query = select(
        models.TestsTable.title,
        func.count(models.AttemptsTable.id).label('total_attempts'),
        func.count(func.distinct(models.AttemptsTable.user_id)).label('unique_users'),
        func.avg(models.AttemptsTable.score).label('avg_score'),
        func.max(models.AttemptsTable.total).label('max_score')
    ).join(
        models.AttemptsTable,
        models.TestsTable.id == models.AttemptsTable.test_id
    ).where(
        models.AttemptsTable.status == "finished"
    ).group_by(
        models.TestsTable.id,
        models.TestsTable.title
    ).order_by(
        func.count(models.AttemptsTable.id).desc()
    )
    
    result = await db.execute(query)
    return result.all()