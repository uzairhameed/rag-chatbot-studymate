"""StudyMate Streamlit entry point."""

import mimetypes

import streamlit as st

from frontend.api_client import (
    create_room,
    get_all_room_history,
    list_room_files,
    list_rooms,
    login_user,
    register_user,
    send_chat_message,
    upload_room_file,
)


SUPPORTED_EXTENSIONS = [
    "pdf", "docx", "csv", "txt", "md", "pptx",
    "png", "jpg", "jpeg", "webp",
    "mp3", "wav", "m4a", "ogg", "flac",
    "mp4", "mov", "avi", "mkv", "webm",
]

st.set_page_config(
    page_title="StudyMate",
    page_icon="📚",
    layout="wide",
)

# Streamlit reruns this file after interactions; session state keeps the JWT.
st.session_state.setdefault("token", None)
st.session_state.setdefault("email", "")
st.session_state.setdefault("selected_room_id", None)
st.session_state.setdefault("upload_version", 0)


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
            try:
                token_data = login_user(login_email, login_password)
                st.session_state.token = token_data["access_token"]
                st.session_state.email = login_email.strip().lower()
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
            try:
                register_user(username, register_email, register_password)

                # Registration returns a user record, so log in to obtain its JWT.
                token_data = login_user(register_email, register_password)
                st.session_state.token = token_data["access_token"]
                st.session_state.email = register_email.strip().lower()
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


def show_room_list() -> None:
    """Show the user's rooms and a form for creating another one."""
    st.title("Your study rooms")
    st.caption(f"Signed in as {st.session_state.email}")

    with st.expander("Create a room", expanded=False):
        with st.form("create_room_form", clear_on_submit=True):
            room_name = st.text_input("Room name")
            room_description = st.text_area("Description")
            create_submitted = st.form_submit_button("Create room")

        if create_submitted:
            if not room_name.strip():
                st.error("Enter a room name.")
            else:
                try:
                    create_room(
                        st.session_state.token,
                        room_name.strip(),
                        room_description.strip(),
                    )
                    st.success("Room created.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

    try:
        rooms = list_rooms(st.session_state.token)
    except Exception as exc:
        st.error(str(exc))
        return

    if not rooms:
        st.info("You don't have any rooms yet. Create one above to get started.")
        return

    for room in rooms:
        with st.container(border=True):
            st.subheader(room["name"])
            if room.get("description"):
                st.write(room["description"])

            if st.button("Enter room", key=f"enter_room_{room['id']}"):
                st.session_state.selected_room_id = room["id"]
                st.rerun()


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
        st.subheader("Room files")

        # Changing the widget key clears its selected file after a successful upload.
        upload_key = f"upload_{room_id}_{st.session_state.upload_version}"
        selected_file = st.file_uploader(
            "Choose a study file",
            type=SUPPORTED_EXTENSIONS,
            key=upload_key,
        )

        if st.button(
            "Upload file",
            key=f"upload_button_{room_id}",
            disabled=selected_file is None,
            use_container_width=True,
        ):
            try:
                content_type = (
                    selected_file.type
                    or mimetypes.guess_type(selected_file.name)[0]
                    or "application/octet-stream"
                )
                with st.spinner("Uploading and indexing file..."):
                    result = upload_room_file(
                        st.session_state.token,
                        room_id,
                        selected_file.name,
                        selected_file.getvalue(),
                        content_type,
                    )
                st.success(
                    f"Uploaded {selected_file.name}: "
                    f"{result['chunks_created']} chunks indexed."
                )
                st.session_state.upload_version += 1
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

        try:
            files = list_room_files(st.session_state.token, room_id)
        except Exception as exc:
            st.error(str(exc))
            files = []

        if not files:
            st.info("No files uploaded to this room yet.")

        status_badges = {
            "ready": "✅ Ready",
            "processing": "⏳ Processing",
            "failed": "❌ Failed",
        }
        for uploaded_file in files:
            with st.container(border=True):
                st.write(f"**{uploaded_file['filename']}**")
                st.caption(uploaded_file["file_type"])
                st.write(
                    status_badges.get(
                        uploaded_file["status"],
                        uploaded_file["status"],
                    )
                )
                if uploaded_file.get("error_message"):
                    st.caption(uploaded_file["error_message"])

    with chat_column:
        st.subheader("Chat")

        try:
            history = get_all_room_history(st.session_state.token, room_id)
        except Exception as exc:
            st.error(str(exc))
            history = []

        if not history:
            st.info("Ask a question about the files in this room.")

        for message in history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

                # Every assistant message displays Sources, even when the list is empty.
                if message["role"] == "assistant":
                    with st.expander("Sources"):
                        sources = message.get("sources") or []
                        if not sources:
                            st.write("No sources found")
                        for source in sources:
                            st.markdown(
                                f"**{source['filename']}** · "
                                f"`{source['file_type']}` · "
                                f"chunk {source['chunk_index']}"
                            )
                            st.caption(source["excerpt"])

        query = st.chat_input("Ask a question about this room")
        if query:
            try:
                with st.spinner("Searching your files and writing an answer..."):
                    send_chat_message(
                        st.session_state.token,
                        room_id,
                        query,
                    )
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


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
