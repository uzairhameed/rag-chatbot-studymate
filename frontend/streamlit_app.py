"""StudyMate Streamlit entry point."""

import streamlit as st

from frontend.screens.auth import show_login_page
from frontend.screens.rooms import show_room_list
from frontend.screens.room_detail import show_room


st.set_page_config(
    page_title="StudyMate",
    page_icon="📚",
    layout="wide",
)

# Streamlit reruns this file after interactions; session state keeps the JWT.
st.session_state.setdefault("token", None)
st.session_state.setdefault("email", "")
st.session_state.setdefault("user_id", None)
st.session_state.setdefault("selected_room_id", None)
st.session_state.setdefault("upload_version", 0)


def main() -> None:
    """Choose the screen based on authentication and room selection."""
    if not st.session_state.token:
        show_login_page()
        return

    with st.sidebar:
        st.write(f"Signed in as **{st.session_state.email}**")
        if st.button("Log out"):
            st.session_state.token = None
            st.session_state.email = ""
            st.session_state.selected_room_id = None
            st.rerun()

    selected_room_id = st.session_state.selected_room_id
    if selected_room_id is not None:
        show_room(selected_room_id)
    else:
        show_room_list()


if __name__ == "__main__":
    main()