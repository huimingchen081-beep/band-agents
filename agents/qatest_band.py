"""
QATest Agent - Connects to Band platform via SDK.
Generates test suites and validates code quality.
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
    format="%(asctime)s [QATEST] %(message)s",
)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the QATEST agent in a multi-agent software development team on Band.

Your role: Generate comprehensive test suites and validate code correctness.

When @mentioned with code + architecture + review, respond with:
### 1. Test Strategy (approach, coverage targets, environment)
### 2. Unit Tests (complete test code files)
### 3. Integration Tests (key scenarios + API tests)
### 4. Edge Cases & Error Scenarios (edge cases to verify)
### 5. Test Data (sample fixtures, mocks)
### 6. CI/CD Integration (runner commands, coverage setup)

Rules: Write COMPLETE runnable tests, cover happy path + error cases, use standard frameworks.
"""


async def main():
    agent_id = os.getenv("BAND_QATEST_ID", "")
    api_key = os.getenv("BAND_QATEST_KEY", "")
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

        logger.info(f"QATest agent connecting to Band... ID: {agent_id[:8]}...")
        await agent.run()

    except ImportError:
        logger.warning("Band SDK not installed. Running in standalone mode.")
        await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"QATest agent error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
