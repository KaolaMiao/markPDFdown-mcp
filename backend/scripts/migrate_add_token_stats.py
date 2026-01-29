"""
数据库迁移：添加任务时间追踪和 Token 统计字段

添加字段：
- started_at: 任务开始时间
- completed_at: 任务完成时间
- input_tokens: 输入 token 总数
- output_tokens: 输出 token 总数
- total_tokens: 总 token 数
"""
import asyncio
import sys
from pathlib import Path

# 添加 src 目录到 Python 路径
backend_dir = Path(__file__).parent.parent
src_dir = backend_dir / "src"
sys.path.insert(0, str(src_dir))

from sqlalchemy import text
from src.db.database import AsyncSessionLocal


async def migrate():
    """执行数据库迁移"""
    print("=" * 60)
    print("数据库迁移：添加时间和 Token 统计字段")
    print("=" * 60)

    async with AsyncSessionLocal() as session:
        try:
            # 检查字段是否已存在
            result = await session.execute(text("PRAGMA table_info(tasks)"))
            columns = [row[1] for row in result.fetchall()]

            print("\n当前字段:", columns)

            # 添加 started_at
            if 'started_at' not in columns:
                print("\n添加字段: started_at")
                await session.execute(text(
                    "ALTER TABLE tasks ADD COLUMN started_at DATETIME"
                ))
                print("✅ started_at 字段添加成功")
            else:
                print("\n⚠️  started_at 字段已存在，跳过")

            # 添加 completed_at
            if 'completed_at' not in columns:
                print("\n添加字段: completed_at")
                await session.execute(text(
                    "ALTER TABLE tasks ADD COLUMN completed_at DATETIME"
                ))
                print("✅ completed_at 字段添加成功")
            else:
                print("\n⚠️  completed_at 字段已存在，跳过")

            # 添加 input_tokens
            if 'input_tokens' not in columns:
                print("\n添加字段: input_tokens")
                await session.execute(text(
                    "ALTER TABLE tasks ADD COLUMN input_tokens INTEGER DEFAULT 0"
                ))
                print("✅ input_tokens 字段添加成功")
            else:
                print("\n⚠️  input_tokens 字段已存在，跳过")

            # 添加 output_tokens
            if 'output_tokens' not in columns:
                print("\n添加字段: output_tokens")
                await session.execute(text(
                    "ALTER TABLE tasks ADD COLUMN output_tokens INTEGER DEFAULT 0"
                ))
                print("✅ output_tokens 字段添加成功")
            else:
                print("\n⚠️  output_tokens 字段已存在，跳过")

            # 添加 total_tokens
            if 'total_tokens' not in columns:
                print("\n添加字段: total_tokens")
                await session.execute(text(
                    "ALTER TABLE tasks ADD COLUMN total_tokens INTEGER DEFAULT 0"
                ))
                print("✅ total_tokens 字段添加成功")
            else:
                print("\n⚠️  total_tokens 字段已存在，跳过")

            await session.commit()

            # 验证迁移结果
            print("\n" + "=" * 60)
            print("迁移完成！验证结果：")
            print("=" * 60)

            result = await session.execute(text("PRAGMA table_info(tasks)"))
            all_columns = result.fetchall()
            print("\n所有字段：")
            for col in all_columns:
                print(f"  - {col[1]} ({col[2]})")

            print("\n✅ 数据库迁移成功完成！")

        except Exception as e:
            await session.rollback()
            print(f"\n❌ 迁移失败: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(migrate())
