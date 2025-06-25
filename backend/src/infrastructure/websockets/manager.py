"""
WebSocket Manager - Handles real-time connections and message broadcasting for dashboard updates.
"""

import json
import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, Optional, Set

from fastapi import WebSocket, WebSocketDisconnect

from core.models.dashboard import (
    ActivityUpdateMessage,
    AlertUpdateMessage,
    ClientUpdateMessage,
    MetricUpdateMessage,
    WebSocketMessage,
)

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections and handles real-time message broadcasting.
    """

    def __init__(self):
        # Store active connections by client_id
        self._connections: Dict[str, Set[WebSocket]] = defaultdict(set)

        # Store connection metadata
        self._connection_info: Dict[WebSocket, Dict[str, Any]] = {}

        # Message queue for reliable delivery
        self._message_queue: Dict[str, list] = defaultdict(list)

        # Connection statistics
        self._stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "connection_errors": 0,
        }

    async def connect(self, websocket: WebSocket, client_id: str, user_info: Optional[Dict] = None):
        """
        Accept a new WebSocket connection and register it for a client.
        """
        try:
            await websocket.accept()

            # Add connection to client's connection set
            self._connections[client_id].add(websocket)

            # Store connection metadata
            self._connection_info[websocket] = {
                "client_id": client_id,
                "user_info": user_info or {},
                "connected_at": datetime.utcnow(),
                "last_ping": datetime.utcnow(),
            }

            # Update statistics
            self._stats["total_connections"] += 1
            self._stats["active_connections"] = self._get_active_connection_count()

            logger.info(
                f"🔗 WebSocket connected for client {client_id}. Active connections: {self._stats['active_connections']}"
            )

            # Send any queued messages
            await self._send_queued_messages(websocket, client_id)

            # Send initial connection confirmation
            await self._send_to_websocket(
                websocket,
                {
                    "type": "connection_established",
                    "client_id": client_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": {
                        "status": "connected",
                        "server_time": datetime.utcnow().isoformat(),
                    },
                },
            )

        except Exception as e:
            logger.error(f"❌ Failed to establish WebSocket connection for {client_id}: {e}")
            self._stats["connection_errors"] += 1
            raise

    async def disconnect(self, websocket: WebSocket):
        """
        Handle WebSocket disconnection and cleanup.
        """
        try:
            # Get connection info
            connection_info = self._connection_info.get(websocket, {})
            client_id = connection_info.get("client_id", "unknown")

            # Remove from connections
            if websocket in self._connections[client_id]:
                self._connections[client_id].remove(websocket)

            # Clean up empty client connection sets
            if not self._connections[client_id]:
                del self._connections[client_id]

            # Remove connection info
            if websocket in self._connection_info:
                del self._connection_info[websocket]

            # Update statistics
            self._stats["active_connections"] = self._get_active_connection_count()

            logger.info(
                f"🔌 WebSocket disconnected for client {client_id}. Active connections: {self._stats['active_connections']}"
            )

        except Exception as e:
            logger.error(f"❌ Error during WebSocket disconnection: {e}")

    async def broadcast_to_client(self, client_id: str, message: WebSocketMessage):
        """
        Broadcast a message to all connections for a specific client.
        """
        try:
            connections = self._connections.get(client_id, set())

            if not connections:
                logger.debug(f"📱 No active connections for client {client_id}, queuing message")
                self._message_queue[client_id].append(message.model_dump())
                # Keep only last 100 messages per client
                self._message_queue[client_id] = self._message_queue[client_id][-100:]
                return

            # Send to all connections for this client
            message_data = message.model_dump()
            disconnected_websockets = []

            for websocket in connections.copy():
                try:
                    await self._send_to_websocket(websocket, message_data)
                    self._stats["messages_sent"] += 1

                except WebSocketDisconnect:
                    logger.debug(f"🔌 WebSocket disconnected during broadcast for {client_id}")
                    disconnected_websockets.append(websocket)

                except Exception as e:
                    logger.error(f"❌ Failed to send message to WebSocket for {client_id}: {e}")
                    disconnected_websockets.append(websocket)

            # Clean up disconnected websockets
            for websocket in disconnected_websockets:
                await self.disconnect(websocket)

            logger.debug(
                f"📡 Broadcasted {message.type} to {len(connections) - len(disconnected_websockets)} connections for {client_id}"
            )

        except Exception as e:
            logger.error(f"❌ Failed to broadcast message to client {client_id}: {e}")

    async def broadcast_metric_update(self, client_id: str, metrics_data: Any):
        """
        Broadcast metrics update to client connections.
        """
        message = MetricUpdateMessage(client_id=client_id, data=metrics_data)
        await self.broadcast_to_client(client_id, message)

    async def broadcast_activity_update(self, client_id: str, activity_data: Any):
        """
        Broadcast new activity to client connections.
        """
        message = ActivityUpdateMessage(client_id=client_id, data=activity_data)
        await self.broadcast_to_client(client_id, message)

    async def broadcast_alert_update(self, client_id: str, alert_data: Any):
        """
        Broadcast alert update to client connections.
        """
        message = AlertUpdateMessage(client_id=client_id, data=alert_data)
        await self.broadcast_to_client(client_id, message)

    async def broadcast_client_update(self, client_id: str, client_data: Any):
        """
        Broadcast client configuration update.
        """
        message = ClientUpdateMessage(client_id=client_id, data=client_data)
        await self.broadcast_to_client(client_id, message)

    async def handle_websocket_messages(self, websocket: WebSocket, client_id: str):
        """
        Handle incoming messages from WebSocket connection.
        """
        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()

                try:
                    message = json.loads(data)
                    await self._process_client_message(websocket, client_id, message)

                except json.JSONDecodeError:
                    logger.warning(
                        f"⚠️ Invalid JSON received from WebSocket for {client_id}: {data}"
                    )
                    await self._send_error(websocket, "Invalid JSON format")

        except WebSocketDisconnect:
            logger.debug(f"🔌 WebSocket disconnected for {client_id}")
            await self.disconnect(websocket)

        except Exception as e:
            logger.error(f"❌ Error handling WebSocket messages for {client_id}: {e}")
            await self.disconnect(websocket)

    async def _process_client_message(
        self, websocket: WebSocket, client_id: str, message: Dict[str, Any]
    ):
        """
        Process incoming message from client WebSocket.
        """
        message_type = message.get("type", "unknown")

        # Update last ping time
        if websocket in self._connection_info:
            self._connection_info[websocket]["last_ping"] = datetime.utcnow()

        if message_type == "ping":
            # Respond to ping with pong
            await self._send_to_websocket(
                websocket, {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
            )

        elif message_type == "subscribe":
            # Handle subscription to specific data types
            subscription_type = message.get("subscription", "all")
            logger.debug(f"📡 Client {client_id} subscribed to {subscription_type}")

        elif message_type == "unsubscribe":
            # Handle unsubscription
            subscription_type = message.get("subscription", "all")
            logger.debug(f"📡 Client {client_id} unsubscribed from {subscription_type}")

        else:
            logger.warning(f"⚠️ Unknown message type from {client_id}: {message_type}")

    async def _send_to_websocket(self, websocket: WebSocket, data: Dict[str, Any]):
        """
        Send data to a specific WebSocket connection.
        """
        try:
            message_str = json.dumps(data, default=str)
            await websocket.send_text(message_str)

        except Exception as e:
            logger.error(f"❌ Failed to send WebSocket message: {e}")
            raise

    async def _send_error(self, websocket: WebSocket, error_message: str):
        """
        Send error message to WebSocket connection.
        """
        try:
            error_data = {
                "type": "error",
                "message": error_message,
                "timestamp": datetime.utcnow().isoformat(),
            }
            await self._send_to_websocket(websocket, error_data)

        except Exception as e:
            logger.error(f"❌ Failed to send error message: {e}")

    async def _send_queued_messages(self, websocket: WebSocket, client_id: str):
        """
        Send any queued messages to newly connected client.
        """
        try:
            queued_messages = self._message_queue.get(client_id, [])

            for message_data in queued_messages:
                await self._send_to_websocket(websocket, message_data)
                self._stats["messages_sent"] += 1

            # Clear queue after sending
            if client_id in self._message_queue:
                self._message_queue[client_id].clear()

            if queued_messages:
                logger.debug(f"📬 Sent {len(queued_messages)} queued messages to {client_id}")

        except Exception as e:
            logger.error(f"❌ Failed to send queued messages to {client_id}: {e}")

    def _get_active_connection_count(self) -> int:
        """
        Get total number of active WebSocket connections.
        """
        return sum(len(connections) for connections in self._connections.values())

    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get WebSocket connection statistics.
        """
        return {
            **self._stats,
            "clients_connected": len(self._connections),
            "connections_by_client": {
                client_id: len(connections) for client_id, connections in self._connections.items()
            },
            "queue_sizes": {
                client_id: len(queue) for client_id, queue in self._message_queue.items() if queue
            },
        }

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on WebSocket connections.
        """
        try:
            active_connections = self._get_active_connection_count()

            # Check for stale connections
            stale_connections = []
            now = datetime.utcnow()

            for websocket, info in self._connection_info.items():
                last_ping = info.get("last_ping", info.get("connected_at"))
                if last_ping and (now - last_ping).total_seconds() > 300:  # 5 minutes
                    stale_connections.append(websocket)

            # Clean up stale connections
            for websocket in stale_connections:
                await self.disconnect(websocket)

            return {
                "status": "healthy",
                "active_connections": active_connections,
                "stale_connections_removed": len(stale_connections),
                "timestamp": now.isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ WebSocket health check failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }


# Global WebSocket manager instance
_websocket_manager = None


def get_websocket_manager() -> WebSocketManager:
    """
    Get or create global WebSocket manager instance.
    """
    global _websocket_manager

    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()

    return _websocket_manager
