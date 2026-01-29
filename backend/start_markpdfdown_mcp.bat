@echo off
REM MarkPDFdown MCP Server启动脚本 (使用虚拟环境 Python)
set API_BASE=https://p2m.384921.XYZ/api/v1
set PYTHONUNBUFFERED=1
cd /d "D:\MyTools\markPDFdown-mcp\backend"
.venv\Scripts\python.exe src/mcp_server.py
