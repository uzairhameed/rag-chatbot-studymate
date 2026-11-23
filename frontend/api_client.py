import os
from typing import Any

import requests

API_BASE_URL = os.getenv(
    "STUDYMATE_API_BASE_URL",
    "http://127.0.0.1:8000",
).rstrip("/")


def _request(
    method: str,
    path: str,
    *,
    token: str | None = None,
    **kwargs: Any,
) -> Any:
    """Send one API request and turn backend errors into readable exceptions."""
    headers = kwargs.pop("headers", {})

    # All protected API calls use the JWT returned by the login endpoint.
    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = requests.request(
        method,
        f"{API_BASE_URL}{path}",
        headers=headers,
        timeout=120,
        **kwargs,
    )

    # DELETE history returns HTTP 204 with no response body.
    if response.status_code == 204:
        return None

    try:
        response_data = response.json()
    except ValueError:
        response_data = {}

    if not response.ok:
        detail = response_data.get("detail", response.text)
        raise RuntimeError(f"API error {response.status_code}: {detail}")

    return response_data


def register_user(username: str, email: str, password: str) -> dict[str, Any]:
    """Create an account using the backend's JSON registration schema."""
    return _request(
        "POST",
        "/auth/register",
        json={"username": username, "email": email, "password": password},
    )


def login_user(email: str, password: str) -> dict[str, Any]:
    """Log in and receive a JWT access token."""
    return _request(
        "POST",
        "/auth/login",
        json={"email": email, "password": password},
    )

def get_current_user(token: str) -> dict[str, Any]:
    """Return the signed-in user's profile."""
    return _request("GET", "/auth/me", token=token)

def list_rooms(token: str) -> list[dict[str, Any]]:
    """Return rooms owned by the signed-in user."""
    return _request("GET", "/rooms/", token=token)


def create_room(
    token: str,
    name: str,
    description: str,
) -> dict[str, Any]:
    """Create a room for the signed-in user."""
    return _request(
        "POST",
        "/rooms/",
        token=token,
        json={"name": name, "description": description},
    )

def delete_room(token: str, room_id: int) -> None:
    """Delete a room through the owner-only API endpoint."""
    _request("DELETE", f"/rooms/{room_id}", token=token)


def add_room_member(
    token: str,
    room_id: int,
    email: str,
) -> dict[str, Any]:
    """Add an existing user to a room through the owner-only API endpoint."""
    return _request(
        "POST",
        f"/rooms/{room_id}/members",
        token=token,
        json={"email": email.strip().lower()},
    )

def list_room_files(token: str, room_id: int) -> list[dict[str, Any]]:
    """List file names and processing statuses for a room."""
    return _request("GET", f"/upload/{room_id}", token=token)


def upload_room_file(
    token: str,
    room_id: int,
    filename: str,
    content: bytes,
    content_type: str,
) -> dict[str, Any]:
    """Upload one file using the API's multipart form field named 'file'."""
    return _request(
        "POST",
        f"/upload/{room_id}",
        token=token,
        files={"file": (filename, content, content_type)},
    )


def send_chat_message(
    token: str,
    room_id: int,
    query: str,
) -> dict[str, Any]:
    """Send a question and receive its answer and source list."""
    return _request(
        "POST",
        f"/chat/{room_id}",
        token=token,
        json={"query": query},
    )


def get_room_history(
    token: str,
    room_id: int,
    *,
    skip: int = 0,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Load saved messages in chronological order."""
    return _request(
        "GET",
        f"/chat/{room_id}/history",
        token=token,
        params={"skip": skip, "limit": limit},
    )


def clear_room_history(token: str, room_id: int) -> None:
    """Clear history through the owner-only API endpoint."""
    _request("DELETE", f"/chat/{room_id}/history", token=token)


def get_all_room_history(token: str, room_id: int) -> list[dict[str, Any]]:
    """Fetch every message by following the history endpoint's pagination."""
    page_size = 100
    all_messages: list[dict[str, Any]] = []
    skip = 0

    while True:
        page = get_room_history(
            token,
            room_id,
            skip=skip,
            limit=page_size,
        )
        all_messages.extend(page)

        if len(page) < page_size:
            return all_messages

        skip += page_size
