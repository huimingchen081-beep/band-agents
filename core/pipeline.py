"""
Agent Pipeline - Core multi-agent workflow orchestrator.
Orchestrates: Architect → Developer → Reviewer → QATest
Each agent is a specialized AI with its own role and system prompt.
"""
import json
import logging
from typing import Dict, Optional, Callable
from dataclasses import dataclass, field
from .llm import llm

logger = logging.getLogger(__name__)


# ─── Agent Role Definitions ──────────────────────────────────────────

ARCHITECT_PROMPT = """You are the ARCHITECT agent in a multi-agent software development team. Your role is to analyze project requirements and produce a comprehensive system architecture design.

## Your Output Format (MUST follow exactly):

### 1. Project Overview
- Brief summary of the project and its core purpose

### 2. System Architecture
- High-level architecture diagram (text-based)
- Component breakdown with clear responsibilities
- Data flow between components

### 3. Technology Stack
- Recommended languages, frameworks, and libraries
- Justification for each choice
- Database/storage recommendations

### 4. API Design
- REST/GraphQL endpoints (if applicable)
- Data models and schemas
- Authentication/authorization strategy

### 5. File Structure
- Recommended project directory layout

### 6. Implementation Roadmap
- Phased development plan
- Key milestones and dependencies

## Rules:
- Be specific and actionable
- Use industry best practices
- Consider scalability, security, and maintainability
- Output ONLY the architecture document, no extra commentary
- Keep it concise but complete - around 800-1200 words
"""

DEVELOPER_PROMPT = """You are the DEVELOPER agent in a multi-agent software development team. You receive an architecture design and produce working, production-quality code.

## Your Output Format:
For each file, use:
```
FILE: path/to/file.ext
```language
// Complete code with proper error handling
```

Then include a ## Build & Run section at the end with setup commands.

## Rules:
- Write COMPLETE, RUNNABLE code - no placeholders
- Include error handling and input validation
- Follow the architecture design precisely
- Be CONCISE - target 100-400 total lines across all files
- Output ONLY code and build instructions, no extra commentary
"""

REVIEWER_PROMPT = """You are the REVIEWER agent in a multi-agent software development team. You review code for quality, security, performance, and best practices. You are a SENIOR ENGINEER who gives balanced, constructive, and actionable feedback.

## Your Philosophy:
1. Recognize good work first — highlight what the developer did well
2. Be specific — every issue must have a concrete fix suggestion with code
3. Be fair — don't penalize for stylistic choices; focus on real problems
4. Be collaborative — your goal is to improve the code, not tear it down
5. Score GENEROUSLY — a complete, working project with good practices should score 7-8; exceptional work scores 9-10

## Your Output Format (MUST follow this structure exactly):

### 1. Overall Assessment
- **Overall Score**: X/10 (be reasonable — complete working code is at least 6)
  - Code Quality: X/10
  - Security: X/10
  - Performance: X/10
  - Architecture Alignment: X/10
- **Summary**: 3-4 sentences covering what the code does well and the main areas for improvement

### 2. What's Working Well ✅
List 3-5 specific things the developer did well. Be genuine and specific — reference actual code patterns, design choices, or implementation details you noticed.

### 3. Code Quality Analysis
- **Strengths**: What design patterns, coding practices, or architectural decisions are solid?
- **Improvements**: Where can the code be cleaner, more maintainable, or more readable?
- **Architecture Adherence**: Does the code follow the architecture design? Where does it deviate?

### 4. Security Review
- **Vulnerabilities Found**: List any actual security issues (injection, auth bypass, exposed secrets, etc.)
- **Security Best Practices**: What security measures are already in place? What's missing?
- **Data Handling**: Any concerns with input validation, output encoding, or sensitive data?

### 5. Performance Review
- **Bottlenecks**: Where might this code slow down under load?
- **Optimizations**: Specific suggestions with code snippets for performance improvements
- **Scalability Notes**: How will this handle growing data/users?

### 6. Specific Issues & Fixes
For each issue, use this exact format:

**Issue #N: [Brief Title]**
- **Severity**: 🔴 Critical / 🟡 Warning / 🔵 Suggestion
- **File**: path/to/file
- **Problem**: What's wrong and why it matters
- **Fix**:
```language
// Show the corrected code
```

### 7. Recommended Improvements
List 2-4 concrete code improvements with before/after snippets. These are NOT bugs — they're enhancements that make the code better.

### 8. Final Verdict
- **Verdict**: ✅ APPROVED / ⚠️ APPROVED WITH SUGGESTIONS / ❌ NEEDS REVISION
- **Reasoning**: 1-2 sentences explaining the verdict
- **Required Actions**: Bullet list of must-fix items before production (empty if APPROVED)

## Rules:
- Be thorough but CONSTRUCTIVE — always provide the fix, not just the problem
- Prioritize actual security and functional issues over style nitpicks
- If the code is complete and functional, the baseline score should be at least 6
- Always include "What's Working Well" — never skip acknowledging good work
- Provide actual code snippets in fixes, not vague suggestions
- Output ONLY the review document, no extra meta-commentary
"""

