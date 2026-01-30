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


async def _process_upload_file(file: UploadFile, task_id: str):
    """Internal helper to save file"""
    # 创建任务专属文件夹: files/tasks/{task_id}/
    task_dir = os.path.join(UPLOAD_DIR, task_id)
    os.makedirs(task_dir, exist_ok=True)
    
    # 保存文件 - 保留原始文件名
    original_filename = file.filename
    file_path = os.path.join(task_dir, original_filename)
    contents = await file.read()
    with open(file_path, "wb") as buffer:
        buffer.write(contents)
        
    return original_filename, os.path.abspath(file_path)

def _create_task_obj(task_id: str, original_filename: str) -> Task:
    """Internal helper to create Task object (not committed)"""
    return Task(
        id=task_id,
        file_name=original_filename,
        status=TaskStatus.PENDING,
        total_pages=0
    )

def _get_processing_params():
    """Helper to get processing parameters from settings"""
    from .settings import load_settings_from_env
    settings = load_settings_from_env()
    return {
        "model_name": settings.model,
        "concurrency": settings.concurrency,
        "api_key": settings.apiKey,
        "base_url": settings.baseUrl,
        "max_tasks": settings.maxTasks,
        "use_celery": os.getenv("USE_CELERY", "true").lower() == "true"
    }

def _trigger_background_task(
    background_tasks: BackgroundTasks, 
    task_id: str, 
    file_path: str, 
    params: dict
):
    """Helper to trigger background processing"""
    if params["use_celery"]:
        convert_pdf_task.delay(
            task_id, 
            file_path, 
            params["model_name"], 
            params["concurrency"], 
            params["api_key"], 
            params["base_url"]
        )
    else:
        background_tasks.add_task(
            run_async_process, 
            task_id, 
            file_path, 
            params["model_name"], 
            params["concurrency"], 
            params["api_key"], 
            params["base_url"]
        )

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
    
    # Save file
    original_filename, file_path_abs = await _process_upload_file(file, task_id)
        
    # Create DB Task
    new_task = _create_task_obj(task_id, original_filename)
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    
    # Trigger processing
    params = _get_processing_params()
    _trigger_background_task(background_tasks, task_id, file_path_abs, params)
    
    # Cleanup task
    background_tasks.add_task(perform_cleanup, params["max_tasks"])
    
    return new_task

@router.post("/upload/batch", response_model=List[TaskResponse])
async def upload_pdf_batch(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Batch upload multiple PDF files.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
        
    tasks_to_create = []
    file_paths = {} # task_id -> file_path
    
    # Process all files first
    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            continue # Skip non-pdf files or raise error? Skipping for now to be robust
            
        task_id = str(uuid.uuid4())
        original_filename, file_path_abs = await _process_upload_file(file, task_id)
        
        new_task = _create_task_obj(task_id, original_filename)
        tasks_to_create.append(new_task)
        file_paths[task_id] = file_path_abs
        
    if not tasks_to_create:
        raise HTTPException(status_code=400, detail="No valid PDF files found")
        
    # Batch DB insert
    db.add_all(tasks_to_create)
    await db.commit()
    
    # Refresh to populate fields if needed (though we created them)
    # For list response, we might don't need refresh each, just use the objects
    
    # Trigger all tasks
    params = _get_processing_params()
    for task in tasks_to_create:
        _trigger_background_task(background_tasks, task.id, file_paths[task.id], params)
        
    # Cleanup task (just once)
    background_tasks.add_task(perform_cleanup, params["max_tasks"])
    
    return tasks_to_create


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

@router.delete("/tasks/{task_id}", status_code=204)
async def delete_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """
    删除任务，包括数据库记录和服务器上的文件
    """
    # 1. 查找任务
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    # 2. 删除文件系统中的任务目录
    task_dir = os.path.join(UPLOAD_DIR, task_id)
    if os.path.exists(task_dir):
        try:
            shutil.rmtree(task_dir)
        except Exception as e:
            print(f"Failed to delete directory {task_dir}: {e}")
            # 继续删除数据库记录，不阻拦
            
    # 3. 删除数据库记录
    try:
        await db.delete(task)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete task from DB: {e}")
        
    return


# Settings Endpoints - 使用持久化的 settings 模块
from .settings import Settings, current_settings, save_settings_to_env, load_settings_from_env
from fastapi.responses import StreamingResponse
from .sse_manager import sse_manager

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


# SSE Events Endpoints
@router.get("/events")
async def task_events(task_id: str):
    """
    SSE端点 - 实时推送任务进度

    参数:
        task_id: 任务ID

    返回:
        Server-Sent Events流

    示例:
        const eventSource = new EventSource('/api/v1/events?task_id=xxx');
        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('Progress:', data.progress);
        };
    """
    return StreamingResponse(
        sse_manager.event_generator(task_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用Nginx缓冲
        }
    )


@router.get("/events/stats")
async def events_stats():
    """获取SSE连接统计信息"""
    return sse_manager.get_stats()


# Page Preview Endpoints
@router.get("/tasks/{task_id}/pages/{page_num}")
async def get_page_image(task_id: str, page_num: int, db: AsyncSession = Depends(get_db)):
    """
    获取指定页面的渲染图片

    参数:
        task_id: 任务ID
        page_num: 页码 (从 1 开始)

    返回:
        页面图片文件 (jpg/png)
    """
    from fastapi.responses import FileResponse

    # 验证任务是否存在
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # 验证页码是否有效（添加合理的上限）
    if page_num < 1 or page_num > 10000:
        raise HTTPException(status_code=400, detail=f"Invalid page number: {page_num}")
    if task.total_pages and page_num > task.total_pages:
        raise HTTPException(status_code=400, detail=f"Page {page_num} exceeds total pages ({task.total_pages})")

    # 构建图片路径，支持 jpg 和 png 格式
    task_dir = os.path.join(UPLOAD_DIR, task_id)

    # 尝试 jpg 格式 (file_worker 默认格式)
    image_path = os.path.join(task_dir, f"page_{page_num:04d}.jpg")
    if not os.path.exists(image_path):
        # 尝试 png 格式 (desktop_study 格式)
        image_path = os.path.join(task_dir, f"page_{page_num}.png")

    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail=f"Page {page_num} image not found")

    return FileResponse(
        image_path,
        media_type="image/jpeg" if image_path.endswith(".jpg") else "image/png",
        headers={"Cache-Control": "max-age=3600"}  # 缓存 1 小时
    )


