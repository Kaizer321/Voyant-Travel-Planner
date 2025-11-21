from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from threading import Lock


class MCPContext:
    """
    Model Context Protocol (MCP) implementation for shared contextual
    understanding across agents
    """

    def __init__(self):
        self.context_store: Dict[str, Any] = {}
        self.dependencies: Dict[str, List[str]] = {}
        self.access_log: List[Dict[str, Any]] = []
        self.vector_clocks: Dict[str, int] = {}  # Simulated vector clock per key
        self.lock = Lock()

    def set_context(
        self, key: str, value: Any, agent_id: str, dependencies: List[str] = None
    ):
        """Set context value with dependency tracking"""
        with self.lock:
            self.vector_clocks[key] = self.vector_clocks.get(key, 0) + 1
            
            self.context_store[key] = {
                "value": value,
                "agent_id": agent_id,
                "timestamp": datetime.utcnow().isoformat(),
                "version": self.vector_clocks[key],
                "vector_clock": self.vector_clocks[key],
            }

            if dependencies:
                self.dependencies[key] = dependencies

            self._log_access(agent_id, "set", key)

    def get_context(self, key: str, agent_id: str) -> Optional[Any]:
        """Get context value"""
        with self.lock:
            if key in self.context_store:
                self._log_access(agent_id, "get", key)
                return self.context_store[key]["value"]
            return None

    def update_context(
        self, key: str, updates: Dict[str, Any], agent_id: str
    ) -> bool:
        """Update existing context value"""
        with self.lock:
            if key not in self.context_store:
                return False

            current_value = self.context_store[key]["value"]
            if isinstance(current_value, dict):
                current_value.update(updates)
                self.vector_clocks[key] = self.vector_clocks.get(key, 0) + 1
                
                self.context_store[key]["value"] = current_value
                self.context_store[key]["timestamp"] = datetime.utcnow().isoformat()
                self.context_store[key]["version"] = self.vector_clocks[key]
                self.context_store[key]["vector_clock"] = self.vector_clocks[key]
                self._log_access(agent_id, "update", key)
                return True
            return False

    def get_dependent_contexts(self, key: str) -> List[str]:
        """Get all contexts that depend on this key"""
        dependents = []
        for ctx_key, deps in self.dependencies.items():
            if key in deps:
                dependents.append(ctx_key)
        return dependents

    def get_full_context(self) -> Dict[str, Any]:
        """Get complete context snapshot"""
        return {k: v["value"] for k, v in self.context_store.items()}

    def clear_context(self, key: str, agent_id: str):
        """Clear specific context"""
        with self.lock:
            if key in self.context_store:
                del self.context_store[key]
                if key in self.dependencies:
                    del self.dependencies[key]
                self._log_access(agent_id, "clear", key)

    def _get_next_version(self, key: str) -> int:
        """Get next version number for context key"""
        if key in self.context_store:
            return self.context_store[key].get("version", 0) + 1
        return 1

    def _log_access(self, agent_id: str, operation: str, key: str):
        """Log context access for audit trail"""
        self.access_log.append(
            {
                "agent_id": agent_id,
                "operation": operation,
                "key": key,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    def get_access_log(self, agent_id: Optional[str] = None) -> List[Dict]:
        """Get access log, optionally filtered by agent"""
        if agent_id:
            return [log for log in self.access_log if log["agent_id"] == agent_id]
        return self.access_log

    def detect_conflicts(self) -> List[Dict[str, Any]]:
        """Detect conflicting context updates"""
        conflicts = []
        
        for key, deps in self.dependencies.items():
            for dep in deps:
                if dep not in self.context_store:
                    conflicts.append(
                        {
                            "type": "missing_dependency",
                            "key": key,
                            "missing_dependency": dep,
                        }
                    )
        
        return conflicts

    def semantic_merge(self, key: str, value1: Any, value2: Any) -> Any:
        """
        Semantic merge operation for conflict resolution (stub).
        In a real distributed system, this would reconcile divergent states.
        """
        # Simple strategy: prefer the one with more keys if dict, else value2
        if isinstance(value1, dict) and isinstance(value2, dict):
            merged = value1.copy()
            merged.update(value2)
            return merged
        return value2
