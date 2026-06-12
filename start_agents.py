"""
Start all 4 Band agents as separate processes.
Each agent connects to the Band platform via SDK and listens for @mentions.
"""
import os
import sys
import subprocess
import time
import signal
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [LAUNCHER] %(message)s",
)
logger = logging.getLogger(__name__)

AGENTS = [
    {"name": "Architect", "script": "agents/architect_band.py", "emoji": "🏗️"},
    {"name": "Developer", "script": "agents/developer_band.py", "emoji": "💻"},
    {"name": "Reviewer", "script": "agents/reviewer_band.py", "emoji": "🔍"},
    {"name": "QATest", "script": "agents/qatest_band.py", "emoji": "🧪"},
]


def start_agents():
    """Launch all agent processes."""
    processes = []
    base_dir = os.path.dirname(os.path.abspath(__file__))

    logger.info("=" * 60)
    logger.info("Band Agents Launcher - Starting all 4 agents")
    logger.info("=" * 60)

    for agent in AGENTS:
        script_path = os.path.join(base_dir, agent["script"])
        if not os.path.exists(script_path):
            logger.error(f"Agent script not found: {script_path}")
            continue

        logger.info(f"{agent['emoji']} Starting {agent['name']} agent...")
        proc = subprocess.Popen(
            [sys.executable, script_path],
            cwd=base_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        processes.append((agent["name"], proc))
        time.sleep(1)  # Stagger startup

    logger.info(f"\n✅ All {len(processes)} agents started!")
    logger.info("Press Ctrl+C to stop all agents.\n")

    def signal_handler(sig, frame):
        logger.info("\n🛑 Stopping all agents...")
        for name, proc in processes:
            logger.info(f"Stopping {name}...")
            proc.terminate()
        logger.info("All agents stopped.")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Monitor processes
    try:
        while True:
            time.sleep(5)
            for name, proc in processes:
                if proc.poll() is not None:
                    logger.warning(f"⚠️ {name} agent exited with code {proc.returncode}")
                    # Read stderr
                    stderr = proc.stderr.read() if proc.stderr else ""
                    if stderr:
                        logger.error(f"{name} stderr: {stderr[:500]}")
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == "__main__":
    start_agents()
