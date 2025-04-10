# utils/session.py
import streamlit as st

def initialize_session_state():
    """
    初始化 Streamlit 应用的会话状态变量。
    """
    if 'access_token' not in st.session_state:
        st.session_state.access_token = None
    if 'refresh_token' not in st.session_state:
        st.session_state.refresh_token = None
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    if 'is_admin' not in st.session_state:
        st.session_state.is_admin = False



    ## 初始化会话状态
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "user_email" not in st.session_state:
        st.session_state.user_email = ""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = {}
    if "selected_chat" not in st.session_state:
        st.session_state.selected_chat = None