import streamlit as st
import requests
import json

BASE_API_URL = "http://localhost:8000/api"  # 假设 FastAPI 应用运行在本地 8005 端口

# Streamlit 应用页面配置
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
            return {"status_code": 400, "detail": "Invalid method"}
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response is not None:
            try:
                error_detail = e.response.json()
                return {"status_code": e.response.status_code, "detail": error_detail.get("detail", "未知错误")}
            except json.JSONDecodeError:
                return {"status_code": e.response.status_code, "detail": f"服务器错误: {e.response.text}"}
        else:
            return {"status_code": 500, "detail": f"请求失败: {e}"}
    except requests.exceptions.RequestException as e:
        return {"status_code": 500, "detail": f"请求失败: {e}"}

def refresh_access_token():
    refresh_token = st.session_state.refresh_token
    if not refresh_token:
        return False, "没有刷新令牌"
    data = {"refresh_token": refresh_token}
    response = api_request('POST', '/auth/refresh', data=data)
    if response and response.get("status_code") == 200:
        st.session_state.access_token = response['access_token']
        return True, "令牌已刷新"
    else:
        st.session_state.access_token = None
        st.session_state.refresh_token = None
        st.session_state.user_info = None
        return False, response.get("detail", "刷新令牌失败")

def check_login_status():
    if not st.session_state.access_token:
        return False
    return True

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
        if not username or not email or not password:
            st.error("请填写完整注册信息")
            return
        register_data = {"username": username, "email": email, "password": password}
        response = api_request('POST', '/auth/register', data=register_data)
        if response and response.get("status_code") == 201:
            st.success("注册成功！")
            st.session_state.access_token = response['access_token']
            st.session_state.refresh_token = response['refresh_token']
            st.session_state.user_info = api_request('POST', '/auth/me', data={"token": st.session_state.access_token})
            st.rerun()
        else:
            st.error(f"注册失败: {response.get('detail', '未知错误')}")



# def login_page():
#     st.header("用户登录")
#     username = st.text_input("用户名")
#     password = st.text_input("密码", type="password")
#     if st.button("登录"):
#         if not username or not password:
#             st.error("请输入用户名和密码")
#             return
#         login_data = {"username": username, "password": password}
#         response = api_request('POST', '/auth/login', data=login_data)
#         if response and response.get("status_code") == 200:
#             st.success("登录成功！")
#             st.session_state.access_token = response['access_token']
#             st.session_state.refresh_token = response['refresh_token']
#             st.session_state.user_info = api_request('POST', '/auth/me', data={"token": st.session_state.access_token})
#             st.rerun()
#         else:
#             st.error(f"登录失败: {response.get('detail', '未知错误')}")

def login_page():
    st.header("用户登录")
    username = st.text_input("用户名")
    password = st.text_input("密码", type="password")

    if st.button("登录"):
        if not username or not password:
            st.error("请输入用户名和密码")
            return

        login_data = {"username": username, "password": password}
        response = api_request('POST', '/auth/login', data=login_data)
        
        # 调试输出，查看实际返回内容
        st.write("后端返回的响应:", response)

        # 检查响应是否为字典且包含 access_token
        if isinstance(response, dict) and "access_token" in response:
            st.success("登录成功！")
            st.session_state.access_token = response['access_token']
            st.session_state.refresh_token = response.get('refresh_token')  # refresh_token 可能可选
            st.session_state.user_info = api_request('POST', '/auth/me', data={"token": st.session_state.access_token})
            st.rerun()
        else:
            st.error(f"登录失败: {response.get('detail', '未知错误') if isinstance(response, dict) else '响应格式错误'}")


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
    user_info = st.session_state.user_info
    if user_info and user_info.get("status_code") == 200:
        user_data = user_info["user"]
        st.write(f"用户名: {user_data['username']}")
        st.write(f"邮箱: {user_data['email']}")
        st.write(f"是否激活: {'是' if user_data['is_active'] else '否'}")
        st.write(f"是否管理员: {'是' if user_data['is_superadmin'] else '否'}")
        st.write(f"上次登录时间: {user_data.get('last_login', 'N/A')}")
    else:
        st.error(f"无法获取用户信息: {user_info.get('detail', '未知错误')}")
        return
    st.subheader("修改密码")
    old_password = st.text_input("旧密码", type="password")
    new_password = st.text_input("新密码", type="password")
    confirm_password = st.text_input("确认新密码", type="password")
    if st.button("修改密码"):
        if new_password != confirm_password:
            st.error("两次输入的新密码不一致")
            return
        if not old_password or not new_password:
            st.error("请填写完整密码信息")
            return
        change_password_data = {"old_password": old_password, "new_password": new_password}
        response = api_request('PUT', '/users/me/password', data=change_password_data, token=st.session_state.access_token)
        if response and response.get("status_code") == 200:
            st.success("密码修改成功！")
        else:
            st.error(f"密码修改失败: {response.get('detail', '未知错误')}")

