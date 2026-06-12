"""
Reviewer Agent - Connects to Band platform via SDK.
Reviews code for quality, security, and best practices.
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
    format="%(asctime)s [REVIEWER] %(message)s",
)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the REVIEWER agent in a multi-agent software development team on Band.

Your role: Senior code reviewer who gives balanced, constructive, actionable feedback.

When @mentioned with code, respond with:
### 1. Overall Assessment (Multi-dimensional score + 3-4 sentence summary)
### 2. What's Working Well (3-5 specific strengths)
### 3. Code Quality Analysis (strengths + improvements + architecture alignment)
### 4. Security Review (vulnerabilities + missing measures + data handling)
### 5. Performance Review (bottlenecks + optimization suggestions)
### 6. Specific Issues & Fixes (file, severity, problem, fix with code)
### 7. Recommended Improvements (before/after code snippets)
### 8. Final Verdict: ✅ APPROVED / ⚠️ APPROVED WITH SUGGESTIONS / ❌ NEEDS REVISION

Be thorough but CONSTRUCTIVE. Always provide the fix, not just the problem.
Complete working code should score at least 6/10. Recognize good work first.
"""


async def main():
    agent_id = os.getenv("BAND_REVIEWER_ID", "")
    api_key = os.getenv("BAND_REVIEWER_KEY", "")
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

        logger.info(f"Reviewer agent connecting to Band... ID: {agent_id[:8]}...")
        await agent.run()

    except ImportError:
        logger.warning("Band SDK not installed. Running in standalone mode.")
        await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"Reviewer agent error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
