import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List

# Import from core using expected path (assuming PYTHONPATH is set)
from markpdfdown.core.file_worker import create_worker
from markpdfdown.core.llm_client import LLMClient
from markpdfdown.config import config

logger = logging.getLogger(__name__)

import os

# ...

class SmartWorker:
    def __init__(self, model_name: str, concurrency: int = 2, api_key: str = None, base_url: str = None):
        self.concurrency = concurrency
        
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

    async def process_file(self, input_path: str) -> str:
        """
        Process a file using a streaming pipeline:
        Split to images via generator, and start LLM conversion immediately as images appear.
        """
        logger.info(f"Processing file (Streaming Mode): {input_path}")
        
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

        async def _wrapped_convert(index: int, img_path: str):
            async with semaphore:
                try:
                    # Wrap blocking _convert_one into thread for true async in loop
                    loop = asyncio.get_running_loop()
                    content = await loop.run_in_executor(None, self._convert_one, img_path)
                    # Simple data cleaning to prevent mojibake/overflow issues
                    if not content or len(content.strip()) == 0:
                        return index, ""
                    return index, content.strip()
                except Exception as e:
                    logger.error(f"Task failed for page {index+1}: {e}")
                    return index, f"<!-- Error processing page {index+1} -->"

        # Read specific pages from generator (Streaming start)
        try:
            for i, img_path in enumerate(image_gen):
                logger.info(f"Page {i+1} rendered. Dispatching recognition task...")
                task = asyncio.create_task(_wrapped_convert(i, img_path))
                tasks.append(task)
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
        
        # Build final markdown
        markdown_parts = []
        for _, content in sorted_results:
            if content:
                markdown_parts.append(content)
        
        final_markdown = "\n\n".join(markdown_parts)
        logger.info(f"File processing complete. Total parts: {len(markdown_parts)}")
        
        return final_markdown

    def _convert_one(self, image_path: str) -> str:
        """
        Single image conversion (runs in thread)
        """
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
            return self.llm_client.completion(
                user_message=user_prompt,
                system_prompt=system_prompt,
                image_paths=[image_path],
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                retry_times=config.retry_times # Reusing config for now
            )
        except Exception as e:
            logger.error(f"Error converting {image_path}: {e}")
            return ""
