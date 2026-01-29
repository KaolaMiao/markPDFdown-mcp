import asyncio
import logging
from .celery_app import celery_app
from .smart_worker import SmartWorker
from src.db.database import AsyncSessionLocal
from src.db.models import Task, TaskStatus

logger = logging.getLogger(__name__)

async def run_async_process(task_id: str, input_path: str, model_name: str, concurrency: int = 2, api_key: str = None, base_url: str = None):
    logger.info(f"Starting async process for task {task_id}")
    
    # 1. Update status to PROCESSING
    async with AsyncSessionLocal() as session:
        task = await session.get(Task, task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return
        
        task.status = TaskStatus.PROCESSING
        await session.commit()
    
    try:
        # 2. Run Worker
        worker = SmartWorker(model_name=model_name, concurrency=concurrency, api_key=api_key, base_url=base_url)
        markdown_content = await worker.process_file(input_path)
        
        # 3. Save Result & Update COMPLETED
        # 输出文件使用原始 PDF 文件名，扩展名改为 .md
        import os
        pdf_dir = os.path.dirname(input_path)
        pdf_name = os.path.basename(input_path)
        md_name = os.path.splitext(pdf_name)[0] + ".md"
        output_file = os.path.join(pdf_dir, md_name)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown_content)
            
        async with AsyncSessionLocal() as session:
            task = await session.get(Task, task_id)
            if task:
                task.status = TaskStatus.COMPLETED
                task.result_path = output_file
                await session.commit()
                
        logger.info(f"Task {task_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        async with AsyncSessionLocal() as session:
            task = await session.get(Task, task_id)
            if task:
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                await session.commit()
        raise e

@celery_app.task(bind=True)
def convert_pdf_task(self, task_id: str, input_path: str, model_name: str = "gpt-4o", concurrency: int = 2, api_key: str = None, base_url: str = None):
    """
    Celery task to convert PDF to Markdown
    """
    # Run async function in blocking manner
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    loop.run_until_complete(run_async_process(task_id, input_path, model_name, concurrency, api_key, base_url))
