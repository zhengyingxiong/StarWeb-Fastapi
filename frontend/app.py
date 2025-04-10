# app.py
import streamlit as st
from pages.streamlit_app import AuthManager, check_login_status
from utils.session import initialize_session_state

# st.set_page_config(
#     page_title="用户管理应用",
#     page_icon="🔑",
#     layout="wide",
#     initial_sidebar_state="expanded",
# )

initialize_session_state()

# --- 创建 AuthManager 实例 ---
auth_manager = AuthManager()

# --- 定义页面 ---
home_page = st.Page(auth_manager.home_page, title="首页", icon="🏠")
auth_page = st.Page(auth_manager.auth_page, title="认证", icon="🔐")
logout_page = st.Page(auth_manager.logout_page, title="登出", icon="🚪")
profile_page = st.Page(auth_manager.profile_page, title="个人资料", icon="👤")
change_password_page = st.Page(auth_manager.change_password_page, title="修改密码", icon="🔑")
admin_panel_page = st.Page(auth_manager.admin_panel_page, title="管理员面板", icon="📊")



nav_menu = {
    "功能": [
        home_page
    ],
    "个人中心": [
        profile_page,
        change_password_page
    ],
    "账户管理": [
        logout_page
    ],
}

if st.session_state.get('is_admin', False):
    nav_menu["管理员"] = [
        admin_panel_page
    ]

if check_login_status():
    navigation = st.navigation(nav_menu, position="sidebar")
else:
    auth_navigation = st.navigation([auth_page], position="sidebar")