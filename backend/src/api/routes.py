import os
import shutil
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.database import get_db, AsyncSessionLocal
from src.db.models import Task, TaskStatus, TaskResponse
from src.worker.tasks import convert_pdf_task, run_async_process
from sqlalchemy import func, select

router = APIRouter()

UPLOAD_DIR = "files/tasks"  # 改为 tasks 目录，每个任务一个子文件夹
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def perform_cleanup(max_tasks: int):
    """自动清理多余的旧任务"""
    import shutil
    async with AsyncSessionLocal() as db:
        try:
            # 获取任务总数
            count_result = await db.execute(select(func.count()).select_from(Task))
            total = count_result.scalar() or 0
            
            if total <= max_tasks:
                return

            # 计算需要删除的数量
            to_delete_count = total - max_tasks
            
            # 找到最旧的任务
            result = await db.execute(
                select(Task)
                .order_by(Task.created_at.asc())
                .limit(to_delete_count)
            )
            old_tasks = result.scalars().all()
            
            for task in old_tasks:
                # 删除文件目录: files/tasks/{task_id}/
                task_dir = os.path.join(UPLOAD_DIR, task.id)
                if os.path.exists(task_dir):
                    shutil.rmtree(task_dir)
                
                # 从数据库中完全删除
                await db.delete(task)
            
            await db.commit()
        except Exception as e:
            print(f"Cleanup error: {e}")

@router.post("/upload", response_model=TaskResponse)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Generate Task ID
    task_id = str(uuid.uuid4())
    
    # 创建任务专属文件夹: files/tasks/{task_id}/
    task_dir = os.path.join(UPLOAD_DIR, task_id)
    os.makedirs(task_dir, exist_ok=True)
    
    # 保存文件 - 保留原始文件名
    original_filename = file.filename
    file_path = os.path.join(task_dir, original_filename)
    contents = await file.read()
    with open(file_path, "wb") as buffer:
        buffer.write(contents)
        
    # Create DB Task - 存储原始文件名
    new_task = Task(
        id=task_id,
        file_name=original_filename,  # 保存原始文件名
        status=TaskStatus.PENDING,
        total_pages=0 # Will be updated by worker
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    
    # Check execution mode
    use_celery = os.getenv("USE_CELERY", "true").lower() == "true"
    
    # 从持久化文件加载最新设置
    from .settings import load_settings_from_env
    settings = load_settings_from_env()
    model_name = settings.model
    concurrency = settings.concurrency
    api_key = settings.apiKey
    base_url = settings.baseUrl
    
    if use_celery:
        # Celery Mode
        convert_pdf_task.delay(task_id, os.path.abspath(file_path), model_name, concurrency, api_key, base_url)
    else:
        # Local Mode (BackgroundTasks)
        background_tasks.add_task(run_async_process, task_id, os.path.abspath(file_path), model_name, concurrency, api_key, base_url)
    
    # 增加自动清理后台任务
    background_tasks.add_task(perform_cleanup, settings.maxTasks)
    
    return new_task

@router.get("/tasks")
async def list_tasks(skip: int = 0, limit: int = 20, db: AsyncSession = Depends(get_db)):
    # 获取任务总数
    from sqlalchemy import func
    count_result = await db.execute(select(func.count()).select_from(Task))
    total = count_result.scalar() or 0
    
    # 获取分页任务
    result = await db.execute(select(Task).offset(skip).limit(limit).order_by(Task.created_at.desc()))
    tasks = result.scalars().all()
    
    # 返回符合前端契约的格式: { items: [...], total: N }
    return {"items": tasks, "total": total}

@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, db: AsyncSession = Depends(get_db)):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.get("/tasks/{task_id}/download")
async def download_task(task_id: str, db: AsyncSession = Depends(get_db)):
    from fastapi.responses import FileResponse
    
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    if task.status != TaskStatus.COMPLETED or not task.result_path:
        raise HTTPException(status_code=400, detail="Task not completed or result missing")
        
    if not os.path.exists(task.result_path):
        raise HTTPException(status_code=404, detail="Result file not found on server")
    # 使用原始文件名作为下载文件名
    import os as os_module
    if task.file_name:
        download_name = os_module.path.splitext(task.file_name)[0] + ".md"
    else:
        download_name = f"{task_id}.md"
    return FileResponse(task.result_path, filename=download_name)

# Settings Endpoints - 使用持久化的 settings 模块
from .settings import Settings, current_settings, save_settings_to_env, load_settings_from_env

@router.get("/settings", response_model=Settings)
async def get_settings():
    # 每次获取时重新从文件加载，确保获取最新值
    global current_settings
    current_settings = load_settings_from_env()
    return current_settings

@router.post("/settings", response_model=Settings)
async def update_settings(settings: Settings):
    global current_settings
    current_settings = settings
    # 持久化到 .env 文件
    save_settings_to_env(settings)
    return current_settings