@router.get("/tasks/{task_id}/pages/{page_num}/content")
async def get_page_content(task_id: str, page_num: int, db: AsyncSession = Depends(get_db)):
    """
    获取指定页面的 Markdown 文本内容

    架构改进:
    - 直接读取每页的 markdown 文件 (page_0001.md)
    - 无需分割最终的合并文件
    - 支持实时预览 - 页面转换完成即可查看

    参数:
        task_id: 任务ID
        page_num: 页码 (从 1 开始)

    返回:
        页面 Markdown 内容和状态信息
    """
    # 验证任务是否存在
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # 验证页码是否有效（添加合理的上限）
    if page_num < 1 or page_num > 10000:
        raise HTTPException(status_code=400, detail=f"Invalid page number: {page_num}")
    if task.total_pages and page_num > task.total_pages:
        raise HTTPException(status_code=400, detail=f"Page {page_num} exceeds total pages ({task.total_pages})")

    # 构建页面 markdown 文件路径
    task_dir = os.path.join(UPLOAD_DIR, task_id)
    page_md_path = os.path.join(task_dir, f"page_{page_num:04d}.md")

    # 检查页面文件是否存在
    if not os.path.exists(page_md_path):
        # 页面文件不存在,可能还未完成转换
        if task.status == TaskStatus.PROCESSING:
            return {
                "page": page_num,
                "status": task.status.value,
                "content": None,
                "message": "Page is being processed...",
                "total_pages": task.total_pages
            }
        elif task.status == TaskStatus.PENDING:
            return {
                "page": page_num,
                "status": task.status.value,
                "content": None,
                "message": "Task is pending...",
                "total_pages": task.total_pages
            }
        elif task.status == TaskStatus.COMPLETED:
            # 任务已完成但页面文件不存在 - 可能是生成中的延迟
            # 返回 processing 状态让前端继续轮询
            return {
                "page": page_num,
                "status": "processing",
                "content": None,
                "message": "Page is being finalized...",
                "total_pages": task.total_pages
            }
        else:
            raise HTTPException(status_code=404, detail=f"Page {page_num} content not found")

    # 读取页面 markdown 内容
    try:
        with open(page_md_path, "r", encoding="utf-8") as f:
            page_content = f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read page content: {str(e)}")

    return {
        "page": page_num,
        "status": task.status.value,
        "content": page_content,
        "total_pages": task.total_pages
    }


@router.post("/tasks/{task_id}/pages/{page_num}/regenerate")
async def regenerate_page(
    task_id: str,
    page_num: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    重新生成指定页面的 Markdown 内容

    当用户对某页的识别结果不满意时，可以重新调用 LLM 进行识别

    参数:
        task_id: 任务ID
        page_num: 页码 (从 1 开始)

    返回:
        重新生成任务的确认信息
    """
    # 验证任务是否存在
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # 验证页码是否有效（添加合理的上限）
    if page_num < 1 or page_num > 10000:
        raise HTTPException(status_code=400, detail=f"Invalid page number: {page_num}")
    if task.total_pages and page_num > task.total_pages:
        raise HTTPException(status_code=400, detail=f"Page {page_num} exceeds total pages ({task.total_pages})")

    # 从持久化文件加载最新设置
    from .settings import load_settings_from_env
    settings = load_settings_from_env()
    model_name = settings.model
    concurrency = settings.concurrency
    api_key = settings.apiKey
    base_url = settings.baseUrl

    # 检查任务目录是否存在
    task_dir = os.path.join(UPLOAD_DIR, task_id)
    if not os.path.exists(task_dir):
        raise HTTPException(status_code=404, detail="Task directory not found")

    # 查找对应的页面图片文件
    page_image_path = os.path.join(task_dir, f"page_{page_num:04d}.jpg")
    if not os.path.exists(page_image_path):
        # 也可能尝试 .png 格式
        page_image_path = os.path.join(task_dir, f"page_{page_num:04d}.png")
        if not os.path.exists(page_image_path):
            raise HTTPException(status_code=404, detail=f"Page {page_num} image not found")

    # 启动后台任务重新生成该页面
    from src.worker.tasks import regenerate_single_page
    background_tasks.add_task(
        regenerate_single_page,
        task_id,
        page_num,
        str(page_image_path),
        model_name,
        api_key,
        base_url
    )

    return {
        "message": f"Page {page_num} regeneration started",
        "task_id": task_id,
        "page_num": page_num,
        "status": "regenerating"
    }

