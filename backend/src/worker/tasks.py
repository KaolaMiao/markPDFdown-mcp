import asyncio
import logging
from .celery_app import celery_app
from .smart_worker import SmartWorker
from src.db.database import AsyncSessionLocal
from src.db.models import Task, TaskStatus
from src.api.sse_manager import sse_manager

logger = logging.getLogger(__name__)

async def progress_callback(task_id: str, current_page: int, total_pages: int, progress: float, status: str):
    """进度回调函数 - 通过SSE发送进度更新"""
    try:
        await sse_manager.broadcast_progress(
            task_id=task_id,
            current_page=current_page,
            total_pages=total_pages,
            progress=progress,
            status=status
        )
        logger.debug(f"Progress update for task {task_id}: {progress:.1f}% ({current_page}/{total_pages})")
    except Exception as e:
        logger.error(f"Failed to send progress update: {e}")



# 全局并发控制信号量 - 限制同时进行的任务数
# 针对 2核4G 环境，默认限制为 2
# 可以通过环境变量 MAX_CONCURRENT_TASKS 进行调整
import os
MAX_CONCURRENT_TASKS = int(os.getenv("MAX_CONCURRENT_TASKS", "2"))
task_semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

async def run_async_process(task_id: str, input_path: str, model_name: str, concurrency: int = 2, api_key: str = None, base_url: str = None):
    # 使用信号量限制并发任务数
    async with task_semaphore:
        logger.info(f"Acquired semaphore for task {task_id}. Active tasks: {MAX_CONCURRENT_TASKS - task_semaphore._value}")
        await _run_async_process_internal(task_id, input_path, model_name, concurrency, api_key, base_url)

