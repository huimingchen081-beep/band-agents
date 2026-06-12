"""
Architect Agent - Connects to Band platform via SDK.
Analyzes requirements and produces system architecture designs.
"""
import asyncio
import logging
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [ARCHITECT] %(message)s",
)
logger = logging.getLogger(__name__)

# Agent role definition
SYSTEM_PROMPT = """You are the ARCHITECT agent in a multi-agent software development team operating on the Band platform.

Your role: Analyze project requirements and produce comprehensive system architecture.

When someone @mentions you with project requirements, respond with:
### 1. Project Overview (brief summary)
### 2. System Architecture (components + data flow)
### 3. Technology Stack (recommendations + justification)
### 4. API Design (endpoints, models, auth)
### 5. File Structure (directory layout)
### 6. Implementation Roadmap (phases + milestones)

Rules:
- Be specific and actionable
- Use industry best practices
- Consider scalability, security, maintainability
- Keep it concise (800-1200 words)
- You are on the Band platform - communicate clearly through chat
"""


async def main():
    """Connect Architect agent to Band platform."""
    agent_id = os.getenv("BAND_ARCHITECT_ID", "")
    api_key = os.getenv("BAND_ARCHITECT_KEY", "")
    dashscope_key = os.getenv("DASHSCOPE_API_KEY", "")
    dashscope_url = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")

    if not all([agent_id, api_key, dashscope_key]):
        logger.error("Missing required environment variables. Check .env file.")
        return

    try:
        from thenvoi import Agent
        from thenvoi.adapters import LangGraphAdapter
        from thenvoi.config import load_agent_config

        # Create LLM with DashScope compatible endpoint
        llm = ChatOpenAI(
            model=os.getenv("LLM_MODEL", "qwen3.7-plus"),
            api_key=dashscope_key,
            base_url=dashscope_url,
            temperature=0.3,
        )

        # Create adapter with architect system prompt
        adapter = LangGraphAdapter(
            llm=llm,
            checkpointer=InMemorySaver(),
        )

        # Create and connect agent
        agent = Agent.create(
            adapter=adapter,
            agent_id=agent_id,
            api_key=api_key,
            ws_url=os.getenv("BAND_WS_URL", "wss://app.band.ai/api/v1/socket/websocket"),
            rest_url=os.getenv("BAND_REST_URL", "https://app.band.ai/"),
        )

        logger.info(f"Architect agent connecting to Band... ID: {agent_id[:8]}...")
        await agent.run()

    except ImportError:
        logger.warning("Band SDK not installed. Running in standalone mode.")
        logger.info("Architect agent initialized (standalone mode)")
        logger.info("Install band-sdk: pip install band-sdk[langgraph]")
        # Keep running for demo
        await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"Architect agent error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
