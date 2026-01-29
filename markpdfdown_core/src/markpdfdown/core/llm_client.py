"""
LLM client using LiteLLM for unified API access
"""

import base64
import logging
import time
from typing import Optional
from dataclasses import dataclass

import litellm
from litellm import completion

logger = logging.getLogger(__name__)


@dataclass
class CompletionResult:
    """LLM completion 结果"""
    content: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class LLMClient:
    """
    Unified LLM client using LiteLLM
    Supports OpenAI and OpenRouter automatically
    """

    def __init__(self, model_name: str):
        """
        Initialize LLM client

        Args:
            model_name: Model name (e.g., "gpt-4o", "openrouter/anthropic/claude-3.5-sonnet")
        """
        self.model_name = model_name

        # Configure LiteLLM logging
        litellm.set_verbose = True  # 启用详细日志用于调试

        # 设置 litellm 日志级别
        import logging
        logging.getLogger("litellm").setLevel(logging.DEBUG)

    def completion(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        image_paths: Optional[list[str]] = None,
        temperature: float = 0.3,
        max_tokens: int = 8192,
        retry_times: int = 3,
    ) -> CompletionResult:
        """
        Create chat completion with multimodal support

        Args:
            user_message: User message content
            system_prompt: System prompt (optional)
            image_paths: List of image paths (optional)
            temperature: Generation temperature
            max_tokens: Maximum number of tokens
            retry_times: Number of retries

        Returns:
            CompletionResult with content and token usage
        """
        # Build user content with text and images
        user_content = [{"type": "text", "text": user_message}]

        if image_paths:
            for img_path in image_paths:
                base64_image = self._encode_image(img_path)
                user_content.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    }
                )

        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_content})

        # Retry mechanism
        for attempt in range(retry_times):
            try:
                response = completion(
                    model=self.model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    # Add custom headers for tracking
                    extra_headers={
                        "X-Title": "MarkPDFdown",
                        "HTTP-Referer": "https://github.com/MarkPDFdown/markpdfdown.git",
                    },
                )

                if not response.choices:
                    raise Exception("No response from API")

                # 提取 token 使用情况
                usage = response.usage
                input_tokens = usage.prompt_tokens if usage else 0
                output_tokens = usage.completion_tokens if usage else 0
                total_tokens = usage.total_tokens if usage else (input_tokens + output_tokens)

                return CompletionResult(
                    content=response.choices[0].message.content,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens
                )

            except Exception as e:
                logger.error(
                    f"API request failed (attempt {attempt + 1}/{retry_times}): {str(e)}"
                )
                if attempt < retry_times - 1:
                    # Wait before retry
                    time.sleep(0.5 * (attempt + 1))
                else:
                    raise e

        return ""

    def _encode_image(self, image_path: str) -> str:
        """
        Encode image to base64 string

        Args:
            image_path: Path to image file

        Returns:
            Base64 encoded image string
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
