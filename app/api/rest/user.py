# app/api/rest/user.py

from typing import Optional, List, Set
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.models.user import User # 导入 User 模型
from app.core.security.deps import (
    get_current_user, get_current_active_superuser,
    require_permissions, require_roles, require_active_user,
    require_superuser, require_all, require_any,
    get_current_user_roles,get_current_user_permissions
)
# 确保 UserCreate 被导入
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserList, PasswordChangeRequest
from app.services.user import UserService


router = APIRouter()
user_service = UserService() # 实例化


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_user) # 建议修改类型提示
    # 可以在这里添加权限检查，例如 Depends(require_permissions("user.create"))
):
    """
    创建新用户 (通常由管理员操作)
    :param user_data: 用户创建数据 (UserCreate)
    :param current_user: 当前登录用户（来自token验证）
    :return: 创建的用户信息
    """
    try:
        # 调用新的 admin_create_user 方法
        user = await user_service.admin_create_user(user_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user) # 建议修改类型提示
     # 可以在这里添加权限检查
):
    """
    更新用户信息
    :param user_id: 用户ID
    :param user_data: 更新的用户数据
    :param current_user: 当前登录用户（来自token验证）
    :return: 更新后的用户信息
    """
    try:
        user = await UserService.update_user(user_id, user_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete(
    "/{user_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_current_active_superuser)]  # 只有超级管理员可以删除用户
)
async def delete_user(
    user_id: int
):
    """
    删除用户 (需要超级管理员权限)
    :param user_id: 用户ID
    """
    try:
        await UserService.delete_user(user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user) # 建议修改类型提示
    # 可以在这里添加权限检查
):
    """
    获取用户详情
    :param user_id: 用户ID
    :param current_user: 当前登录用户（来自token验证）
    :return: 用户详细信息
    """
    try:
        user = await UserService.get_user(user_id)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.get("", response_model=UserList)
async def list_users(
    page: int = 1,
    page_size: int = 10,
    username: Optional[str] = None,
    email: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user) # 建议修改类型提示
    # 可以在这里添加权限检查
):
    """
    获取用户列表
    :param page: 页码，默认1
    :param page_size: 每页数量，默认10
    :param username: 用户名过滤（可选）
    :param email: 邮箱过滤（可选）
    :param is_active: 是否激活过滤（可选）
    :param current_user: 当前登录用户（来自token验证）
    :return: 用户列表和总数
    """
    print("current_user:", current_user)
    users, total = await UserService.list_users(
        page=page,
        page_size=page_size,
        username=username,
        email=email,
        is_active=is_active
    )
    return {
        "total": total,
        "items": users
    }

# 以下是各种鉴权方式的示例

@router.get(
    "/me/me", 
    response_model=UserResponse,
    dependencies=[Depends(require_active_user())]  # 确保用户处于活跃状态
)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前登录用户信息 (需要用户处于活跃状态)
    :param current_user: 当前登录用户
    :return: 用户详细信息
    """
    print("current_user:", current_user)
    return current_user






@router.put("/me/password", status_code=status.HTTP_200_OK, dependencies=[Depends(require_active_user())])
async def change_password(
    password_change_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user) # 获取当前登录用户
):
    """
    用户修改密码 (需要用户处于活跃状态)
    """
    try:
        await user_service.change_password(
            user_id=current_user.id, # 使用当前用户的 ID
            old_password=password_change_data.old_password,
            new_password=password_change_data.new_password,
            confirm_password=password_change_data.confirm_password
        )
        return {"message": "密码修改成功"} # 返回成功消息
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )



@router.post(
    "/{user_id}/activate",
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(require_any(
            lambda: require_roles("admin"),
            lambda: require_permissions(["user.manage","user.reset-password"])
        ))
    ]
)
async def activate_user(
    user_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    激活用户账号
    
    权限要求（满足以下任意一个条件）：
    - 拥有admin角色
    - 拥有user.manage和user.reset-password权限
    
    :param user_id: 用户ID
    :param current_user: 当前登录用户
    :return: 操作结果
    """
    print("user_id:", int)
    print("current_user:", current_user)
    return "访问成功"

@router.post(
    "/{user_id}/deactivate",
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(require_all(
            lambda: require_permissions("user.manage"),
            lambda: require_roles(["admin", "supervisor"], require_all=False)
        ))
    ]
)
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    禁用用户账号
    
    权限要求（必须同时满足以下所有条件）：
    - 拥有user.manage权限
    - 拥有admin或supervisor角色之一
    
    :param user_id: 用户ID
    :param current_user: 当前登录用户
    :return: 操作结果
    """
    print("user_id:", int)
    print("current_user:", current_user)
    return "访问成功"

@router.post(
    "/{user_id}/reset-password",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_superuser())]  # 只有超级管理员可以重置密码
)
async def reset_user_password(
    user_id: int
):
    """
    重置用户密码 (需要超级管理员权限)
    
    :param user_id: 用户ID
    :return: 操作结果
    """
    return "访问成功"

@router.get(
    "/admin/dashboard",
    dependencies=[Depends(require_roles("admin"))]  # 只有管理员可以访问仪表盘
)
async def admin_dashboard():
    """
    管理员仪表盘 (需要admin角色)
    
    :return: 仪表盘数据
    """
    return "访问成功"

@router.get(
    "/me/permissions", 
    response_model=List[str]
)
async def get_my_permissions(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户的权限列表
    
    :param current_user: 当前登录用户
    :return: 权限列表
    """
    permissions = await get_current_user_permissions(current_user)
    return permissions

@router.get(
    "/me/roles", 
    response_model=List[str]
)
async def get_my_roles(
    current_user: User = Depends(get_current_user)
):
    """
    获取当前用户的角色列表
    
    :param current_user: 当前登录用户
    :return: 角色列表
    """
    roles = await get_current_user_roles(current_user)
    return roles

