"""
Developer Agent - Connects to Band platform via SDK.
Receives architecture designs and generates production code.
"""
import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [DEVELOPER] %(message)s",
)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the DEVELOPER agent in a multi-agent software development team on Band.

Your role: Receive architecture designs and write production-quality code.

When @mentioned with architecture, respond with complete, runnable code files:
```
FILE: path/to/file.ext
```language
// Complete code here
```

Include: package config, env template, build/run instructions.
Rules: Write COMPLETE code (no placeholders), include error handling, follow the architecture precisely.
"""


async def main():
    agent_id = os.getenv("BAND_DEVELOPER_ID", "")
    api_key = os.getenv("BAND_DEVELOPER_KEY", "")
    dashscope_key = os.getenv("DASHSCOPE_API_KEY", "")
    dashscope_url = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")

    if not all([agent_id, api_key, dashscope_key]):
        logger.error("Missing required environment variables.")
        return

    try:
        from thenvoi import Agent
        from thenvoi.adapters import LangGraphAdapter

        llm = ChatOpenAI(
            model=os.getenv("LLM_MODEL", "qwen3.7-plus"),
            api_key=dashscope_key,
            base_url=dashscope_url,
            temperature=0.2,
        )

        adapter = LangGraphAdapter(
            llm=llm,
            checkpointer=InMemorySaver(),
        )

        agent = Agent.create(
            adapter=adapter,
            agent_id=agent_id,
            api_key=api_key,
        )

        logger.info(f"Developer agent connecting to Band... ID: {agent_id[:8]}...")
        await agent.run()

    except ImportError:
        logger.warning("Band SDK not installed. Running in standalone mode.")
        await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"Developer agent error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
