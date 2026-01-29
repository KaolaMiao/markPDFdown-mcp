"""
修复历史任务的 total_pages 字段

遍历所有已完成的任务，根据 page_*.md 文件数量更新 total_pages
"""
import asyncio
import os
import sys
from pathlib import Path

# 添加 src 目录到 Python 路径
backend_dir = Path(__file__).parent.parent
src_dir = backend_dir / "src"
sys.path.insert(0, str(src_dir))

from src.db.database import AsyncSessionLocal
from src.db.models import Task, TaskStatus
from sqlalchemy import select

# UPLOAD_DIR 配置（需要与 routes.py 一致）
# 从 backend 目录查找 files/tasks
UPLOAD_DIR = backend_dir / "files" / "tasks"
if not UPLOAD_DIR.exists():
    # 如果不在 backend/files，尝试项目根目录的 files
    UPLOAD_DIR = backend_dir.parent / "files" / "tasks"

print(f"使用任务目录: {UPLOAD_DIR}")


async def fix_total_pages():
    """修复所有任务的 total_pages"""
    print("=" * 60)
    print("开始修复历史任务的 total_pages 字段")
    print("=" * 60)

    async with AsyncSessionLocal() as session:
        # 查询所有 COMPLETED 状态且 total_pages = 0 的任务
        result = await session.execute(
            select(Task)
            .where(Task.status == TaskStatus.COMPLETED)
            .where(Task.total_pages == 0)
        )
        tasks = result.scalars().all()

        print(f"\n找到 {len(tasks)} 个需要修复的任务\n")

        for task in tasks:
            task_dir = UPLOAD_DIR / task.id

            if not task_dir.exists():
                print(f"⚠️  任务 {task.id[:8]} 目录不存在，跳过")
                continue

            # 统计 page_*.md 文件数量
            page_files = list(task_dir.glob("page_*.md"))
            page_count = len(page_files)

            if page_count > 0:
                task.total_pages = page_count
                print(f"✅ 任务 {task.id[:8]} ({task.file_name}): {page_count} 页")
            else:
                print(f"⚠️  任务 {task.id[:8]} ({task.file_name}): 未找到 page 文件")

        # 提交更改
        await session.commit()
        print(f"\n✅ 数据库更新完成！")

        # 显示修复结果
        print("\n" + "=" * 60)
        print("修复结果统计")
        print("=" * 60)

        result = await session.execute(
            select(Task)
            .where(Task.status == TaskStatus.COMPLETED)
        )
        all_tasks = result.scalars().all()

        with_pages = [t for t in all_tasks if t.total_pages > 0]
        without_pages = [t for t in all_tasks if t.total_pages == 0]

        print(f"总已完成任务: {len(all_tasks)}")
        print(f"有页数信息: {len(with_pages)}")
        print(f"无页数信息: {len(without_pages)}")

        if with_pages:
            total_pages = sum(t.total_pages for t in with_pages)
            print(f"总页数: {total_pages}")


if __name__ == "__main__":
    asyncio.run(fix_total_pages())
