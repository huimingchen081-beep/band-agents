# Band Agents — AI Software Development Team

> **Band of Agents Hackathon 2026** — lablab.ai & band.ai  
> Multi-agent AI system for autonomous software development using the Band SDK.

[![Tech](https://img.shields.io/badge/Band_SDK-1.0-blue)](https://band.ai)
[![LLM](https://img.shields.io/badge/LLM-Qwen_3.7_Plus-purple)](https://dashscope.aliyun.com)
[![Python](https://img.shields.io/badge/Python-3.11+-green)](https://python.org)
[![Flask](https://img.shields.io/badge/Web-Flask-lightgrey)](https://flask.palletsprojects.com)
[![Hackathon](https://img.shields.io/badge/Hackathon-Band_of_Agents-orange)](https://lablab.ai/ai-hackathons/band-of-agents-hackathon)

## 🎯 Overview

**Band Agents** is a multi-agent AI system where four specialized AI agents collaborate to autonomously build software projects:

```
User Input → 🏗️ Architect → 💻 Developer → 🔍 Reviewer → 🧪 QATest → Complete Project
```

Each agent is registered on the **Band platform** and communicates through Band's chat rooms, simulating a real software development team where AI agents have different roles and responsibilities.

## 🤖 Agent Team

| Agent | Band Handle | Role |
|-------|-------------|------|
| 🏗️ **Architect** | `@huimingchen081/architect` | Analyzes requirements, designs system architecture, recommends tech stack |
| 💻 **Developer** | `@huimingchen081/developer` | Writes production code based on architecture specifications |
| 🔍 **Reviewer** | `@huimingchen081/reviewer` | Reviews code for quality, security, performance, and best practices |
| 🧪 **QATest** | `@huimingchen081/qatest` | Generates test suites, edge cases, and CI/CD integration |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Band Platform                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │Architect │  │Developer │  │ Reviewer │  │  QATest  │  │
│  │  Agent   │→ │  Agent   │→ │  Agent   │→ │  Agent   │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│       ↑              ↑              ↑              ↑       │
│       └──────────────┴──────────────┴──────────────┘       │
│                     Band SDK (WebSocket)                    │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                     Flask Orchestrator                       │
│         Pipeline Manager + REST API + Web UI                 │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                     DashScope LLM (Qwen 3.7 Plus)            │
│                  via OpenAI-compatible API                   │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- DashScope API Key (Alibaba Cloud)
- Band Platform account (app.band.ai) with 4 registered agents

### Installation

```bash
# Clone
git clone https://github.com/huimingchen081/band-agents.git
cd band-agents

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Run the Demo

```bash
# Start the web server + orchestrator
python server.py

# Open browser → http://localhost:3000
```

The web UI connects to the Flask server, which orchestrates the multi-agent pipeline using DashScope LLM. Each agent's output is displayed in real-time.

### Run Band Agents (requires band-sdk)

```bash
# Start all 4 agents (each connects to Band platform)
python start_agents.py
```

Each agent connects to Band via WebSocket and listens for @mentions in chat rooms.

## 🔧 Project Structure

```
band-agents/
├── agents/                    # Band agent scripts
│   ├── architect_band.py      # Architect agent (Band SDK)
│   ├── developer_band.py      # Developer agent (Band SDK)
│   ├── reviewer_band.py       # Reviewer agent (Band SDK)
│   └── qatest_band.py         # QATest agent (Band SDK)
├── core/                      # Core engine
│   ├── llm.py                 # DashScope LLM wrapper
│   └── pipeline.py            # Multi-agent pipeline orchestrator
├── web/                       # Demo web UI
│   └── index.html             # Interactive demo interface
├── server.py                  # Flask web server + API
├── start_agents.py            # Launch all 4 Band agents
├── requirements.txt           # Python dependencies
├── config.yaml                # Band agent configuration
├── .env                       # API keys and environment
└── README.md                  # This file
```

## 🔌 Band SDK Integration

Each agent connects to Band using the official Python SDK:

```python
from thenvoi import Agent
from thenvoi.adapters import LangGraphAdapter
from langchain_openai import ChatOpenAI

# Use DashScope compatible endpoint
llm = ChatOpenAI(
    model="qwen3.7-plus",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key="your-dashscope-key",
)

adapter = LangGraphAdapter(llm=llm, checkpointer=InMemorySaver())
agent = Agent.create(adapter=adapter, agent_id="uuid", api_key="key")
await agent.run()  # Connect and listen
```

## 📊 Demo Results

**Test Project:** URL Shortener Service (Express.js + TypeScript + SQLite)

| Agent | Output | Status |
|-------|--------|--------|
| 🏗️ Architect | 7,695 chars | ✅ System design & API specification |
| 💻 Developer | 12,724 chars | ✅ Production-ready Express.js code |
| 🔍 Reviewer | 10,860 chars | ✅ Multi-dimension review (7/10) |
| 🧪 QATest | 15,610 chars | ✅ 33 test cases generated |
| **Pipeline** | **476.6s** | **All 4 agents completed** |

### Reviewer Improvements (v2)
- Multi-dimensional scoring (Code Quality, Security, Performance, Architecture)
- "What's Working Well" section with specific praise
- Actionable fixes with code snippets
- More balanced and constructive tone
- Baseline score raised from 4/10 to 7/10 for complete working code

### 🎬 Demo Video
[![Demo Video](https://img.youtube.com/vi/VIDEO_ID/0.jpg)](https://youtube.com/watch?v=VIDEO_ID)
> Screen recording: **demo_video_final.mp4** (35s, 1.4MB)

## 🎨 Demo UI Features

- Real-time agent progress visualization with SSE streaming
- Tabbed output display (Architecture / Code / Review / Tests)
- Pipeline progress indicators
- Example project templates
- Statistics dashboard
- Self-playing demo replay: `demo_replay.html`

## 🏆 Hackathon Submission

- **Platform**: lablab.ai Band of Agents Hackathon (June 12-19, 2026)
- **Category**: Multi-Agent Software Development
- **Submitted**: June 12, 2026
- **Team**: Individual (Huiming Chen / @huimingchen081)
- **GitHub**: [github.com/huimingchen081-beep/band-agents](https://github.com/huimingchen081-beep/band-agents)
- **Demo Video**: Included in repo (`demo_video_final.mp4`)

## 📄 License

MIT License — see [LICENSE](LICENSE) file.
