# To run this code you need to install the following dependencies:
# pip install google-genai

import base64
import os
from google import genai
from google.genai import types


def generate():
    # 从环境变量或直接设置 API key
    api_key = "AIzaSyAezvEo7_PaBggLfseOTIflYLBUEWLWsEc"
    client = genai.Client(
        api_key=api_key,
    )

    model = "gemini-3-flash-preview"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""Hello, please reply with 'API is working!'"""),
            ],
        ),
    ]

    print(f"测试 Gemini API...")
    print(f"模型: {model}")
    print(f"API Key: {api_key[:20]}...")
    print("-" * 60)

    try:
        response = client.models.generate_content(
            model=model,
            contents=contents,
        )
        print(f"✅ 成功!")
        print(f"响应: {response.text}")
    except Exception as e:
        print(f"❌ 失败: {e}")


if __name__ == "__main__":
    generate()