def admin_login_page():
    st.header("管理员登录")
    username = st.text_input("管理员用户名")
    password = st.text_input("管理员密码", type="password")
    if st.button("管理员登录"):
        if not username or not password:
            st.error("请输入管理员用户名和密码")
            return
        login_data = {"username": username, "password": password}
        response = api_request('POST', '/auth/login', data=login_data)
        if response and response.get("status_code") == 200:
            user_info_response = api_request('POST', '/auth/me', data={"token": response['access_token']})
            if user_info_response and user_info_response.get("status_code") == 200 and user_info_response["user"]["is_superadmin"]:
                st.success("管理员登录成功！")
                st.session_state.access_token = response['access_token']
                st.session_state.refresh_token = response['refresh_token']
                st.session_state.user_info = user_info_response
                st.session_state.is_admin = True
                st.rerun()
            else:
                st.error("非管理员用户，无法登录管理员后台")
        else:
            st.error(f"管理员登录失败: {response.get('detail', '未知错误')}")

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
    if not users_response or users_response.get("status_code") != 200:
        st.error(f"无法获取用户列表: {users_response.get('detail', '未知错误')}")
        return
    users = users_response.get("items", [])
    if not users:
        st.info("当前没有用户数据")
        return
    st.write(f"共 {users_response.get('total', 0)} 位用户")

    # 使用列布局展示用户列表
    for user in users:
        col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 1, 1])
        col1.write(user["id"])
        col2.write(user["username"])
        col3.write(user["email"])
        col4.write("是" if user["is_active"] else "否")
        if col5.button("删除", key=f"delete_user_{user['id']}"):
            admin_delete_user(user["id"])

    # 添加用户功能
    with st.expander("添加用户"):
        admin_add_user_form()

def admin_add_user_form():
    st.subheader("添加用户")
    username = st.text_input("用户名", key="add_user_username")
    email = st.text_input("邮箱", key="add_user_email")
    password = st.text_input("密码", type="password", key="add_user_password")
    is_active = st.checkbox("激活用户", value=True, key="add_user_is_active")
    if st.button("添加用户", key="add_user_button"):
        if not username or not email or not password:
            st.error("请填写完整用户信息")
            return
        add_user_data = {"username": username, "email": email, "password": password, "is_active": is_active}
        response = api_request('POST', '/users', data=add_user_data, token=st.session_state.access_token)
        if response and response.get("status_code") == 201:
            st.success("用户添加成功！")
            st.rerun()
        else:
            st.error(f"添加用户失败: {response.get('detail', '未知错误')}")

def admin_delete_user(user_id_to_delete):
    response = api_request('DELETE', f'/users/{user_id_to_delete}', token=st.session_state.access_token)
    if response and response.get("status_code") == 204:
        st.success(f"用户 ID: {user_id_to_delete} 删除成功！")
        st.rerun()
    else:
        st.error(f"删除用户 ID: {user_id_to_delete} 失败: {response.get('detail', '未知错误')}")

# --- 管理员面板 - 角色管理 ---
def admin_manage_roles():
    st.subheader("角色管理")
    access_token = st.session_state.access_token
    roles_response = api_request('GET', '/roles?page_size=100', token=access_token)
    if not roles_response or roles_response.get("status_code") != 200:
        st.error(f"无法获取角色列表: {roles_response.get('detail', '未知错误')}")
        return
    roles = roles_response.get("items", [])
    if not roles:
        st.info("当前没有角色数据")
        return
    st.write(f"共 {roles_response.get('total', 0)} 个角色")

    # 使用列布局展示角色列表
    for role in roles:
        col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 2, 1])
        col1.write(role["id"])
        col2.write(role["name"])
        col3.write(role["code"])
        col4.write(role["description"] or "-")
        if col5.button("删除", key=f"delete_role_{role['id']}"):
            admin_delete_role(role["id"])

    # 添加角色功能
    with st.expander("添加角色"):
        admin_add_role_form()