async def _run_async_process_internal(task_id: str, input_path: str, model_name: str, concurrency: int = 2, api_key: str = None, base_url: str = None):

    logger.info(f"Starting async process for task {task_id}")
    logger.info(f"Task parameters: Input path: {input_path}, Model: {model_name}, Concurrency: {concurrency}")

    from datetime import datetime

    # 1. Update status to PROCESSING and set started_at
    async with AsyncSessionLocal() as session:
        task = await session.get(Task, task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return

        task.status = TaskStatus.PROCESSING
        task.started_at = datetime.utcnow()
        await session.commit()
        logger.info(f"Task {task_id} status updated to PROCESSING")

    try:
        # 2. Run Worker with progress callback
        logger.info(f"SmartWorker initialized")
        worker = SmartWorker(
            model_name=model_name,
            concurrency=concurrency,
            api_key=api_key,
            base_url=base_url,
            progress_callback=progress_callback
        )
        logger.info(f"Starting file processing...")
        markdown_content, total_pages, input_tokens, output_tokens = await worker.process_file(input_path, task_id=task_id)

        logger.info(f"Processing completed. Total pages: {total_pages}. Tokens: Input={input_tokens}, Output={output_tokens}, Total={input_tokens + output_tokens}")

        # 3. Save Result & Update COMPLETED
        # 输出文件使用原始 PDF 文件名，扩展名改为 .md
        import os
        pdf_dir = os.path.dirname(input_path)
        pdf_name = os.path.basename(input_path)
        md_name = os.path.splitext(pdf_name)[0] + ".md"
        output_file = os.path.join(pdf_dir, md_name)

        # 使用原子操作：先写临时文件，再重命名
        output_tmp = output_file + ".tmp"
        with open(output_tmp, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        os.replace(output_tmp, output_file)

        async with AsyncSessionLocal() as session:
            task = await session.get(Task, task_id)
            if task:
                task.status = TaskStatus.COMPLETED
                task.total_pages = total_pages  # 更新总页数
                task.result_path = output_file
                task.completed_at = datetime.utcnow()  # 设置完成时间
                task.input_tokens = input_tokens  # 更新 token 统计
                task.output_tokens = output_tokens
                task.total_tokens = input_tokens + output_tokens
                await session.commit()

        logger.info(f"Task {task_id} completed successfully. Duration: {task.completed_at - task.started_at}")

    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        async with AsyncSessionLocal() as session:
            task = await session.get(Task, task_id)
            if task:
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                await session.commit()
        raise e


async def regenerate_single_page(
    task_id: str,
    page_num: int,
    image_path: str,
    model_name: str,
    api_key: str = None,
    base_url: str = None
):
    """
    重新生成单个页面的 Markdown 内容，并重新合并所有页面

    Args:
        task_id: 任务ID
        page_num: 页码
        image_path: 页面图片路径
        model_name: 模型名称
        api_key: API密钥
        base_url: API基础URL
    """
    logger.info(f"Regenerating page {page_num} for task {task_id}")

    import os
    from pathlib import Path
    task_dir = Path(os.path.dirname(image_path))

    # 用于跟踪 token 使用
    total_tokens_used = 0

    try:
        # 初始化 SmartWorker（不需要 progress_callback）
        worker = SmartWorker(
            model_name=model_name,
            concurrency=1,  # 单页并发为1
            api_key=api_key,
            base_url=base_url,
            progress_callback=None  # 单页重新生成不需要进度回调
        )

        # 1. 转换单页 - 使用 _convert_one 方法而不是 process_file
        # _convert_one 是同步方法，需要在线程池中运行
        import asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, worker._convert_one, image_path)

        # 提取 markdown 内容和 token 使用
        if hasattr(result, 'content'):
            page_markdown = result.content
        else:
            page_markdown = str(result)

        # 统计 token 使用
        if hasattr(result, 'total_tokens'):
            total_tokens_used += result.total_tokens

        # 2. 保存单页 markdown 文件（使用原子操作）
        page_md_path = task_dir / f"page_{page_num:04d}.md"
        page_md_tmp = task_dir / f"page_{page_num:04d}.md.tmp"

        # 先写入临时文件
        with open(page_md_tmp, "w", encoding="utf-8") as f:
            f.write(page_markdown)

        # 原子性重命名（OS 级别的原子操作）
        os.replace(page_md_tmp, page_md_path)
        logger.info(f"Page {page_num} markdown saved to {page_md_path}")

        # 3. 查找所有页面文件并按顺序合并（使用严格的模式匹配）
        # 使用严格的4位数字模式匹配，避免匹配到用户上传的其他文件
        page_files = sorted(task_dir.glob("page_[0-9][0-9][0-9][0-9].md"))
        if not page_files:
            raise Exception(f"No page files found in {task_dir}")

        logger.info(f"Found {len(page_files)} page files to merge")

        # 4. 合并所有页面
        merged_parts = []
        for page_file in page_files:
            try:
                with open(page_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # 提取页码（添加错误处理）
                try:
                    page_num_from_file = int(page_file.stem.split("_")[1])
                    merged_parts.append((page_num_from_file, content))
                    logger.debug(f"Loaded page {page_num_from_file} from {page_file.name}")
                except (ValueError, IndexError) as e:
                    logger.error(f"Invalid page file format: {page_file.name}: {e}")
                    continue  # 跳过格式错误的文件

            except Exception as e:
                logger.error(f"Failed to read {page_file}: {e}")

        # Merging pages in order
        merged_parts.sort(key=lambda x: x[0])

        # 5. 构建最终 markdown（添加页码分隔符）
        final_markdown = ""
        for idx, (pnum, content) in enumerate(merged_parts):
            final_markdown += f"\n\n<!-- Page {pnum} -->\n\n"
            final_markdown += content
            if idx < len(merged_parts) - 1:
                final_markdown += "\n\n---\n\n"  # 页面分隔符

        # 6. 保存到最终的合并文件
        # 查找原始 PDF 文件名
        pdf_files = list(task_dir.glob("*.pdf"))
        if pdf_files:
            pdf_name = pdf_files[0].stem  # 不含扩展名
            output_file = task_dir / f"{pdf_name}.md"

            # 使用原子操作保存
            output_tmp = task_dir / f"{pdf_name}.md.tmp"
            with open(output_tmp, "w", encoding="utf-8") as f:
                f.write(final_markdown)
            os.replace(output_tmp, output_file)

            logger.info(f"Merged markdown saved to: {output_file}")
        else:
            logger.warning(f"No PDF file found in {task_dir}, skipping merge")

        logger.info(f"Page {page_num} regeneration and merge completed")

        # 7. 更新数据库中的 token 统计
        if total_tokens_used > 0:
            from src.db.database import AsyncSessionLocal
            from src.db.models import Task

            try:
                async with AsyncSessionLocal() as session:
                    task = await session.get(Task, task_id)
                    if task:
                        # 累加所有 token 字段，保持数据一致性
                        task.input_tokens = (task.input_tokens or 0) + (result.input_tokens or 0)
                        task.output_tokens = (task.output_tokens or 0) + (result.output_tokens or 0)
                        task.total_tokens = (task.total_tokens or 0) + total_tokens_used
                        await session.commit()
                        logger.info(f"Updated tokens for task {task_id}")
            except Exception as db_error:
                logger.error(f"❌ Failed to update database for task {task_id}: {db_error}")
                # 不抛出异常，因为文件已经保存成功

    except Exception as e:
        logger.error(f"Failed to regenerate page {page_num}: {e}")
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
