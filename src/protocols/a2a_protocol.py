from typing import Dict, Any, List, Callable, Optional
from datetime import datetime
import asyncio
import json


class A2AProtocol:
    """
    Agent-to-Agent Protocol implementation for standardized peer-to-peer
    agent coordination and communication
    """

    def __init__(self):
        self.agents: Dict[str, "AgentInterface"] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.message_history: List[Dict[str, Any]] = []
        self.subscriptions: Dict[str, List[str]] = {}

    def register_agent(self, agent_id: str, agent: "AgentInterface"):
        """Register an agent in the A2A network"""
        self.agents[agent_id] = agent
        self.subscriptions[agent_id] = []
        print(f"[A2A] Registered agent: {agent_id}")

    def subscribe(self, agent_id: str, topic: str):
        """Subscribe agent to specific message topics"""
        if agent_id in self.subscriptions:
            if topic not in self.subscriptions[agent_id]:
                self.subscriptions[agent_id].append(topic)

    async def send_message(
        self,
        from_agent: str,
        to_agent: str,
        message_type: str,
        content: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Send message from one agent to another using A2A protocol"""
        message = {
            "from": from_agent,
            "to": to_agent,
            "type": message_type,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        }

        self.message_history.append(message)

        if to_agent in self.agents:
            response = await self.agents[to_agent].receive_message(message)
            return response
        else:
            return {
                "status": "error",
                "message": f"Agent {to_agent} not found",
            }

    async def broadcast(
        self, from_agent: str, topic: str, content: Dict[str, Any]
    ):
        """Broadcast message to all subscribed agents"""
        message = {
            "from": from_agent,
            "topic": topic,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        }

        for agent_id, topics in self.subscriptions.items():
            if topic in topics and agent_id != from_agent:
                if agent_id in self.agents:
                    await self.agents[agent_id].receive_message(message)

    def get_message_history(self, agent_id: Optional[str] = None) -> List[Dict]:
        """Get message history, optionally filtered by agent"""
        if agent_id:
            return [
                msg
                for msg in self.message_history
                if msg["from"] == agent_id or msg["to"] == agent_id
            ]
        return self.message_history


class AgentInterface:
    """Base interface that all agents must implement for A2A compatibility"""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id

    async def receive_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming messages - must be implemented by subclasses"""
        raise NotImplementedError("Agents must implement receive_message")

    async def send_message(
        self,
        protocol: A2AProtocol,
        to_agent: str,
        message_type: str,
        content: Dict[str, Any],
    ):
        """Send message through A2A protocol"""
        return await protocol.send_message(
            self.agent_id, to_agent, message_type, content
        )
