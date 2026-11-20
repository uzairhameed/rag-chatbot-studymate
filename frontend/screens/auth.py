"""Login and registration screens."""

import streamlit as st

from frontend.api_client import get_current_user, login_user, register_user


def show_login_page() -> None:
    """Render login and registration forms."""
    st.title("StudyMate")
    st.write("Sign in or create an account to continue.")

    login_tab, register_tab = st.tabs(["Login", "Register"])

    with login_tab:
        with st.form("login_form"):
            login_email = st.text_input("Email", key="login_email")
            login_password = st.text_input(
                "Password",
                type="password",
                key="login_password",
            )
            login_submitted = st.form_submit_button("Log in")

        if login_submitted:
            email = login_email.strip().lower()
            password = login_password

            if not email or not password:
                st.error("Enter email and password.")
            elif (
                "@" not in email
                or "." not in email.rsplit("@", 1)[-1]
                or " " in email
            ):
                st.error("Enter a valid email address.")
            elif len(password) < 8:
                st.error("Password must be at least 8 characters.")
            else:
                try:
                    token_data = login_user(email, password)
                    st.session_state.token = token_data["access_token"]
                    st.session_state.user_id = get_current_user(
                        st.session_state.token
                    )["id"]
                    st.session_state.email = email
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

    with register_tab:
        with st.form("register_form"):
            username = st.text_input("Username", key="register_username")
            register_email = st.text_input("Email", key="register_email")
            register_password = st.text_input(
                "Password",
                type="password",
                key="register_password",
            )
            register_submitted = st.form_submit_button("Create account")

        if register_submitted:
            username_value = username.strip()
            email = register_email.strip().lower()
            password = register_password

            if not username_value or not email or not password:
                st.error("Enter username, email, and password.")
            elif len(username_value) < 3:
                st.error("Username must be at least 3 characters.")
            elif (
                "@" not in email
                or "." not in email.rsplit("@", 1)[-1]
                or " " in email
            ):
                st.error("Enter a valid email address.")
            elif len(password) < 8:
                st.error("Password must be at least 8 characters.")
            else:
                try:
                    register_user(username_value, email, password)

                    token_data = login_user(email, password)
                    st.session_state.token = token_data["access_token"]
                    st.session_state.user_id = get_current_user(
                        st.session_state.token
                    )["id"]
                    st.session_state.email = email
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))