import streamlit as st
import requests
import json

BASE_API_URL = "http://localhost:8000/api"  # 请确认后端实际端口（8000 或 8005）

st.set_page_config(
    page_title="用户管理应用",
    page_icon="🔑",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Session State 管理 ---
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

        # 检查 HTTP 错误状态码 (4xx, 5xx)
        response.raise_for_status()

        # --- 修改开始 ---
        # 检查是否是 204 No Content 状态码
        if response.status_code == 204:
            # 对于 204，操作成功，但没有 JSON 数据返回
            return {"success": True, "status_code": response.status_code, "data": None}
        else:
            # 对于其他成功的状态码 (如 200 OK, 201 Created)，尝试解析 JSON
            try:
                data = response.json()
                return {"success": True, "status_code": response.status_code, "data": data}
            except json.JSONDecodeError:
                # 如果服务器返回成功状态码但响应体不是有效JSON（理论上不应发生，但做个健壮性处理）
                return {"success": False, "status_code": response.status_code, "detail": "服务器成功响应但无法解析响应体"}
        # --- 修改结束 ---

    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response else 500
        try:
            # 尝试从错误响应中解析 JSON 细节
            error_detail = e.response.json().get("detail", f"HTTP 错误 {status_code}") if e.response and e.response.content else f"HTTP 错误 {status_code}"
        except json.JSONDecodeError:
            # 如果错误响应也不是 JSON，则显示原始文本
            error_detail = f"服务器响应解析失败 (状态码: {status_code}): {e.response.text if e.response else '无响应体'}"
        return {"success": False, "status_code": status_code, "detail": error_detail}
    except requests.exceptions.RequestException as e:
        # 网络层面的错误
        return {"success": False, "status_code": 500, "detail": f"网络请求失败: {str(e)}"}

# ... (其余函数 home_page, register_page, login_page 等保持不变) ...



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
        return False, response["detail"]

def check_login_status():
    return bool(st.session_state.access_token)

# --- 页面函数 ---
def home_page():
    st.title("欢迎来到用户管理应用")
    st.write("这是一个基于 FastAPI 后端的 Streamlit 用户管理前端应用。")


def register_page():
    st.header("用户注册")
    username = st.text_input("用户名")
    email = st.text_input("邮箱")
    password = st.text_input("密码", type="password")
    password_confirm = st.text_input("确认密码", type="password")
    if st.button("注册"):
        if password != password_confirm:
            st.error("两次输入的密码不一致")
            return
        if not all([username, email, password]):
            st.error("请填写完整注册信息")
            return
        register_data = {"username": username, "email": email, "password": password}
        response = api_request('POST', '/auth/register', data=register_data)
        if response["success"]:
            st.success("注册成功！")
            st.session_state.access_token = response["data"]["access_token"]
            st.session_state.refresh_token = response["data"].get("refresh_token")
            # 注册后直接登录，获取用户信息
            user_info_response = api_request('POST', '/auth/me', data={"token": st.session_state.access_token})
            if user_info_response["success"]:
                st.session_state.user_info = user_info_response["data"]
                st.session_state.is_admin = user_info_response["data"].get("is_superadmin", False)
                st.rerun()  # 重新运行应用，更新 UI
            else:
                st.error(f"注册成功，但获取用户信息失败：{user_info_response['detail']}") #注册成功后获取用户信息失败，提示用户
        else:
            st.error(f"注册失败: {response['detail']}")


def login_page():
    st.header("用户登录")
    username = st.text_input("用户名")
    password = st.text_input("密码", type="password")
    if st.button("登录"):
        if not all([username, password]):
            st.error("请输入用户名和密码")
            return
        login_data = {"username": username, "password": password}
        response = api_request('POST', '/auth/login', data=login_data)
        # st.write("调试: 登录响应:", response) # 可以取消注释查看登录响应
        if response["success"]:
            st.success("登录成功！")
            st.session_state.access_token = response["data"]["access_token"]
            st.session_state.refresh_token = response["data"].get("refresh_token")

# --- 获取用户信息 ---
            user_info_response = api_request('POST', '/auth/me', data={"token": st.session_state.access_token})
            # st.write("调试: /auth/me 响应:", user_info_response) # <--- 调试信息


            if user_info_response["success"]:
                # 这里存储的是 /auth/me 响应的整个 data 部分，
                # 而不是嵌套的 user 对象
                # st.session_state.user_info = user_info_response["data"]["user"] # <--- 旧代码
                st.session_state.user_info = user_info_response["data"] # <--- 修正：存储整个响应数据

                # --- 从存储的整个响应数据中获取 user 对象和 is_superadmin ---
                user_object = user_info_response["data"].get("user", {})
                st.session_state.is_admin = user_object.get("is_superadmin", False)
                # --- 修正结束 ---

                # st.write(f"调试: 检测到的 is_admin: {st.session_state.is_admin}") # <--- 调试信息
                # st.write(f"调试: 存储的 user_info: {st.session_state.user_info}") # <--- 新增调试信息
                st.rerun()








def logout_page():
    st.header("用户登出")
    if st.button("确认登出"):
        st.session_state.access_token = None
        st.session_state.refresh_token = None
        st.session_state.user_info = None
        st.session_state.is_admin = False
        st.success("您已成功登出！")
        st.rerun()



def user_profile_page():
    st.header("用户个人资料")
    if not check_login_status():
        st.error("请先登录")
        return

    # --- 修正：从存储的完整响应数据中提取 user 对象 ---
    full_user_info_response = st.session_state.user_info # 这是 {"token_type": "...", "user": {...}}
    # st.write(f"调试: 读取的 user_info (完整响应): {full_user_info_response}") # <--- 新增调试信息

    user_info = None # 初始化
    if full_user_info_response and isinstance(full_user_info_response, dict):
        user_info = full_user_info_response.get("user") # 提取嵌套的 user 对象

    # st.write(f"调试: 提取的 user 对象: {user_info}") # <--- 新增调试信息

    # --- 使用提取出的 user_info 对象 ---
    if user_info and isinstance(user_info, dict):
        st.write(f"用户名: {user_info.get('username', '未知')}")
        st.write(f"邮箱: {user_info.get('email', '未知')}")
        st.write(f"是否激活: {'是' if user_info.get('is_active', False) else '否'}")
        st.write(f"是否管理员: {'是' if user_info.get('is_superadmin', False) else '否'}")
        last_login = user_info.get('last_login')
        st.write(f"上次登录时间: {last_login if last_login else 'N/A'}") # 处理 null 值
    else:
        st.error("用户信息未正确加载，请重新登录")
        # ... [清理 session state 的代码保持不变] ...
        st.session_state.access_token = None
        st.session_state.refresh_token = None
        st.session_state.user_info = None
        st.session_state.is_admin = False
        st.rerun()
        return

    # ... [修改密码部分保持不变] ...
    st.subheader("修改密码")
    old_password = st.text_input("旧密码", type="password", key="profile_old_pw") # 添加 key 避免冲突
    new_password = st.text_input("新密码", type="password", key="profile_new_pw")
    confirm_password = st.text_input("确认新密码", type="password", key="profile_confirm_pw")
    if st.button("修改密码"):
        if new_password != confirm_password:
            st.error("两次输入的新密码不一致")
            return
        if not all([old_password, new_password]):
            st.error("请填写完整密码信息")
            return
        # 确认 confirm_password 传递给后端
        change_password_data = {"old_password": old_password, "new_password": new_password, "confirm_password": confirm_password}
        response = api_request('PUT', '/users/me/password', data=change_password_data, token=st.session_state.access_token)
        if response["success"]:
            st.success("密码修改成功！")
        else:
            st.error(f"密码修改失败: {response['detail']}")



def admin_login_page():
    st.header("管理员登录")
    username = st.text_input("管理员用户名")
    password = st.text_input("管理员密码", type="password")
    if st.button("管理员登录"):
        if not all([username, password]):
            st.error("请输入管理员用户名和密码")
            return
        login_data = {"username": username, "password": password}
        response = api_request('POST', '/auth/login', data=login_data)
        # st.write("调试: 管理员登录响应:", response) # 可以取消注释查看登录响应
        if response["success"]:
            access_token = response["data"]["access_token"]
            # --- 获取用户信息 ---
            user_info_response = api_request('POST', '/auth/me', data={"token": access_token})
            # st.write("调试: 管理员 /auth/me 响应:", user_info_response) # <--- 添加调试信息

            # --- 修正：从嵌套的 user 对象中获取 is_superadmin ---
            is_superadmin = user_info_response.get("data", {}).get("user", {}).get("is_superadmin", False)
            # --- 修正结束 ---
            # st.write(f"调试: 检测到的 is_superadmin: {is_superadmin}") # <--- 添加调试信息

            if user_info_response["success"] and is_superadmin: # 使用修正后的 is_superadmin 变量
                st.success("管理员登录成功！")
                st.session_state.access_token = access_token
                st.session_state.refresh_token = response["data"].get("refresh_token")
                st.session_state.user_info = user_info_response["data"]["user"] # <--- 存储 user 对象
                st.session_state.is_admin = True
                st.rerun()
            elif user_info_response["success"] and not is_superadmin:
                 st.error("该用户不是管理员，无法登录管理员后台")
            else:
                 st.error(f"获取用户信息失败: {user_info_response.get('detail', '未知错误')}")
        else:
            st.error(f"管理员登录失败: {response['detail']}")





def admin_panel_page():
    st.header("管理员面板")
    if not st.session_state.is_admin:
        st.error("您不是管理员，无权访问此页面")
        return
    tab = st.sidebar.radio("管理选项", ["用户管理", "角色管理", "权限管理"])
    if tab == "用户管理":
        admin_manage_users()
    elif tab == "角色管理":
        admin_manage_roles()
    elif tab == "权限管理":
        admin_manage_permissions()

# --- 管理员面板 - 用户管理 ---
def admin_manage_users():
    st.subheader("用户管理")
    access_token = st.session_state.access_token
    users_response = api_request('GET', '/users?page_size=100', token=access_token)
    if not users_response["success"]:
        st.error(f"无法获取用户列表: {users_response['detail']}")
        return
    users = users_response["data"]["items"]
    if not users:
        st.info("当前没有用户数据")
        return
    st.write(f"共 {users_response['data']['total']} 位用户")
    for user in users:
        col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 1, 1])
        col1.write(user["id"])
        col2.write(user["username"])
        col3.write(user["email"])
        col4.write("是" if user["is_active"] else "否")
        if col5.button("删除", key=f"delete_user_{user['id']}"):
            admin_delete_user(user["id"])
    with st.expander("添加用户"):
        admin_add_user_form()


