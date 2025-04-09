import streamlit as st
import requests
import json
import time
import random

BASE_API_URL = "http://localhost:8000/api"  # 请确认后端实际端口

st.set_page_config(
    page_title="用户管理应用",
    page_icon="🔑",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Session State 初始化 ---
if 'access_token' not in st.session_state:
    st.session_state.access_token = None
if 'refresh_token' not in st.session_state:
    st.session_state.refresh_token = None
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False

# --- 辅助函数 ---
def api_request(method, endpoint, data=None, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    url = f"{BASE_API_URL}{endpoint}"
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, data=json.dumps(data))
        elif method == 'PUT':
            response = requests.put(url, headers=headers, data=json.dumps(data))
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)
        else:
            return {"success": False, "status_code": 400, "detail": "无效的请求方法"}

        response.raise_for_status()

        if response.status_code == 204:
            return {"success": True, "status_code": 204, "data": None}
        else:
            try:
                data = response.json()
                return {"success": True, "status_code": response.status_code, "data": data}
            except json.JSONDecodeError:
                return {"success": False, "status_code": response.status_code, "detail": "无法解析响应体"}
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response else 500
        error_detail = e.response.json().get("detail", f"HTTP 错误 {status_code}") if e.response and e.response.content else f"HTTP 错误 {status_code}"
        return {"success": False, "status_code": status_code, "detail": error_detail}
    except requests.exceptions.RequestException as e:
        return {"success": False, "status_code": 500, "detail": f"网络请求失败: {str(e)}"}

def refresh_access_token():
    refresh_token = st.session_state.refresh_token
    if not refresh_token:
        return False, "没有刷新令牌"
    data = {"refresh_token": refresh_token}
    response = api_request('POST', '/auth/refresh', data=data)
    if response["success"]:
        st.session_state.access_token = response["data"]["access_token"]
        st.session_state.refresh_token = response["data"].get("refresh_token")
        return True, "令牌已刷新"
    else:
        st.session_state.access_token = None
        st.session_state.refresh_token = None
        st.session_state.user_info = None
        st.session_state.is_admin = False
        return False, response["detail"]

def check_login_status():
    return bool(st.session_state.access_token)

