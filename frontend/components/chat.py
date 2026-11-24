"""Chat panel for a study room."""

import re
import streamlit as st

from frontend.api_client import get_all_room_history, send_chat_message


def show_chat_panel(room_id: int) -> None:
    """Display room history, sources, and the question input."""
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
                        #st.caption(source["excerpt"])
                        excerpt = re.sub(r"(?m)^\s{0,3}#{1,6}\s+", "", source["excerpt"])
                        st.caption(excerpt)

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