def admin_add_user_form():
    st.subheader("添加用户")
    username = st.text_input("用户名", key="add_user_username")
    email = st.text_input("邮箱", key="add_user_email")
    password = st.text_input("密码", type="password", key="add_user_password")
    is_active = st.checkbox("激活用户", value=True, key="add_user_is_active")

    if st.button("添加用户", key="add_user_button"):
        # --- 前端基础验证 ---
        error_messages = []
        if not username:
            error_messages.append("请输入用户名")
        if not email:
            error_messages.append("请输入邮箱")
        # 简单的前端邮箱格式检查 (可选，后端已有更严格的验证)
        import re
        if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
             error_messages.append("请输入有效的邮箱地址")
        if not password:
            error_messages.append("请输入密码")
        if len(password) < 6: # 假设密码最小长度为6
             error_messages.append("密码长度至少为6位")

        if error_messages:
            st.error("\n".join(error_messages)) # 显示所有前端错误
            return
        # --- 前端基础验证结束 ---


        add_user_data = {"username": username, "email": email, "password": password, "is_active": is_active}
        response = api_request('POST', '/users', data=add_user_data, token=st.session_state.access_token)

        if response["success"]:
            st.success("用户添加成功！")
            # 清空表单或rerun以刷新
            st.rerun()
        else:
            # --- 改进 422 错误处理 ---
            if response["status_code"] == 422:
                error_detail = response.get("detail")
                # FastAPI 的 422 detail 通常是列表
                if isinstance(error_detail, list) and error_detail:
                    messages = []
                    for err in error_detail:
                        field = " -> ".join(map(str, err.get('loc', ['未知字段']))) # 获取字段路径
                        msg = err.get('msg', '验证失败')
                        messages.append(f"字段 '{field}': {msg}")
                    st.error(f"添加用户失败 (验证错误):\n" + "\n".join(messages))
                else:
                    # 如果 detail 不是预期的列表格式，显示原始信息
                    st.error(f"添加用户失败 (验证错误): {error_detail}")
            else:
                # 其他类型的错误
                st.error(f"添加用户失败: {response['detail']}")
            # --- 改进结束 ---