# --- 页面类 ---
class AuthManager:
    def home_page(self):
        st.title("欢迎来到用户管理应用")
        st.write("这是一个基于 FastAPI 后端的 Streamlit 用户管理前端应用。")

    def login_page(self):
        st.header("登录")
        username = st.text_input("用户名", key="login_username")
        password = st.text_input("密码", type="password", key="login_password")
        if st.button("登录", use_container_width=True):
            if not all([username, password]):
                st.error("请输入用户名和密码")
                return
            login_data = {"username": username, "password": password}
            response = api_request('POST', '/auth/login', data=login_data)
            if response["success"]:
                st.session_state.access_token = response["data"]["access_token"]
                st.session_state.refresh_token = response["data"].get("refresh_token")
                user_info_response = api_request('POST', '/auth/me', data={"token": st.session_state.access_token})
                if user_info_response["success"]:
                    st.session_state.user_info = user_info_response["data"]
                    st.session_state.is_admin = user_info_response["data"]["user"].get("is_superadmin", False)
                    st.success("✅ 登录成功！正在重定向...")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error(f"❌ 获取用户信息失败: {user_info_response['detail']}")
            else:
                st.error(f"❌ 登录失败: {response['detail']}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("注册账户"):
                st.query_params["auth_page"] = "signup"
                st.rerun()
        with col2:
            if st.button("忘记密码？"):
                st.query_params["auth_page"] = "reset"
                st.rerun()

    def signup_page(self):
        st.header("注册")
        username = st.text_input("用户名", key="signup_username")
        email = st.text_input("邮箱", key="signup_email")
        password = st.text_input("密码", type="password", key="signup_password")
        confirm_password = st.text_input("确认密码", type="password", key="signup_confirm")
        if st.button("注册", use_container_width=True):
            if password != confirm_password:
                st.error("❌ 两次输入的密码不一致")
                return
            if not all([username, email, password]):
                st.error("❌ 请填写完整注册信息")
                return
            register_data = {"username": username, "email": email, "password": password}
            response = api_request('POST', '/auth/register', data=register_data)
            if response["success"]:
                st.success("✅ 注册成功！正在重定向到登录页面...")
                time.sleep(0.5)
                st.query_params["auth_page"] = "login"
                st.rerun()
            else:
                st.error(f"❌ 注册失败: {response['detail']}")

        if st.button("返回登录"):
            st.query_params["auth_page"] = "login"
            st.rerun()

    # def reset_password_page(self):
    #     st.header("重置密码")
    #     email = st.text_input("邮箱", key="reset_email")
    #     if st.button("发送重置码", use_container_width=True):
    #         # 这里假设后端支持发送重置码，实际需调整
    #         st.success("✅ 重置码已发送至您的邮箱！（示例功能）")
        
    #     reset_code = st.text_input("输入重置码", key="reset_code")
    #     new_password = st.text_input("新密码", type="password", key="reset_new_password")
    #     confirm_password = st.text_input("确认新密码", type="password", key="reset_confirm_password")
    #     if st.button("重置密码", use_container_width=True):
    #         if new_password != confirm_password:
    #             st.error("❌ 两次输入的密码不匹配")
    #             return
    #         # 这里假设后端支持重置密码，实际需实现
    #         st.success("✅ 密码重置成功！正在重定向到登录页面...")
    #         time.sleep(1)
    #         st.query_params["auth_page"] = "login"
    #         st.rerun()

    #     if st.button("返回登录"):
    #         st.query_params["auth_page"] = "login"
    #         st.rerun()



    def reset_password_page(self):
        st.header("重置密码")
        email = st.text_input("邮箱", key="reset_email")
        
        if st.button("发送重置码", use_container_width=True):
            # 生成随机的6位数字重置码
            reset_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            # 这里假设后端支持发送重置码，实际需调整
            # 模拟将重置码与邮箱关联（实际需存储到后端数据库）
            st.session_state.temp_reset_code = reset_code  # 临时存储重置码供验证
            st.success(f"✅ 重置码已发送至您的邮箱！示例重置码: {reset_code}")

        reset_code_input = st.text_input("输入重置码", key="reset_code")
        new_password = st.text_input("新密码", type="password", key="reset_new_password")
        confirm_password = st.text_input("确认新密码", type="password", key="reset_confirm_password")
        
        if st.button("重置密码", use_container_width=True):
            if new_password != confirm_password:
                st.error("❌ 两次输入的密码不匹配")
                return
            # 验证重置码（这里是模拟，实际应通过后端验证）
            if 'temp_reset_code' in st.session_state and reset_code_input == st.session_state.temp_reset_code:
                # 这里假设后端支持重置密码，实际需实现
                # 模拟成功重置密码
                del st.session_state.temp_reset_code  # 重置后删除临时重置码
                st.success("✅ 密码重置成功！正在重定向到登录页面...")
                time.sleep(1)
                st.query_params["auth_page"] = "login"
                st.rerun()
            else:
                st.error("❌ 重置码不正确或已过期")

        if st.button("返回登录"):
            st.query_params["auth_page"] = "login"
            st.rerun()





    def auth_page(self):
        auth_page = st.query_params.get("auth_page", "login")
        if auth_page == "login":
            self.login_page()
        elif auth_page == "signup":
            self.signup_page()
        elif auth_page == "reset":
            self.reset_password_page()

    def logout_page(self):
        st.header("登出")
        if st.button("确认登出", use_container_width=True):
            st.session_state.access_token = None
            st.session_state.refresh_token = None
            st.session_state.user_info = None
            st.session_state.is_admin = False
            st.success("✅ 您已成功登出！正在重定向...")
            time.sleep(0.5)
            st.rerun()

    def profile_page(self):
        st.header("个人资料")
        if not check_login_status():
            st.error("❌ 请先登录")
            return
        user_info = st.session_state.user_info["user"]
        st.write(f"用户名: {user_info.get('username', '未知')}")
        st.write(f"邮箱: {user_info.get('email', '未知')}")
        st.write(f"是否激活: {'是' if user_info.get('is_active', False) else '否'}")
        st.write(f"是否管理员: {'是' if user_info.get('is_superadmin', False) else '否'}")
        st.write(f"上次登录: {user_info.get('last_login', 'N/A')}")

    def change_password_page(self):
        st.header("修改密码")
        if not check_login_status():
            st.error("❌ 请先登录")
            return
        old_password = st.text_input("旧密码", type="password", key="change_old_pw")
        new_password = st.text_input("新密码", type="password", key="change_new_pw")
        confirm_password = st.text_input("确认新密码", type="password", key="change_confirm_pw")
        if st.button("修改密码", use_container_width=True):
            if new_password != confirm_password:
                st.error("❌ 两次输入的新密码不一致")
                return
            if not all([old_password, new_password]):
                st.error("❌ 请填写完整密码信息")
                return
            change_password_data = {"old_password": old_password, "new_password": new_password}
            response = api_request('PUT', '/users/me/password', data=change_password_data, token=st.session_state.access_token)
            if response["success"]:
                st.success("✅ 密码修改成功！")
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"❌ 密码修改失败: {response['detail']}")

    def admin_panel_page(self):
        st.header("管理员面板")
        if not st.session_state.is_admin:
            st.error("❌ 您不是管理员，无权访问此页面")
            return
        tab = st.sidebar.radio("管理选项", ["用户管理", "角色管理", "权限管理"])
        if tab == "用户管理":
            self.admin_manage_users()
        elif tab == "角色管理":
            st.info("角色管理功能尚未实现")
        elif tab == "权限管理":
            st.info("权限管理功能尚未实现")

    def admin_manage_users(self):
        st.subheader("用户管理")
        response = api_request('GET', '/users?page_size=100', token=st.session_state.access_token)
        if not response["success"]:
            st.error(f"❌ 无法获取用户列表: {response['detail']}")
            return
        users = response["data"]["items"]
        if not users:
            st.info("当前没有用户数据")
            return
        st.write(f"共 {response['data']['total']} 位用户")
        for user in users:
            col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 1, 1])
            col1.write(user["id"])
            col2.write(user["username"])
            col3.write(user["email"])
            col4.write("是" if user["is_active"] else "否")
            if col5.button("删除", key=f"delete_user_{user['id']}"):
                response = api_request('DELETE', f'/users/{user["id"]}', token=st.session_state.access_token)
                if response["success"]:
                    st.success(f"✅ 用户 ID: {user['id']} 删除成功！")
                    st.rerun()
                else:
                    st.error(f"❌ 删除用户失败: {response['detail']}")
        with st.expander("添加用户"):
            self.admin_add_user_form()

    def admin_add_user_form(self):
        st.subheader("添加用户")
        username = st.text_input("用户名", key="add_user_username")
        email = st.text_input("邮箱", key="add_user_email")
        password = st.text_input("密码", type="password", key="add_user_password")
        is_active = st.checkbox("激活用户", value=True, key="add_user_is_active")
        if st.button("添加用户", use_container_width=True):
            if not all([username, email, password]):
                st.error("❌ 请填写完整用户信息")
                return
            add_user_data = {"username": username, "email": email, "password": password, "is_active": is_active}
            response = api_request('POST', '/users', data=add_user_data, token=st.session_state.access_token)
            if response["success"]:
                st.success("✅ 用户添加成功！")
                st.rerun()
            else:
                st.error(f"❌ 添加用户失败: {response['detail']}")

# --- 主逻辑 ---
auth_manager = AuthManager()



home_page = st.Page(auth_manager.home_page, title="首页", icon="🏠")
auth_page = st.Page(auth_manager.auth_page, title="认证", icon="🔐")
logout_page = st.Page(auth_manager.logout_page, title="登出", icon="🚪")
profile_page = st.Page(auth_manager.profile_page, title="个人资料", icon="👤")
change_password_page = st.Page(auth_manager.change_password_page, title="修改密码", icon="🔑")
admin_panel_page = st.Page(auth_manager.admin_panel_page, title="管理员面板", icon="📊")


def get_nav_menu():
    base_menu = {
        "功能": [home_page],
        "个人中心": [profile_page, change_password_page],
        "账户管理": [logout_page],
    }
    if st.session_state.is_admin:
        base_menu["管理员"] = [admin_panel_page]
    return base_menu

if check_login_status():
    nav_menu = get_nav_menu()
    nav = st.navigation(nav_menu, position="sidebar")
    nav.run()
else:
    pg = st.navigation([auth_page])
    pg.run()