# WebSockets and Streaming

Module 11 compares communication styles while keeping REST as the normal
interface for Project and Task operations.

## WebSockets: essential concepts

- A client starts with an HTTP request that asks to upgrade the connection to
  WebSocket. If the server accepts, both sides use the same connection for
  WebSocket messages.
- The connection stays open until the client or server closes it. After the
  handshake, either side can send messages independently, so the server can
  push updates without waiting for another client request or poll.
- Avoiding a new HTTP request for each message can make interactive exchanges
  more direct. The open connection still uses server resources, and its
  capacity depends on connection limits, message handling, and deployment.
- FastAPI provides a `WebSocket` object and a `@router.websocket(...)`
  decorator. An endpoint accepts a connection, receives or sends text and
  binary messages, and can use a connection manager to track clients or
  broadcast messages.
- FastAPI WebSocket handlers can use `async` and `await` for socket I/O. While
  one handler waits for a message, the event loop can make progress on other
  ready connections.
- Common uses include chat, notifications, multiplayer games, and collaborative
  applications that need ongoing interaction.

Full-duplex means that client and server can each send messages independently
after the connection opens. It does not make messages durable or automatically
broadcast them. Project and Task data continue to use REST and PostgreSQL; the
demonstrations do not change those business resources.

## WebSocket lifecycle and broadcast

The public classroom endpoint `ws://localhost:8000/ws/messages` demonstrates
this lifecycle:

- Each connected client is registered in the process-local connection manager.
- The endpoint receives text from a client and broadcasts it as JSON to the
  other connected clients; the sender does not receive an echo.
- When a client disconnects, its connection is removed from the manager.

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

### Why the WebSocket is not in Swagger UI

OpenAPI describes HTTP request/response operations; it does not define a
WebSocket operation. Because Swagger UI is generated from the application's
OpenAPI document, `/ws/messages` does not appear in Swagger UI or under the
`paths` in `/openapi.json`. The WebSocket still works and should be tested with
a WebSocket-aware client such as Postman or the browser-console example above.
HTTP response-conformance tools such as Schemathesis do not test the WebSocket
message protocol.

### Connection manager

The connection manager stores active WebSocket objects in an in-memory set:

- `connect` accepts a client's connection and adds it to the set.
- `broadcast` sends a JSON message to each connected client except the sender.
- `disconnect` removes a client's connection so future broadcasts skip it.

The set represents currently open connections. It is temporary application
state, separate from durable Project and Task data in PostgreSQL.

## HTTP streaming: protected event stream

An HTTP streaming response sends parts of one response as they become
available:

- The client makes a normal HTTP request; the server sends data progressively
  in the response.
- The client can process each chunk without waiting for the complete result.
- In FastAPI, `StreamingResponse` sends chunks from an iterator or generator.
- For a large export, the server can read database rows in batches and write
  them as chunks, avoiding construction of one large in-memory result. This
  benefit requires the data source and application to stream incrementally.
- The stream itself is one-way. The client does not send messages back through
  the open response.

`GET /api/v1/projects/stream` is a protected, finite event stream for members
and administrators. It requires a valid Bearer token. Its async generator
yields three Server-Sent Event-style frames and then finishes. It uses
`asyncio.sleep()` between events to yield control while waiting, and it does not
open a database session or transaction.

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

## Async handling and concurrent clients

The stream generator and WebSocket handler are asynchronous. When a handler
awaits network I/O, such as waiting for a message or sending a frame, it pauses
so the server can make progress on other ready connections. This supports
concurrent I/O interactions; it does not guarantee lower latency or higher
throughput for every workload. Capacity still depends on server resources,
connection limits, and any downstream work.

The HTTP event stream is one-way: the client makes an HTTP request and the
server sends events over that response. A WebSocket is two-way after its
handshake: either side can send messages over the persistent connection.

## Compare the communication approaches

| **Model**      | **Connection and direction**                                 | **Good fit**                                |
| -------------- | ------------------------------------------------------------ | ------------------------------------------- |
| REST           | One request followed by one complete response               | CRUD and resource queries                   |
| HTTP streaming | One request followed by progressive server-to-client chunks | Exports, logs, progress, and feeds          |
| WebSocket      | One upgraded, persistent, full-duplex connection             | Interactive live messages and collaboration |

### Tradeoffs between the approaches

| **Approach**          | **Benefit**                                                                                    | **Tradeoff**                                                                                                                |
| --------------------- | ---------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| REST request/response | Simple request and response lifecycle; well suited to CRUD and resource queries                | The client receives a complete result for each request; ongoing two-way interaction requires additional requests            |
| HTTP streaming        | Delivers results progressively over one HTTP response; useful for large exports and long feeds | The client must process chunks as they arrive and handle an incomplete stream if the connection fails                       |
| WebSocket             | Both sides can send messages over one persistent connection                                    | Connections consume resources while open and require explicit lifecycle, authorization, backpressure, and scaling decisions |

### HTTP streaming and WebSockets compared

| **Feature**     | **HTTP streaming response**                                      | **WebSocket**                                                               |
| --------------- | ---------------------------------------------------------------- | --------------------------------------------------------------------------- |
| Connection      | One HTTP request stays open while the response is sent           | An HTTP upgrade handshake opens a persistent connection                     |
| Communication   | Server to client for that response                               | Two-way; either side can send messages                                      |
| Typical uses    | Large downloads, exports, logs, and progress updates             | Chat, notifications, and collaborative interaction                         |
| Client behavior | Processes response chunks as they arrive                         | Sends and receives messages over the open connection                        |
| Main tradeoff   | Client handles a progressive response and possible interruption  | Server manages connection lifecycle, resources, authorization, and scaling |


