"""Integration tests for the Module 11 real-time transport demonstrations."""

from starlette.testclient import TestClient


STREAM_PATH = "/api/v1/projects/stream"
EXPECTED_EVENTS = [
    (
        "event: project-update\n"
        f'data: {{"sequence": {sequence}, "message": "Demonstration project update"}}'
    )
    for sequence in range(1, 4)
]


def test_stream_requires_bearer_authentication(memory_client: TestClient) -> None:
    """An unauthenticated stream request uses the shared Problem Details policy."""
    response = memory_client.get(STREAM_PATH)

    assert response.status_code == 401
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json()["type"].endswith("/unauthorized")
    assert response.json()["instance"] == STREAM_PATH


def test_member_receives_finite_event_stream(
    memory_client: TestClient,
    member_headers: dict[str, str],
) -> None:
    """TestClient validates the completed stream and its event framing."""
    response = memory_client.get(STREAM_PATH, headers=member_headers)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.text.endswith("\n\n")
    assert response.text.strip().split("\n\n") == EXPECTED_EVENTS


def test_openapi_documents_http_stream_but_not_websocket(
    memory_client: TestClient,
) -> None:
    """OpenAPI describes the HTTP stream, not the separate WebSocket protocol."""
    openapi = memory_client.get("/openapi.json").json()
    operation = openapi["paths"][STREAM_PATH]["get"]

    assert "text/event-stream" in operation["responses"]["200"]["content"]
    assert "application/problem+json" in operation["responses"]["401"]["content"]
    assert "/ws/messages" not in openapi["paths"]


def test_websocket_broadcast_reaches_other_client_not_sender(
    memory_client: TestClient,
) -> None:
    """A sender gets no echo; another connected client receives the JSON."""
    with memory_client.websocket_connect("/ws/messages") as first:
        with memory_client.websocket_connect("/ws/messages") as second:
            first.send_text("Hello to both clients")
            expected = {"type": "message", "message": "Hello to both clients"}

            assert second.receive_json() == expected


def test_remaining_websocket_works_after_peer_disconnects(
    memory_client: TestClient,
) -> None:
    """Removing a disconnected peer leaves the remaining connection usable."""
    with memory_client.websocket_connect("/ws/messages") as remaining:
        with memory_client.websocket_connect("/ws/messages") as departing:
            departing.send_text("Before disconnect")
            remaining.receive_json()

        with memory_client.websocket_connect("/ws/messages") as listener:
            remaining.send_text("Still connected")

            assert listener.receive_json() == {
                "type": "message",
                "message": "Still connected",
            }