def admin_add_role_form():
    st.subheader("添加角色")
    name = st.text_input("角色名称", key="add_role_name")
    code = st.text_input("角色代码", key="add_role_code")
    description = st.text_area("角色描述", key="add_role_description")
    if st.button("添加角色", key="add_role_button"):
        if not name or not code:
            st.error("请填写角色名称和代码")
            return
        add_role_data = {"name": name, "code": code, "description": description}
        response = api_request('POST', '/roles', data=add_role_data, token=st.session_state.access_token)
        if response and response.get("status_code") == 201:
            st.success("角色添加成功！")
            st.rerun()
        else:
            st.error(f"添加角色失败: {response.get('detail', '未知错误')}")

def admin_delete_role(role_id_to_delete):
    response = api_request('DELETE', f'/roles/{role_id_to_delete}', token=st.session_state.access_token)
    if response and response.get("status_code") == 204:
        st.success(f"角色 ID: {role_id_to_delete} 删除成功！")
        st.rerun()
    else:
        st.error(f"删除角色 ID: {role_id_to_delete} 失败: {response.get('detail', '未知错误')}")

# --- 管理员面板 - 权限管理 ---
def admin_manage_permissions():
    st.subheader("权限管理")
    access_token = st.session_state.access_token
    permissions_response = api_request('GET', '/permissions?page_size=100', token=access_token)
    if not permissions_response or permissions_response.get("status_code") != 200:
        st.error(f"无法获取权限列表: {permissions_response.get('detail', '未知错误')}")
        return
    permissions = permissions_response.get("items", [])
    if not permissions:
        st.info("当前没有权限数据")
        return
    st.write(f"共 {permissions_response.get('total', 0)} 个权限")

    # 使用列布局展示权限列表
    for perm in permissions:
        col1, col2, col3, col4, col5, col6 = st.columns([1, 2, 2, 1, 2, 1])
        col1.write(perm["id"])
        col2.write(perm["name"])
        col3.write(perm["code"])
        col4.write(perm["type"])
        col5.write(perm["description"] or "-")
        if col6.button("删除", key=f"delete_perm_{perm['id']}"):
            admin_delete_permission(perm["id"])

    # 添加权限功能
    with st.expander("添加权限"):
        admin_add_permission_form()

def admin_add_permission_form():
    st.subheader("添加权限")
    name = st.text_input("权限名称", key="add_perm_name")
    code = st.text_input("权限代码", key="add_perm_code")
    description = st.text_area("权限描述", key="add_perm_description")
    type_options = ["menu", "button", "api"]
    type_select = st.selectbox("权限类型", type_options, key="add_perm_type")
    path = st.text_input("路由路径 (菜单/接口类型)", key="add_perm_path", placeholder="仅菜单或接口类型填写")
    sort_order = st.number_input("排序序号", value=0, step=1, key="add_perm_sort_order")
    if st.button("添加权限", key="add_perm_button"):
        if not name or not code or not type_select:
            st.error("请填写权限名称、代码和类型")
            return
        add_perm_data = {
            "name": name,
            "code": code,
            "description": description,
            "type": type_select,
            "path": path if type_select in ["menu", "api"] else None,
            "sort_order": int(sort_order)
        }
        response = api_request('POST', '/permissions', data=add_perm_data, token=st.session_state.access_token)
        if response and response.get("status_code") == 201:
            st.success("权限添加成功！")
            st.rerun()
        else:
            st.error(f"添加权限失败: {response.get('detail', '未知错误')}")

def admin_delete_permission(permission_id_to_delete):
    response = api_request('DELETE', f'/permissions/{permission_id_to_delete}', token=st.session_state.access_token)
    if response and response.get("status_code") == 204:
        st.success(f"权限 ID: {permission_id_to_delete} 删除成功！")
        st.rerun()
    else:
        st.error(f"删除权限 ID: {permission_id_to_delete} 失败: {response.get('detail', '未知错误')}")

# --- 主 Streamlit 应用 ---
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