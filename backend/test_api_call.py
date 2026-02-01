"""测试 LLM API 调用"""
import os
import sys
from pathlib import Path

# 设置路径
backend_dir = Path(__file__).parent
core_src_dir = backend_dir.parent / "markpdfdown_core" / "src"
if str(core_src_dir) not in sys.path:
    sys.path.insert(0, str(core_src_dir))

from markpdfdown.core.llm_client import LLMClient

# 设置 API key - 从环境变量读取
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("请设置 GEMINI_API_KEY 环境变量")
os.environ["GEMINI_API_KEY"] = api_key

# 测试不同的模型名称格式
model_names = [
    "gemini-3.0-flash-exp",  # 当前配置
    "gemini-2.0-flash-exp",  # 可能的正确名称
    "gemini/gemini-2.0-flash-exp",  # 带 provider 前缀
]

print("测试 API 调用...")
print(f"API Key: {api_key[:20]}...")
print(f"GEMINI_API_KEY env: {os.environ.get('GEMINI_API_KEY', 'NOT SET')[:20]}...")
print()

for model_name in model_names:
    print(f"\n{'='*60}")
    print(f"测试模型: {model_name}")
    print(f"{'='*60}")

    try:
        client = LLMClient(model_name)
        result = client.completion(
            user_message="Hello, please reply with 'API working'",
            system_prompt="You are a helpful assistant.",
            temperature=0.3,
            max_tokens=50,
            retry_times=1
        )
        print(f"✅ 成功! 结果: {result[:100]}")
    except Exception as e:
        print(f"❌ 失败: {str(e)}")
