import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.db.models import Base, Task, TaskDetail, TaskStatus
from src.db.database import get_db
import uuid
from datetime import datetime

# Use in-memory SQLite for testing
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture
async def async_engine():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def session(async_engine):
    async_session = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as s:
        yield s

@pytest.mark.asyncio
async def test_create_task(session):
    task_id = str(uuid.uuid4())
    new_task = Task(id=task_id, status=TaskStatus.PENDING, total_pages=5)
    session.add(new_task)
    await session.commit()

    # Query back
    result = await session.get(Task, task_id)
    assert result is not None
    assert result.status == TaskStatus.PENDING
    assert result.total_pages == 5
    assert isinstance(result.created_at, datetime)

@pytest.mark.asyncio
async def test_task_details(session):
    task_id = str(uuid.uuid4())
    task = Task(id=task_id, status=TaskStatus.PROCESSING, total_pages=2)
    session.add(task)
    await session.commit()

    # Add details
    detail1 = TaskDetail(task_id=task_id, page_num=1, status=TaskStatus.COMPLETED, content="Page 1 Content")
    detail2 = TaskDetail(task_id=task_id, page_num=2, status=TaskStatus.PENDING)
    session.add_all([detail1, detail2])
    await session.commit()

    # Refresh task to see relationships (if configured) or query details
    # For now, let's query details directly
    from sqlalchemy import select
    stmt = select(TaskDetail).where(TaskDetail.task_id == task_id).order_by(TaskDetail.page_num)
    result = await session.execute(stmt)
    details = result.scalars().all()

    assert len(details) == 2
    assert details[0].content == "Page 1 Content"
    assert details[1].status == TaskStatus.PENDING
