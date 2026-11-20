import streamlit as st

from frontend.api_client import (
    add_room_member,
    create_room,
    delete_room,
    list_rooms,
)


def show_room_list() -> None:
    """Show the user's rooms and a form for creating another one."""
    st.title("Your rooms")
    st.caption(f"Signed in as {st.session_state.email}")

    with st.expander("Create a room", expanded=False):
        with st.form("create_room_form", clear_on_submit=True):
            room_name = st.text_input("Room name *")
            room_description = st.text_area("Description")
            create_submitted = st.form_submit_button("Create room")

        if create_submitted:
            if not room_name.strip():
                st.error("*Enter a room name.")
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
        room_id = room["id"]

        with st.container(border=True):
            st.subheader(room["name"])
            if room.get("description"):
                st.write(room["description"])

            if st.button("Enter room", key=f"enter_room_{room_id}"):
                st.session_state.selected_room_id = room_id
                st.rerun()

            if room["owner_id"] == st.session_state.user_id:
                with st.expander("Manage room"):
                    with st.form(
                        f"add_member_form_{room_id}",
                        clear_on_submit=True,
                    ):
                        member_email = st.text_input(
                            "Member's account email",
                            key=f"member_email_{room_id}",
                        )
                        add_member_submitted = st.form_submit_button(
                            "Add member"
                        )

                    if add_member_submitted:
                        if not member_email.strip():
                            st.error("Enter the member's account email.")
                        else:
                            try:
                                member = add_room_member(
                                    st.session_state.token,
                                    room_id,
                                    member_email,
                                )
                                st.success(
                                    f"Added {member['email']} to the room."
                                )
                            except Exception as exc:
                                st.error(str(exc))

                    confirmed = st.checkbox(
                        "I understand this permanently deletes the room "
                        "and its files.",
                        key=f"confirm_delete_{room_id}",
                    )
                    if st.button(
                        "Delete room",
                        key=f"delete_room_{room_id}",
                        disabled=not confirmed,
                    ):
                        try:
                            delete_room(st.session_state.token, room_id)
                            st.success("Room deleted.")
                            st.rerun()
                        except Exception as exc:
                            st.error(str(exc))