QATEST_PROMPT = """You are the QA/TEST agent in a multi-agent software development team. You receive code and architecture documents, and produce a comprehensive test suite.

## Your Output Format:

### 1. Test Strategy
- Testing approach (unit, integration, e2e)
- Coverage targets
- Test environment requirements

### 2. Unit Tests
For each test file, output:
```
FILE: path/to/test_file.py
```language
// Complete test code using the appropriate framework
```

### 3. Integration Tests
- Key integration test scenarios
- API endpoint tests (if applicable)
- Database interaction tests

### 4. Edge Cases & Error Scenarios
- Known edge cases to test
- Error handling verification
- Input validation tests

### 5. Test Data
- Sample test data / fixtures
- Mock configurations (if needed)

### 6. CI/CD Integration
- Test runner commands
- Coverage reporting setup

## Rules:
- Write COMPLETE, RUNNABLE tests - no placeholders
- Use standard testing frameworks (pytest, jest, etc.)
- Cover happy path AND error cases
- Include setup/teardown where needed
- Output ONLY the test document
"""


@dataclass
class AgentResult:
    """Result from a single agent execution."""
    agent_name: str
    success: bool
    output: str
    error: Optional[str] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class PipelineResult:
    """Complete pipeline execution result."""
    input: str
    architect: Optional[AgentResult] = None
    developer: Optional[AgentResult] = None
    reviewer: Optional[AgentResult] = None
    qatest: Optional[AgentResult] = None
    total_time: float = 0.0

    def to_dict(self) -> Dict:
        """Convert to dict for JSON serialization."""
        return {
            "input": self.input,
            "architect": self._agent_to_dict(self.architect),
            "developer": self._agent_to_dict(self.developer),
            "reviewer": self._agent_to_dict(self.reviewer),
            "qatest": self._agent_to_dict(self.qatest),
            "total_time": self.total_time,
        }

    def _agent_to_dict(self, r: Optional[AgentResult]) -> Optional[Dict]:
        if r is None:
            return None
        return {
            "agent_name": r.agent_name,
            "success": r.success,
            "output": r.output,
            "error": r.error,
        }


