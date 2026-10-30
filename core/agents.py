"""
core/agents.py

Autonomous Multi-Agent Architecture & Action Receipts Engine for MAYA
Implements Module 17 (Autonomous Multi-Agent Architecture) and Module 2 (Explainable Execution & Action Receipts)
from the Personal AI Voice Assistant Product Blueprint.
"""

import os
import time
import json
import uuid
import sqlite3
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class ActionReceipt:
    receipt_id: str
    timestamp: str
    agent_name: str
    tool_name: str
    parameters: Dict[str, Any]
    status: str            # 'SUCCESS', 'FAILED', 'PENDING_APPROVAL', 'CANCELLED'
    execution_time_ms: float
    summary: str
    undo_possible: bool = False
    undo_token: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ActionReceiptStore:
    """Persistent storage for explainable execution action receipts."""

    def __init__(self, db_path: str = "maya_history.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        try:
            with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS action_receipts (
                        receipt_id TEXT PRIMARY KEY,
                        timestamp TEXT,
                        agent_name TEXT,
                        tool_name TEXT,
                        parameters_json TEXT,
                        status TEXT,
                        execution_time_ms REAL,
                        summary TEXT,
                        undo_possible INTEGER,
                        undo_token TEXT
                    )
                """)
                conn.commit()
        except Exception as e:
            print(f"⚠️ ActionReceiptStore init warning: {e}")

    def record_receipt(self, receipt: ActionReceipt):
        try:
            with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO action_receipts
                    (receipt_id, timestamp, agent_name, tool_name, parameters_json, status, execution_time_ms, summary, undo_possible, undo_token)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    receipt.receipt_id,
                    receipt.timestamp,
                    receipt.agent_name,
                    receipt.tool_name,
                    json.dumps(receipt.parameters, ensure_ascii=False),
                    receipt.status,
                    receipt.execution_time_ms,
                    receipt.summary,
                    1 if receipt.undo_possible else 0,
                    receipt.undo_token
                ))
                conn.commit()
        except Exception as e:
            print(f"⚠️ Error recording action receipt: {e}")

    def get_recent_receipts(self, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM action_receipts ORDER BY timestamp DESC LIMIT ?",
                    (limit,)
                )
                rows = cursor.fetchall()
                results = []
                for r in rows:
                    item = dict(r)
                    try:
                        item['parameters'] = json.loads(item.get('parameters_json', '{}'))
                    except Exception:
                        item['parameters'] = {}
                    results.append(item)
                return results
        except Exception as e:
            print(f"⚠️ Error querying action receipts: {e}")
            return []


# Initialize global receipt store
receipt_store = ActionReceiptStore()


class BaseAgent:
    """Base class for specialized autonomous sub-agents."""
    name: str = "BaseAgent"
    description: str = "General agent"

    def __init__(self, tools_map: Dict[str, Any] = None):
        self.tools_map = tools_map or {}

    def handles_domain(self, prompt: str) -> bool:
        """Determines if this agent specializes in the given task prompt."""
        return False

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> tuple[str, ActionReceipt]:
        start_time = time.time()
        receipt_id = f"rcpt_{uuid.uuid4().hex[:8]}"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if tool_name not in self.tools_map:
            elapsed = (time.time() - start_time) * 1000
            receipt = ActionReceipt(
                receipt_id=receipt_id,
                timestamp=timestamp,
                agent_name=self.name,
                tool_name=tool_name,
                parameters=args,
                status="FAILED",
                execution_time_ms=elapsed,
                summary=f"Tool '{tool_name}' not found."
            )
            receipt_store.record_receipt(receipt)
            return f"Error: Tool '{tool_name}' is not recognized.", receipt

        try:
            func = self.tools_map[tool_name]
            result = func(**args)
            elapsed = (time.time() - start_time) * 1000
            res_str = str(result)
            receipt = ActionReceipt(
                receipt_id=receipt_id,
                timestamp=timestamp,
                agent_name=self.name,
                tool_name=tool_name,
                parameters=args,
                status="SUCCESS",
                execution_time_ms=elapsed,
                summary=res_str[:200]
            )
            receipt_store.record_receipt(receipt)
            return res_str, receipt
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            err_str = f"Execution error in {tool_name}: {e}"
            receipt = ActionReceipt(
                receipt_id=receipt_id,
                timestamp=timestamp,
                agent_name=self.name,
                tool_name=tool_name,
                parameters=args,
                status="FAILED",
                execution_time_ms=elapsed,
                summary=err_str
            )
            receipt_store.record_receipt(receipt)
            return err_str, receipt


class OperatingSystemAgent(BaseAgent):
    name = "OperatingSystemAgent"
    description = "Handles desktop automation, applications, file management, hardware controls, and power operations."

    def handles_domain(self, prompt: str) -> bool:
        keywords = ["open", "close", "launch", "volume", "brightness", "wifi", "bluetooth",
                    "window", "screenshot", "battery", "hotspot", "airplane", "power", "shutdown",
                    "restart", "process", "kill", "taskbar", "clean", "organize"]
        prompt_lower = prompt.lower()
        return any(k in prompt_lower for k in keywords)


class BrowserResearchAgent(BaseAgent):
    name = "BrowserResearchAgent"
    description = "Handles internet research, webpage reading and summarization, YouTube navigation, and tab management."

    def handles_domain(self, prompt: str) -> bool:
        keywords = ["search", "google", "youtube", "webpage", "article", "website",
                    "url", "summarize page", "tabs", "browse", "price", "video transcript"]
        prompt_lower = prompt.lower()
        return any(k in prompt_lower for k in keywords)


class CodingDeveloperAgent(BaseAgent):
    name = "CodingDeveloperAgent"
    description = "Handles code generation, debugging, git operations, testing, scaffolding, and security code reviews."

    def handles_domain(self, prompt: str) -> bool:
        keywords = ["code", "git", "commit", "diff", "branch", "debug", "python",
                    "function", "class", "test", "scaffold", "security review", "api", "viva"]
        prompt_lower = prompt.lower()
        return any(k in prompt_lower for k in keywords)


class ProductivityCalendarAgent(BaseAgent):
    name = "ProductivityCalendarAgent"
    description = "Handles reminders, calendar events, agenda preparation, to-do tasks, Pomodoro sessions, and habit tracking."

    def handles_domain(self, prompt: str) -> bool:
        keywords = ["reminder", "timer", "pomodoro", "task", "todo", "calendar",
                    "event", "schedule", "meeting", "agenda", "habit", "deadline", "goal"]
        prompt_lower = prompt.lower()
        return any(k in prompt_lower for k in keywords)


class DocumentRAGAgent(BaseAgent):
    name = "DocumentRAGAgent"
    description = "Handles PDF generation, opening PDFs in system viewer, user-specified PDF reading and extraction, Word documents, Excel spreadsheets, document comparison, duplicate detection, and file RAG."

    def handles_domain(self, prompt: str) -> bool:
        keywords = ["pdf", "word", "docx", "excel", "spreadsheet", "csv", "read document",
                    "report", "presentation", "slides", "compare document", "duplicate file",
                    "generate pdf", "create pdf", "open pdf", "read pdf", "પીડીએફ", "દસ્તાવેજ"]
        prompt_lower = prompt.lower()
        return any(k in prompt_lower for k in keywords)


class SmartHomeIoTAgent(BaseAgent):
    name = "SmartHomeIoTAgent"
    description = "Handles smart home devices, Home Assistant integration, smart plugs, lights, and automated scenes."

    def handles_domain(self, prompt: str) -> bool:
        keywords = ["home assistant", "smart home", "light", "plug", "scene", "thermostat", "iot", "fan", "mqtt"]
        prompt_lower = prompt.lower()
        return any(k in prompt_lower for k in keywords)


class SecurityAuditAgent(BaseAgent):
    name = "SecurityAuditAgent"
    description = "Handles audit logging, permission checks, emergency stop, data privacy, and safe power confirmations."

    def handles_domain(self, prompt: str) -> bool:
        keywords = ["audit", "receipt", "emergency stop", "cancel all", "privacy", "export data", "wipe data"]
        prompt_lower = prompt.lower()
        return any(k in prompt_lower for k in keywords)


class MultiAgentOrchestrator:
    """
    Central AI Orchestrator coordinating specialized sub-agents,
    handling task decomposition, scoped context passing, and explainable action receipts.
    """

    def __init__(self, tools_map: Dict[str, Any] = None):
        self.tools_map = tools_map or {}
        self.agents = {
            "os": OperatingSystemAgent(self.tools_map),
            "browser": BrowserResearchAgent(self.tools_map),
            "coding": CodingDeveloperAgent(self.tools_map),
            "productivity": ProductivityCalendarAgent(self.tools_map),
            "document": DocumentRAGAgent(self.tools_map),
            "smarthome": SmartHomeIoTAgent(self.tools_map),
            "security": SecurityAuditAgent(self.tools_map),
        }
        self.active_agent = "os"

    def update_tools_map(self, tools_map: Dict[str, Any]):
        self.tools_map = tools_map
        for agent in self.agents.values():
            agent.tools_map = tools_map

    def route_task(self, prompt: str) -> BaseAgent:
        """Determines the most appropriate specialized agent for a task."""
        for key, agent in self.agents.items():
            if agent.handles_domain(prompt):
                self.active_agent = key
                return agent
        return self.agents["os"]

    def execute_with_receipt(self, tool_name: str, args: Dict[str, Any], caller_agent: Optional[str] = None) -> tuple[str, ActionReceipt]:
        """Executes a tool with automatic agent routing and audit receipt generation."""
        agent = self.agents.get(caller_agent) if caller_agent else None
        if not agent:
            # Map tool name to agent category
            if any(k in tool_name for k in ["browser", "web", "youtube", "url"]):
                agent = self.agents["browser"]
            elif any(k in tool_name for k in ["git", "code", "scaffold", "test"]):
                agent = self.agents["coding"]
            elif any(k in tool_name for k in ["calendar", "event", "task", "timer", "pomodoro", "agenda", "habit"]):
                agent = self.agents["productivity"]
            elif any(k in tool_name for k in ["pdf", "docx", "word", "excel", "document", "csv", "duplicate"]):
                agent = self.agents["document"]
            elif any(k in tool_name for k in ["smart", "home_assistant", "plug", "light", "scene"]):
                agent = self.agents["smarthome"]
            elif any(k in tool_name for k in ["audit", "receipt", "emergency", "power", "security"]):
                agent = self.agents["security"]
            else:
                agent = self.agents["os"]

        return agent.execute_tool(tool_name, args)
