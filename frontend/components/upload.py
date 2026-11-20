"""Upload and file list panel for a study room."""

import mimetypes

import streamlit as st

from frontend.api_client import list_room_files, upload_room_file


SUPPORTED_EXTENSIONS = [
    "pdf", "docx", "csv", "txt", "md", "pptx",
    "png", "jpg", "jpeg", "webp",
    "mp3", "wav", "m4a", "ogg", "flac",
    "mp4", "mov", "avi", "mkv", "webm",
]


def show_upload_panel(room_id: int) -> None:
    """Render a room's uploader and uploaded file list."""
    st.subheader("Room files")

    upload_key = f"single_upload_{room_id}_{st.session_state.upload_version}"
    selected_file = st.file_uploader(
        "Choose a study file",
        type=SUPPORTED_EXTENSIONS,
        key=upload_key,
        accept_multiple_files=False,
    )

    upload_supported = (
        selected_file is not None
        and "." in selected_file.name
        and selected_file.name.rsplit(".", 1)[-1].lower()
        in SUPPORTED_EXTENSIONS
    )

    if selected_file is not None and not upload_supported:
        st.error("That file type isn't supported. Choose a listed format.")

    if st.button(
        "Upload file",
        key=f"upload_button_{room_id}",
        disabled=not upload_supported,
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