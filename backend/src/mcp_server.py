import asyncio
import os
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
import mcp.types as types

# Initialize Server
app = Server("markpdfdown-server")

API_BASE = os.getenv("API_BASE", "http://localhost:8000/api/v1")

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="convert_pdf",
            description="Convert a PDF file to Markdown using the MarkPDFdown Server. Uploads the file, waits for processing, and returns the markdown content.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Absolute path to the local PDF file to convert."
                    }
                },
                "required": ["file_path"]
            }
        ),
        types.Tool(
            name="list_tasks",
            description="List conversion tasks on the server. Useful for finding past tasks or checking status.",
            inputSchema={
                 "type": "object",
                 "properties": {
                     "limit": {"type": "integer", "description": "Number of tasks to return (default 10)", "default": 10},
                     "skip": {"type": "integer", "description": "Number of tasks to skip (default 0)", "default": 0}
                 }
            }
        ),
        types.Tool(
            name="get_task_content",
            description="Get the Markdown content of a specific task by ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "The UUID of the task"}
                },
                "required": ["task_id"]
            }
        ),
        types.Tool(
            name="download_file",
            description="Download the converted Markdown file for a specific task ID and save it to the specified local path.",
            inputSchema={
                "type": "object",
                "properties": {
                     "task_id": {"type": "string", "description": "The UUID of the task to download"},
                     "save_path": {"type": "string", "description": "The absolute path where the MD file should be saved (e.g., /status/output.md)"}
                },
                "required": ["task_id", "save_path"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    try:
        # 禁用系统代理 (trust_env=False)，防止因代理配置导致的 502 错误
        async with httpx.AsyncClient(timeout=300.0, trust_env=False, follow_redirects=True) as client:
            
            if name == "convert_pdf":
                file_path = arguments.get("file_path")
                if not file_path or not os.path.exists(file_path):
                    return [types.TextContent(type="text", text=f"Error: File not found: {file_path}")]

                # 1. Upload
                with open(file_path, "rb") as f:
                    # Explicitly set filename for httpx
                    filename = os.path.basename(file_path)
                    files = {"file": (filename, f)}
                    resp = await client.post(f"{API_BASE}/upload", files=files)
                    if resp.status_code != 200:
                         return [types.TextContent(type="text", text=f"Upload failed: {resp.text}")]
                    
                    data = resp.json()
                    task_id = data.get("id")
                
                # 2. Poll
                while True:
                    resp = await client.get(f"{API_BASE}/tasks/{task_id}")
                    if resp.status_code != 200:
                        return [types.TextContent(type="text", text=f"Polling failed: {resp.text}")]
                        
                    task_data = resp.json()
                    status = task_data.get("status")
                    
                    if status == "completed":
                        break
                    if status == "failed":
                         return [types.TextContent(type="text", text=f"Conversion failed: {task_data.get('error_message')}")]
                    
                    await asyncio.sleep(1)

                # 3. Download
                resp = await client.get(f"{API_BASE}/tasks/{task_id}/download")
                if resp.status_code != 200:
                     return [types.TextContent(type="text", text=f"Download failed: {resp.text}")]
                
                return [types.TextContent(type="text", text=resp.text)]

            elif name == "list_tasks":
                limit = arguments.get("limit", 10)
                skip = arguments.get("skip", 0)
                
                resp = await client.get(f"{API_BASE}/tasks?skip={skip}&limit={limit}")
                if resp.status_code != 200:
                    return [types.TextContent(type="text", text=f"List tasks failed: {resp.text}")]
                    
                data = resp.json()
                # data format: {"items": [...], "total": N} or just list depending on implementation
                # Based on previous fix, it returns {"items": [...], "total": ...}
                
                items = data.get("items", []) if isinstance(data, dict) else data
                
                # Format as readable list
                result_text = "Task List:\n"
                for task in items:
                    result_text += f"- ID: {task.get('id')}\n"
                    result_text += f"  File: {task.get('file_name') or 'Unknown'}\n"
                    result_text += f"  Status: {task.get('status')}\n"
                    result_text += f"  Created: {task.get('created_at')}\n"
                    
                return [types.TextContent(type="text", text=result_text)]

            elif name == "get_task_content":
                task_id = arguments.get("task_id")
                if not task_id:
                     return [types.TextContent(type="text", text="Error: task_id is required")]
                     
                resp = await client.get(f"{API_BASE}/tasks/{task_id}/download")
                if resp.status_code != 200:
                     return [types.TextContent(type="text", text=f"Get content failed: {resp.text}")]
                
                return [types.TextContent(type="text", text=resp.text)]

            elif name == "download_file":
                task_id = arguments.get("task_id")
                save_path = arguments.get("save_path")
                
                if not task_id:
                     return [types.TextContent(type="text", text="Error: task_id is required")]
                
                if not save_path:
                     return [types.TextContent(type="text", text="Error: save_path is required")]
                     
                # Reuse the download endpoint logic via internal API call
                resp = await client.get(f"{API_BASE}/tasks/{task_id}/download")
                if resp.status_code != 200:
                     return [types.TextContent(type="text", text=f"Download failed: {resp.text}")]
                
                # Write raw content to the specified path without processing
                try:
                    # Ensure directory exists
                    os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
                    
                    with open(save_path, "wb") as f:
                        f.write(resp.content)
                        
                    return [types.TextContent(type="text", text=f"Success: File saved to {save_path}")]
                except Exception as e:
                    return [types.TextContent(type="text", text=f"Error saving file: {str(e)}")]

            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
