import logging
import operator
import os
import sys
from typing import Annotated, Sequence, TypedDict

import aiosqlite
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from config import APP_NAME
from utils.model_registry import ModelFactory
from utils.chat_providers import register_builtin_providers

# Register available providers at startup
register_builtin_providers()

try:
    from backend.src.utils.mcp_client import MCPClient
except ImportError:
    from utils.mcp_client import MCPClient

# Setup logger
logger = logging.getLogger(__name__)

# --- Types ---

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

class ChatbotAgent:
    def __init__(self):
        self.mcp_client = MCPClient(
            command=sys.executable,
            args=[os.path.join(os.path.dirname(__file__), "utils/mcp_server.py")],
            env=os.environ.copy()
        )
        self.tools = []
        self.model = None
        self.workflow = None
        self.app = None
        self._setup_storage()
        
        self.system_message = self._load_training_data()

    def _setup_storage(self):
        """Setup data directory and database path"""
        # Database setup: Use /home/data on Azure App Service for persistence across deployments
        if os.environ.get("WEBSITE_SITE_NAME"):
            self.data_dir = "/home/data"
        else:
            self.data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
            
        os.makedirs(self.data_dir, exist_ok=True)
        self.db_path = os.path.join(self.data_dir, "chat_history.sqlite")

    async def _init_memory(self):
        """Initialize async sqlite server if not exists"""
        if not hasattr(self, 'conn') or self.conn is None:
            self.conn = await aiosqlite.connect(self.db_path)
            self.memory = AsyncSqliteSaver(self.conn)
            # aiosqlite requires initialization
            await self.memory.setup()


    def _load_training_data(self) -> str:
        base_message = f"You are {APP_NAME}, a helpful AI assistant."
        try:
            kb_path = os.path.join(os.path.dirname(__file__), "..", "training", "knowledge_base.md")
            if os.path.exists(kb_path):
                with open(kb_path, "r") as f:
                    content = f.read()
                    content = content.replace("{{APP_NAME}}", APP_NAME)
                    content = content.replace("{{APP_NAME_LOWER}}", APP_NAME.lower())
                    return f"{base_message}\n\n{content}"
        except Exception as e:
            logger.error(f"Failed to load knowledge base: {e}")
            pass
        return base_message
        
    async def initialize(self):
        # 1. Initialize MCP Connection
        await self.mcp_client.initialize()
        self.tools = await self.mcp_client.get_tools()
        
        # 2. Setup Model
        provider = os.getenv("CHAT_MODEL_PROVIDER")
        if not provider:
            # Fallback for backward compatibility with old env vars
            provider = "azure" if os.getenv("AZURE_OPENAI_API_KEY") else "openai"
            
        self.model = ModelFactory.get_model(provider, tools=self.tools)
        
        # 3. Define Graph
        await self._init_memory()
        
        workflow = StateGraph(AgentState)
        workflow.add_node("agent", self.call_model)
        workflow.add_node("tools", ToolNode(self.tools))
        
        workflow.set_entry_point("agent")
        workflow.add_conditional_edges(
            "agent",
            self.should_continue,
            {"continue": "tools", "end": END}
        )
        workflow.add_edge("tools", "agent")
        
        self.app = workflow.compile(checkpointer=self.memory)
        logger.info(f"Agent Initialized with Tools: {[t.name for t in self.tools]}")

    async def call_model(self, state):
        messages = state['messages']
        # Ensure system message is first if not present
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=self.system_message)] + list(messages)
            
        response = await self.model.ainvoke(messages)
        return {"messages": [response]}

    def should_continue(self, state):
        messages = state['messages']
        last_message = messages[-1]
        if last_message.tool_calls:
            return "continue"
        return "end"

    async def chat(self, message: str, thread_id: str):
        if not self.app:
            await self.initialize()
            
        config = {"configurable": {"thread_id": thread_id}}
        inputs = {"messages": [HumanMessage(content=message)]}
        
        try:
            # Invoke gets the final state of the graph
            final_state = await self.app.ainvoke(inputs, config=config)
            return final_state["messages"][-1].content
        except Exception as e:
            return f"I encountered an error: {str(e)}"

    async def reset_history(self, thread_id: str):
        # We could delete the rows manually, or just let users generate a new thread.
        # But if we must clear a specific thread ID's state:
        await self._init_memory()
        if self.conn:
            try:
                # Remove checkpoints associated with this thread to 'reset' it
                await self.conn.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
                await self.conn.execute("DELETE FROM writes WHERE thread_id = ?", (thread_id,))
                await self.conn.commit()
            except Exception as e:
                logger.error(f"Failed to reset history for {thread_id}: {e}")

    async def cleanup(self):
        await self.mcp_client.close()
        if hasattr(self, 'conn') and self.conn:
            await self.conn.close()