def admin_delete_user(user_id_to_delete):
    response = api_request('DELETE', f'/users/{user_id_to_delete}', token=st.session_state.access_token)
    # 现在 response["success"] 会是 True
    if response["success"]:
        st.success(f"用户 ID: {user_id_to_delete} 删除成功！")
        st.rerun() # 重新运行以刷新列表
    else:
        # 如果仍然失败，会显示更具体的错误信息
        st.error(f"删除用户失败: {response['detail']}")


# --- 管理员面板 - 角色管理 ---
def admin_manage_roles():
    st.subheader("角色管理")
    st.info("角色管理功能尚未实现")  # 后端未提供角色管理接口，可根据需要扩展

def admin_manage_permissions():
    st.subheader("权限管理")
    st.info("权限管理功能尚未实现")  # 后端未提供权限管理接口，可根据需要扩展

# --- 主应用 ---
def main():
    st.sidebar.title("用户管理")
    menu = ["首页"]
    if check_login_status():
        menu.extend(["个人资料", "登出"])
        if st.session_state.is_admin:
            menu.append("管理员面板")
    else:
        menu.extend(["注册", "用户登录", "管理员登录"])
    choice = st.sidebar.selectbox("菜单", menu)
    if choice == "首页":
        home_page()
    elif choice == "注册":
        register_page()
    elif choice == "用户登录":
        login_page()
    elif choice == "管理员登录":
        admin_login_page()
    elif choice == "个人资料":
        user_profile_page()
    elif choice == "登出":
        logout_page()
    elif choice == "管理员面板":
        admin_panel_page()

if __name__ == "__main__":
    main()