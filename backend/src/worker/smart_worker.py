import asyncio
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import List
from pathlib import Path

# 添加markpdfdown_core到Python路径
backend_dir = Path(__file__).parent.parent.parent
core_src_dir = backend_dir.parent / "markpdfdown_core" / "src"
if str(core_src_dir) not in sys.path:
    sys.path.insert(0, str(core_src_dir))

# Import from core using expected path (assuming PYTHONPATH is set)
from markpdfdown.core.file_worker import create_worker
from markpdfdown.core.llm_client import LLMClient
from markpdfdown.config import config

logger = logging.getLogger(__name__)

# ...

class SmartWorker:
    def __init__(self, model_name: str, concurrency: int = 2, api_key: str = None, base_url: str = None, progress_callback=None):
        self.concurrency = concurrency
        self.progress_callback = progress_callback  # 进度回调函数

        # 处理模型名称格式，确保符合 litellm 规范
        # litellm 需要 provider/model 格式，如 gemini/gemini-2.0-flash
        if model_name.startswith("gemini") and not model_name.startswith("gemini/"):
            # 为 Gemini 模型添加 gemini/ 前缀
            self.model_name = f"gemini/{model_name}"
        elif model_name.startswith("claude") and not model_name.startswith("anthropic/"):
            # Claude 模型可以直接使用，litellm 会自动处理
            self.model_name = model_name
        else:
            self.model_name = model_name

        # Determine provider to set correct env var
        # Basic mapping for common providers
        if api_key:
            if model_name.startswith("gpt"):
                os.environ["OPENAI_API_KEY"] = api_key
            elif model_name.startswith("claude"):
                os.environ["ANTHROPIC_API_KEY"] = api_key
            elif model_name.startswith("gemini"):
                os.environ["GEMINI_API_KEY"] = api_key
            elif "ollama" in model_name:
                pass # Ollama usually doesn't need key, or used in base_url
            else:
                # Default fallback or custom provider
                os.environ["OPENAI_API_KEY"] = api_key

        if base_url:
            os.environ["OPENAI_API_BASE"] = base_url

        self.llm_client = LLMClient(self.model_name)

    async def process_file(self, input_path: str, task_id: str = None) -> tuple[str, int]:
        """
        Process a file using a streaming pipeline with per-page markdown saving.

        架构改进:
        1. 每转换完一页，立即保存该页面的 markdown 文件 (page_0001.md)
        2. 实现实时预览 - 每页完成后即可查看
        3. 最后合并所有页面为完整的 markdown 文件

        Args:
            input_path: 输入文件路径
            task_id: 任务ID (用于进度回调)

        Returns:
            (markdown_content, total_pages): Markdown 内容和总页数
        """
        logger.info(f"Processing file (Streaming Mode with Per-Page Saving): {input_path}")

        # 获取输出目录
        output_dir = os.path.dirname(input_path)

        try:
             worker = create_worker(input_path)
             # image_gen is a generator (one page at a time)
             image_gen = worker.convert_to_images()
        except Exception as e:
            logger.error(f"Failed to initialize worker: {e}")
            raise

        # Parallel conversion with Semaphore to control concurrency
        tasks = []
        semaphore = asyncio.Semaphore(self.concurrency)
        completed_count = 0
        total_pages = 0
        total_input_tokens = 0
        total_output_tokens = 0

        async def _wrapped_convert(index: int, img_path: str):
            nonlocal completed_count, total_input_tokens, total_output_tokens
            async with semaphore:
                try:
                    # Wrap blocking _convert_one into thread for true async in loop
                    loop = asyncio.get_running_loop()
                    result = await loop.run_in_executor(None, self._convert_one, img_path)

                    # Extract content and tokens from result
                    if hasattr(result, 'content'):
                        content = result.content
                        total_input_tokens += result.input_tokens
                        total_output_tokens += result.output_tokens
                    else:
                        # 兼容旧版本，如果返回的是字符串
                        content = result

                    # Simple data cleaning to prevent mojibake/overflow issues
                    if not content or len(content.strip()) == 0:
                        content = ""

                    content = content.strip()

                    # ✨ 架构改进: 立即保存每页的 markdown 文件
                    # 这样前端可以实时获取和预览每个页面的内容
                    page_num = index + 1
                    page_md_path = os.path.join(output_dir, f"page_{page_num:04d}.md")

                    try:
                        # 使用原子操作：先写临时文件，再重命名
                        page_md_tmp = page_md_path + ".tmp"
                        with open(page_md_tmp, "w", encoding="utf-8") as f:
                            f.write(content)
                        # 原子性重命名（OS 级别的原子操作）
                        os.replace(page_md_tmp, page_md_path)
                        logger.info(f"Page {page_num} markdown saved to: {page_md_path}")
                    except Exception as e:
                        logger.error(f"Failed to save page {page_num} markdown: {e}")

                    # 更新进度
                    completed_count += 1
                    if self.progress_callback and task_id:
                        progress = (completed_count / total_pages * 100) if total_pages > 0 else 0
                        await self.progress_callback(
                            task_id=task_id,
                            current_page=completed_count,
                            total_pages=total_pages,
                            progress=progress,
                            status="processing"
                        )

                    return index, content
                except Exception as e:
                    logger.error(f"Task failed for page {index+1}: {e}")
                    return index, f"<!-- Error processing page {index+1} -->"

        # Read specific pages from generator (Streaming start)
        try:
            for i, img_path in enumerate(image_gen):
                total_pages = i + 1  # 更新总页数
                logger.info(f"Page {i+1} rendered. Dispatching recognition task...")
                task = asyncio.create_task(_wrapped_convert(i, img_path))
                tasks.append(task)

                # 发送初始进度
                if self.progress_callback and task_id and i == 0:
                    await self.progress_callback(
                        task_id=task_id,
                        current_page=0,
                        total_pages=total_pages,
                        progress=0,
                        status="processing"
                    )
        except Exception as e:
            logger.error(f"Error during image generation: {e}")

        if not tasks:
            logger.warning("No pages were generated for processing.")
            return ""

        # Wait for all tasks to complete
        logger.info(f"All {len(tasks)} pages dispatched. Waiting for recognition results...")
        results = await asyncio.gather(*tasks)

        # Sort results by index to ensure strictly correct order
        # This prevents the "out of order" or "interleaved" data corruption
        sorted_results = sorted(results, key=lambda x: x[0])

        # ✨ 改进的合并逻辑:
        # 1. 从保存的每页 markdown 文件中读取内容
        # 2. 在每页之间添加页码分隔符
        # 3. 合并为最终的 markdown 文件
        markdown_parts = []
        for index, _ in sorted_results:
            page_num = index + 1
            page_md_path = os.path.join(output_dir, f"page_{page_num:04d}.md")

            try:
                # 读取每页保存的 markdown 文件
                with open(page_md_path, "r", encoding="utf-8") as f:
                    page_content = f.read()

                # 添加页码分隔符
                page_marker = f"\n\n<!-- PAGE {page_num} -->\n\n"
                markdown_parts.append(page_marker + page_content)

                logger.info(f"Page {page_num} content loaded for merging")
            except Exception as e:
                logger.error(f"Failed to read page {page_num} markdown: {e}")

        # 合并所有页面
        final_markdown = "".join(markdown_parts)
        logger.info(f"File processing complete. Total pages merged: {len(sorted_results)}")

        # 发送完成进度
        if self.progress_callback and task_id:
            await self.progress_callback(
                task_id=task_id,
                current_page=total_pages,
                total_pages=total_pages,
                progress=100,
                status="completed"
            )

        logger.info(f"Processing completed. Total pages: {total_pages}")
        logger.info(f"Token usage - Input: {total_input_tokens}, Output: {total_output_tokens}, Total: {total_input_tokens + total_output_tokens}")
        return final_markdown, total_pages, total_input_tokens, total_output_tokens

    def _convert_one(self, image_path: str) -> 'CompletionResult':
        """
        Single image conversion (runs in thread)

        Returns:
            CompletionResult with content and token usage
        """
        logger.info(f"🔄 Starting conversion for: {image_path}")
        logger.info(f"📝 Using model: {self.model_name}")

        system_prompt = """
You are a helpful assistant that can convert images to Markdown format. You are given an image, and you need to convert it to Markdown format. Please output the Markdown content only, without any other text.
"""
        user_prompt = """
Below is the image of one page of a document, please read the content in the image and transcribe it into plain Markdown format. Please note:
1. Identify heading levels, text styles, formulas, and the format of table rows and columns
2. Mathematical formulas should be transcribed using LaTeX syntax, ensuring consistency with the original
3. Please output the Markdown content only, without any other text.
"""
        try:
            logger.info(f"📤 Calling LLM API with image: {image_path}")
            result = self.llm_client.completion(
                user_message=user_prompt,
                system_prompt=system_prompt,
                image_paths=[image_path],
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                retry_times=config.retry_times # Reusing config for now
            )
            logger.info(f"✅ LLM API call successful for {image_path}, result length: {len(result.content) if result and result.content else 0}")
            logger.info(f"📊 Tokens: Input={result.input_tokens}, Output={result.output_tokens}, Total={result.total_tokens}")
            return result
        except Exception as e:
            logger.error(f"❌ Error converting {image_path}: {e}")
            logger.error(f"❌ Exception type: {type(e).__name__}")
            # 返回空的 CompletionResult 而不是空字符串
            from markpdfdown.core.llm_client import CompletionResult
            return CompletionResult(content="")
