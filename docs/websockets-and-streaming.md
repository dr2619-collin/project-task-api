# WebSockets and Streaming

Module 11 compares communication styles while keeping REST as the normal
interface for Project and Task operations.

## Endpoint reference

- `GET /api/v1/projects/stream` is a protected, finite HTTP event stream for
  members and administrators.
- `ws://localhost:8000/ws/messages` is a public classroom WebSocket that
  broadcasts received text as JSON to other clients connected to the same
  application process. The sender does not receive an echo.

| Model | Connection and direction | Good fit |
|---|---|---|
| REST | One request followed by one complete response | CRUD and resource queries |
| HTTP streaming | One request followed by progressive server-to-client chunks | Exports, logs, progress, and feeds |
| WebSocket | One upgraded, persistent, full-duplex connection | Interactive live messages and collaboration |

Full-duplex means that client and server can each send messages independently
after the connection opens. It does not make messages durable or automatically
broadcast them. Project and Task data continue to use REST and PostgreSQL; the
demonstrations do not change those business resources.

## Protected HTTP event stream

`GET /api/v1/projects/stream` requires a valid member or administrator Bearer
token. Its async generator yields three Server-Sent Event-style frames and then
finishes. It uses `asyncio.sleep()` between events to yield control while
waiting, and it does not open a database session or transaction.

Run the API, then use curl's `-N` option to disable output buffering so the
events can be seen as they arrive:

```bash
curl -N \
  -H "Authorization: Bearer member-demo-token" \
  http://localhost:8000/api/v1/projects/stream
```

OpenAPI describes this HTTP operation, including the `200 text/event-stream`
and `401 application/problem+json` responses. `TestClient` can check the
completed response and event framing, but it does not prove that a real network
client observes each chunk at a separate moment. The `curl -N` command
demonstrates progressive delivery.

## WebSocket lifecycle and broadcast

The client begins with an HTTP upgrade handshake to `/ws/messages`. The server
accepts the upgrade, registers the persistent connection, receives text
messages, and sends JSON messages. When a client disconnects, the server
removes that connection. After the upgrade, either side can send messages over
the same connection.

Each text message is broadcast to every other active client as JSON, for
example:

```json
{"type": "message", "message": "Hello from the client"}
```

Try it in Postman by creating a **WebSocket** request, connecting to
`ws://localhost:8000/ws/messages`, entering a text message, and selecting
**Send**. The JSON response appears in Postman's message pane.

Alternatively, run this in a browser console:

```javascript
const socket = new WebSocket("ws://localhost:8000/ws/messages");
socket.onmessage = (event) => console.log(event.data);
socket.onopen = () => socket.send("Hello from the browser");
```

Open two browser tabs and run the snippet in each to see a message reach both
clients. When a site is served over HTTPS, production clients use `wss://` so
the WebSocket connection is encrypted.

## State and deployment boundaries

The connection manager keeps active WebSocket objects in application memory.
This is temporary connection state, not durable PostgreSQL business data. One
manager can broadcast only to clients connected to that same application
process. A multi-instance deployment needs additional architecture, commonly a
shared publish/subscribe system; its reverse proxy must also support WebSocket
upgrades. This module intentionally does not implement that infrastructure.

The WebSocket is public only to keep the local classroom demonstration focused
on the protocol and connection lifecycle. Production systems need an explicit
authentication design. Do not put long-lived Bearer tokens in query strings.

## Why the WebSocket is not in Swagger UI

OpenAPI describes HTTP request/response operations; it does not define a
WebSocket operation. Because Swagger UI is generated from the application's
OpenAPI document, `/ws/messages` does not appear in Swagger UI or under the
`paths` in `/openapi.json`. The WebSocket still works and should be tested with
a WebSocket-aware client such as Postman or the browser-console example above.
HTTP response-conformance tools such as Schemathesis do not test the WebSocket
message protocol.
