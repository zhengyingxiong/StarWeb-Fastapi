import os
import sys
import asyncio
import bcrypt

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from tortoise import Tortoise
from app.models.user import User
from app.models.rbac import Role, UserRole  # Import Role and UserRole models
from app.core.events.database import TORTOISE_ORM

def hash_password(password: str) -> str:
    """使用bcrypt加密密码"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()

async def create_admin_user():
    # 初始化数据库连接
    await Tortoise.init(config=TORTOISE_ORM)
    
    try:
        # Check if admin role exists, if not create it
        admin_role = await Role.get_or_none(code="admin")
        if not admin_role:
            admin_role = await Role.create(name="Administrator", code="admin", description="System Administrator Role", is_system=True)
            print("管理员角色创建成功")

        # Create admin user if one doesn't exist
        admin_user = await User.get_or_none(username="admin")
        if not admin_user:
            admin_user = await User.create(
                username="admin",
                password_hash=hash_password("123456"),
                email="admin@example.com",
                is_active=True,
                is_superadmin=True
            )

            # Assign admin role to admin user
            await UserRole.create(user=admin_user, role=admin_role)
            print("管理员用户创建成功，并分配了管理员角色")
        else:
            print("管理员用户已经存在，跳过创建")


    except Exception as e:
        print(f"创建管理员用户失败: {str(e)}")
    finally:
        # 关闭数据库连接
        await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(create_admin_user())