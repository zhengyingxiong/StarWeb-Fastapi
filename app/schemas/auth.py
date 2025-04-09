from pydantic import BaseModel, Field

class TokenResponse(BaseModel):
    """令牌响应模型"""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    refresh_expires_in: int

class RefreshTokenResponse(BaseModel):
    """刷新令牌的响应模型"""
    access_token: str
    expires_in: int

class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str
    password: str

class RefreshTokenRequest(BaseModel):
    """刷新令牌请求模型"""
    refresh_token: str

class TokenRequest(BaseModel):
    """令牌请求模型"""
    token: str




class UserRegisterRequest(BaseModel):
    """用户注册请求模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: str = Field(..., description="邮箱地址") # 可以添加邮箱格式验证
    password: str = Field(..., min_length=6, description="密码") # 可以添加密码复杂度验证
