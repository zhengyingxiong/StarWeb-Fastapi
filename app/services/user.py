# app/services/user.py

from typing import Optional, List, Dict, Any
from tortoise.expressions import Q

from app.models.user import User
# 保持 UserCreate 的导入，因为 admin_create_user 需要它
from app.schemas.user import UserCreate, UserUpdate, UserRegisterRequest
from app.core.security.token import get_password_hash, verify_password

class UserService:
    """
    用户服务类
    处理所有与用户相关的业务逻辑
    """

    @staticmethod
    async def create_user(user_data: UserRegisterRequest) -> User: # 这个方法用于注册
        """
        创建新用户 (注册)
        :param user_data: 用户注册数据 (UserRegisterRequest)
        :return: 创建的用户对象
        :raises: ValueError 当用户名或邮箱已存在时
        """
        if await User.filter(username=user_data.username).exists():
            raise ValueError("用户名已存在")
        if await User.filter(email=user_data.email).exists():
            raise ValueError("邮箱已存在")

        user = await User.create(
            username=user_data.username,
            email=user_data.email,
            password_hash=get_password_hash(user_data.password),
            is_active=True # 注册用户默认激活
        )
        return user

    @staticmethod
    async def admin_create_user(user_data: UserCreate) -> User: # 新增这个方法用于管理员创建
        """
        管理员创建新用户
        :param user_data: 用户创建数据 (UserCreate)
        :return: 创建的用户对象
        :raises: ValueError 当用户名或邮箱已存在时
        """
        if await User.filter(username=user_data.username).exists():
            raise ValueError("用户名已存在")
        if await User.filter(email=user_data.email).exists():
            raise ValueError("邮箱已存在")

        user = await User.create(
            username=user_data.username,
            email=user_data.email,
            password_hash=get_password_hash(user_data.password),
            is_active=user_data.is_active # 使用 UserCreate 中的 is_active 值
        )
        return user


    # ... 其他方法 (update_user, delete_user, get_user, list_users, change_password) ...
    @staticmethod
    async def update_user(user_id: int, user_data: UserUpdate) -> User:
        """
        更新用户信息
        :param user_id: 用户ID
        :param user_data: 更新的用户数据
        :return: 更新后的用户对象
        :raises: ValueError 当用户不存在或用户名/邮箱已被其他用户使用时
        """
        user = await User.get_or_none(id=user_id)
        if not user:
            raise ValueError("用户不存在")
        update_data = user_data.model_dump(exclude_unset=True)
        if "username" in update_data:
            exists = await User.filter(
                username=update_data["username"]
            ).exclude(id=user_id).exists()
            if exists:
                raise ValueError("用户名已存在")
        if "email" in update_data:
            exists = await User.filter(
                email=update_data["email"]
            ).exclude(id=user_id).exists()
            if exists:
                raise ValueError("邮箱已存在")
        if "password" in update_data:
            update_data["password_hash"] = get_password_hash(update_data.pop("password"))

        await user.update_from_dict(update_data)
        await user.save()
        return user


    @staticmethod
    async def delete_user(user_id: int) -> None:
        """
        删除用户
        :param user_id: 用户ID
        :raises: ValueError 当用户不存在时
        """
        user = await User.get_or_none(id=user_id)
        if not user:
            raise ValueError("用户不存在")
        await user.delete()

    @staticmethod
    async def get_user(user_id: int) -> User:
        """
        获取用户详情
        :param user_id: 用户ID
        :return: 用户对象
        :raises: ValueError 当用户不存在时
        """
        user = await User.get_or_none(id=user_id)
        if not user:
            raise ValueError("用户不存在")
        return user

    @staticmethod
    async def list_users(
        page: int = 1,
        page_size: int = 10,
        username: Optional[str] = None,
        email: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> tuple[List[User], int]:
        """
        获取用户列表
        :param page: 页码
        :param page_size: 每页数量
        :param username: 用户名过滤
        :param email: 邮箱过滤
        :param is_active: 是否激活过滤
        :return: (用户列表, 总数)
        """
        query = User.all()
        if username:
            query = query.filter(username__icontains=username)
        if email:
            query = query.filter(email__icontains=email)
        if is_active is not None:
            query = query.filter(is_active=is_active)
        total = await query.count()
        users = await query.offset((page - 1) * page_size).limit(page_size)
        return users, total

    @staticmethod
    async def change_password(
        user_id: int, old_password: str, new_password: str, confirm_password: str
    ) -> None:
        """
        更改用户密码
        :param user_id: 用户ID
        :param old_password: 旧密码
        :param new_password: 新密码
        :param confirm_password: 确认新密码
        :raises: ValueError 当用户不存在、旧密码错误或新密码不一致时
        """
        user = await User.get_or_none(id=user_id)
        if not user:
            raise ValueError("用户不存在")
        if not user.verify_password(old_password):
            raise ValueError("旧密码错误")
        if new_password != confirm_password:
            raise ValueError("新密码和确认密码不一致")
        user.password_hash = get_password_hash(new_password)
        await user.save()
        return None
