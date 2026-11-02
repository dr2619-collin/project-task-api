# Module 11 — Real-Time Communication

Choose a communication style based on how information needs to move and how
long the interaction lasts. These principles apply across languages,
frameworks, and protocols.

## Match the communication pattern to the need

- Use request/response when a client asks for an operation or resource and
  receives a complete result.
- Use streaming when one side needs to deliver a sequence of updates over a
  single request or connection.
- Use a persistent, two-way channel when both sides need to send messages
  independently without opening a new request for each message.

These patterns solve different problems. A persistent connection is not
automatically a better replacement for ordinary resource APIs; keep CRUD and
other request/response operations in the style that best fits them.

## Define message behavior as a contract

Real-time protocols still need clear contracts. Specify the message shape,
meaning, direction, and expected behavior for invalid or unexpected messages.
Clients should not have to infer message meaning from undocumented conventions.

Treat connection lifecycle and message behavior as public behavior too:

- Define what happens when a client connects and disconnects.
- Decide whether messages go to the sender, selected subscribers, or all
  connected clients.
- Handle disconnects and delivery failures without leaving stale connections.
- Test the protocol with tools that understand the protocol; an HTTP API
  schema does not describe a WebSocket message exchange.

## Be explicit about state and delivery scope

An active connection is temporary state. Decide which component owns that
state, how long it lives, and what happens when the process restarts. Do not
confuse an in-memory connection registry with durable application data.

An in-process broadcast reaches only clients connected to that process. If an
application runs in multiple processes or instances, each may have a different
connection registry. Cross-instance delivery requires shared coordination,
such as a publish/subscribe service or message broker. Choose that architecture
when the deployment and delivery requirements need it; do not imply that a
local broadcast is globally distributed.

## Plan security and resource limits

Persistent connections consume resources for as long as they remain open.
Production systems should define connection limits, timeouts, backpressure or
slow-client behavior, and authorization rules. Authenticate and authorize a
connection according to the same access policy as other application
operations, while accounting for how credentials are safely supplied during
the connection handshake.

## Keep protocol concerns at the boundary

Connection handling, message framing, and transport-specific errors belong at
the communication boundary. Keep application rules independent of WebSocket
or streaming response classes so those rules can be reused by other entry
points. Add a separate real-time component when it helps isolate connection
management from ordinary request/response services.

For the concrete HTTP stream and WebSocket examples, endpoint behavior, and
testing notes in this project, see [WebSockets and Streaming](../websockets-and-streaming.md).