class AgentPipeline:
    """Orchestrates the multi-agent software development pipeline."""

    def __init__(self, on_progress: Optional[Callable] = None):
        """Initialize pipeline with optional progress callback.
        
        Args:
            on_progress: Callback(agent_name, status, output) called after each agent.
        """
        self.on_progress = on_progress
        self.agents = {
            "architect": {
                "name": "Architect",
                "prompt": ARCHITECT_PROMPT,
                "emoji": "🏗️",
                "description": "Analyzing requirements and designing system architecture...",
            },
            "developer": {
                "name": "Developer",
                "prompt": DEVELOPER_PROMPT,
                "emoji": "💻",
                "description": "Writing production code based on architecture...",
            },
            "reviewer": {
                "name": "Reviewer",
                "prompt": REVIEWER_PROMPT,
                "emoji": "🔍",
                "description": "Reviewing code for quality and security...",
            },
            "qatest": {
                "name": "QATest",
                "prompt": QATEST_PROMPT,
                "emoji": "🧪",
                "description": "Generating test cases and validation...",
            },
        }

    def _run_agent(self, agent_key: str, input_text: str) -> AgentResult:
        """Run a single agent with given input."""
        agent_info = self.agents[agent_key]
        logger.info(f"Running {agent_info['name']} agent...")

        try:
            output = llm.chat_with_retry(
                messages=[{"role": "user", "content": input_text}],
                system=agent_info["prompt"],
            )
            result = AgentResult(
                agent_name=agent_info["name"],
                success=True,
                output=output.strip(),
            )
            logger.info(f"{agent_info['name']} completed successfully")
        except Exception as e:
            logger.error(f"{agent_info['name']} failed: {e}")
            result = AgentResult(
                agent_name=agent_info["name"],
                success=False,
                output="",
                error=str(e),
            )

        # Notify progress
        if self.on_progress:
            self.on_progress(agent_key, "completed", result)

        return result

    def run(self, project_description: str) -> PipelineResult:
        """Execute the full multi-agent pipeline.

        Flow: Project Description → Architect → Developer → Reviewer → QATest → Results

        Args:
            project_description: Natural language description of the project.

        Returns:
            PipelineResult with all agent outputs.
        """
        import time
        start_time = time.time()

        logger.info("=" * 60)
        logger.info("Starting Multi-Agent Software Development Pipeline")
        logger.info("=" * 60)

        result = PipelineResult(input=project_description)

        # Stage 1: Architect
        if self.on_progress:
            self.on_progress("architect", "running", None)
        try:
            result.architect = self._run_agent(
                "architect",
                f"## Project Requirements\n\n{project_description}\n\nPlease analyze these requirements and produce a complete system architecture design.",
            )
        except Exception as e:
            logger.error(f"Architect failed: {e}")
            result.architect = AgentResult(agent_name="Architect", success=False, output="", error=str(e))

        # Stage 2: Developer
        if self.on_progress:
            self.on_progress("developer", "running", None)
        try:
            arch_output = result.architect.output if result.architect and result.architect.success else "[Architecture not available due to previous failure]"
            result.developer = self._run_agent(
                "developer",
                f"## Architecture Design\n\n{arch_output}\n\nBased on this architecture, write the complete implementation code for this project.",
            )
        except Exception as e:
            logger.error(f"Developer failed: {e}")
            result.developer = AgentResult(agent_name="Developer", success=False, output="", error=str(e))

        # Stage 3: Reviewer
        if self.on_progress:
            self.on_progress("reviewer", "running", None)
        try:
            arch_output = result.architect.output if result.architect and result.architect.success else "[Architecture not available]"
            dev_output = result.developer.output if result.developer and result.developer.success else "[Code not available due to previous failure]"
            result.reviewer = self._run_agent(
                "reviewer",
                f"## Architecture\n{arch_output[:2000]}\n\n## Code\n{dev_output}\n\nPlease review this code thoroughly.",
            )
        except Exception as e:
            logger.error(f"Reviewer failed: {e}")
            result.reviewer = AgentResult(agent_name="Reviewer", success=False, output="", error=str(e))

        # Stage 4: QATest
        if self.on_progress:
            self.on_progress("qatest", "running", None)
        try:
            arch_output = result.architect.output if result.architect and result.architect.success else "[Architecture not available]"
            dev_output = result.developer.output if result.developer and result.developer.success else "[Code not available]"
            review_output = result.reviewer.output if result.reviewer and result.reviewer.success else "[Review not available]"
            result.qatest = self._run_agent(
                "qatest",
                f"## Architecture\n{arch_output[:2000]}\n\n## Code\n{dev_output}\n\n## Review\n{review_output}\n\nGenerate a complete test suite for this code.",
            )
        except Exception as e:
            logger.error(f"QATest failed: {e}")
            result.qatest = AgentResult(agent_name="QATest", success=False, output="", error=str(e))

        result.total_time = time.time() - start_time
        logger.info(f"Pipeline completed in {result.total_time:.2f}s")
        return result


# Create global pipeline instance
pipeline = AgentPipeline()
