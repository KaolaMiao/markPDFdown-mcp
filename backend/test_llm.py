"""
测试 LLM API 调用是否正常
"""
import asyncio
import os
import sys

# 添加路径
backend_dir = r"D:\MyTools\markPDFdown-mcp\backend"
sys.path.insert(0, backend_dir)
sys.path.insert(0, backend_dir + r"\src")
core_dir = r"D:\MyTools\markPDFdown-mcp\markpdfdown_core\src"
sys.path.insert(0, core_dir)

from markpdfdown.core.llm_client import LLMClient

async def test_llm():
    """测试 LLM 调用"""

    # 从环境变量读取配置
    model_name = "gemini-3.0-flash-exp"
    api_key = os.getenv("API_KEY", "")

    # ⚠️ 重要：模型名称需要添加 gemini/ 前缀
    if model_name.startswith("gemini") and not model_name.startswith("gemini/"):
        model_name = f"gemini/{model_name}"

    print(f"原始模型名: gemini-3.0-flash-exp")
    print(f"格式化模型: {model_name}")
    print(f"API Key: {api_key[:20]}...{len(api_key)} digits")

    if not api_key:
        print("❌ API_KEY 未设置！")
        return

    # 设置环境变量
    os.environ["GEMINI_API_KEY"] = api_key

    # 创建 LLM 客户端
    client = LLMClient(model_name)

    # 准备一个简单的测试图片（使用 base64 编码的小图片）
    # 创建一个 1x1 像素的白色图片
    import base64
    test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAfFcSJAAAADUlEQVR42mNk+M9QD0ADYk2v33z8gAAAABJRU5ErkJggg=="

    # 解码并保存为临时文件
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(base64.b64decode(test_image_base64))
        test_image_path = f.name

    print(f"\n测试图片路径: {test_image_path}")

    try:
        # 调用 LLM
        print("\n正在调用 LLM API...")
        result = client.completion(
            user_message="请识别这张图片中的内容（这是一个简单的测试图片）",
            system_prompt="你是一个图片识别助手。",
            image_paths=[test_image_path],
            temperature=0.3,
            max_tokens=100,
            retry_times=1
        )

        print(f"\n✅ LLM 调用成功！")
        print(f"返回结果:\n{result}")

        return True

    except Exception as e:
        print(f"\n❌ LLM 调用失败！")
        print(f"错误信息: {e}")
        print(f"错误类型: {type(e).__name__}")

        # 检查是否是认证错误
        error_str = str(e)
        if "API key" in error_str and ("expired" in error_str or "INVALID" in error_str):
            print("\n🔑 错误原因：API Key 无效或已过期")
            print("请检查：")
            print("1. API Key 是否正确")
            print("2. API Key 是否已启用")
            print("3. 账户是否有配额")
            return False
        elif "quota" in error_str.lower():
            print("\n📊 错误原因：API 配额已用完")
            return False
        else:
            print(f"\n❓ 其他错误：{error_str}")
            return False

    finally:
        # 清理临时文件
        import os
        if os.path.exists(test_image_path):
            os.remove(test_image_path)

if __name__ == "__main__":
    # 加载 .env 文件
    from dotenv import load_dotenv
    load_dotenv()

    print("=" * 60)
    print("测试 LLM API 调用")
    print("=" * 60)

    success = asyncio.run(test_llm())

    print("\n" + "=" * 60)
    if success:
        print("✅ 测试通过！LLM API 可以正常使用")
    else:
        print("❌ 测试失败！请检查 API Key 配置")
    print("=" * 60)
