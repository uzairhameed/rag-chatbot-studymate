import streamlit as st

from frontend.components.chat import show_chat_panel
from frontend.components.upload import show_upload_panel

from frontend.api_client import list_rooms


def show_room(room_id: int) -> None:
    """Show uploaded files beside the room's saved chat conversation."""
    try:
        rooms = list_rooms(st.session_state.token)
        room = next((item for item in rooms if item["id"] == room_id), None)
        if room is None:
            st.error("That room is unavailable.")
            if st.button("Back to rooms"):
                st.session_state.selected_room_id = None
                st.rerun()
            return
    except Exception as exc:
        st.error(str(exc))
        return

    st.title(room["name"])
    if st.button("← Back to rooms"):
        st.session_state.selected_room_id = None
        st.rerun()

    files_column, chat_column = st.columns([1, 2], gap="large")

    with files_column:
        show_upload_panel(room_id)

    with chat_column:
        show_chat_panel(room_id)