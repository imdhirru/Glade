"""Specialized agents for Glade AI workflow system."""

import json
import logging
from typing import Any, Dict, Optional
from agents.base import Agent, AgentContext, AgentResult, ToolRegistry

logger = logging.getLogger(__name__)


class PlannerAgent(Agent):
    """Converts complex goals into structured workflows with stages and micro-wins."""

    def __init__(self, tool_registry: Optional[ToolRegistry] = None, gemini_client=None):
        super().__init__(
            name="PlannerAgent",
            description="Converts goals into executable workflows",
            tool_registry=tool_registry
        )
        self.gemini_client = gemini_client

    async def execute(
        self,
        context: AgentContext,
        prompt: str
    ) -> AgentResult:
        """Analyze goal and create structured workflow."""
        try:
            self.log_execution("Starting goal analysis", {"goal": prompt})

            if not self.gemini_client:
                return self.create_result(
                    success=False,
                    error="Gemini client not configured"
                )

            # Get Gemini response
            response = await self._analyze_with_gemini(prompt)

            # Validate and parse response
            workflow_data = self._parse_workflow_response(response)

            self.log_execution(
                "Goal analysis complete",
                {
                    "stages": len(workflow_data.get("stages", [])),
                    "total_micro_wins": sum(
                        len(s.get("micro_wins", []))
                        for s in workflow_data.get("stages", [])
                    )
                }
            )

            return self.create_result(
                success=True,
                data=workflow_data,
                reasoning="Analyzed goal and created structured workflow",
                next_agent="ExecutionAgent"
            )

        except Exception as e:
            self.logger.error(f"Error in goal analysis: {str(e)}")
            return self.create_result(
                success=False,
                error=f"Failed to analyze goal: {str(e)}"
            )

    async def _analyze_with_gemini(self, goal: str) -> str:
        """Call Gemini API for goal analysis."""
        prompt = f"""You are a sophisticated AI productivity system called Glade.

Your task is to analyze a user's goal and return ONLY a valid JSON response.

USER GOAL: "{goal}"

Analyze the goal and return JSON with:
1. interpreted_goal - What the user really wants
2. category - business/learning/personal/technical/other
3. complexity - low/medium/high
4. expected_outcome - What success looks like
5. required_resources - List of resources needed
6. constraints - List of limitations
7. dependencies - List of prerequisites
8. missing_information - What you need to know
9. execution_strategy - How to approach it

Create 4-6 stages with 2-4 micro-wins each.

Each micro-win must be completable in 5-10 minutes with:
- title: Clear action title
- description: What they'll accomplish
- estimated_time: 5-10 (minutes)
- difficulty: easy/medium/hard
- ai_guidance: Helpful hints
- dependencies: Array of dependent micro-win titles

Return ONLY valid JSON, no markdown, no explanations:

{{
  "interpreted_goal": "...",
  "category": "...",
  "complexity": "...",
  "expected_outcome": "...",
  "required_resources": [...],
  "constraints": [...],
  "dependencies": [...],
  "missing_information": [...],
  "execution_strategy": "...",
  "stages": [
    {{
      "name": "Stage Name",
      "description": "...",
      "order": 1,
      "micro_wins": [
        {{
          "title": "...",
          "description": "...",
          "estimated_time": 5,
          "difficulty": "easy",
          "ai_guidance": "...",
          "dependencies": []
        }}
      ]
    }}
  ],
  "success_metrics": [
    {{
      "metric": "...",
      "target": "..."
    }}
  ]
}}"""

        response = self.gemini_client.generate_content(prompt)
        return response.text

    def _parse_workflow_response(self, response: str) -> Dict[str, Any]:
        """Parse and validate Gemini JSON response."""
        # Clean up response if wrapped in markdown
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]

        try:
            data = json.loads(response)

            # Validate required fields
            required_fields = [
                "interpreted_goal",
                "category",
                "complexity",
                "stages",
                "success_metrics"
            ]

            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")

            return data

        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON from Gemini: {e}")
            raise ValueError("Failed to parse workflow structure")


class ResearchAgent(Agent):
    """Gathers and analyzes information needed for workflows."""

    def __init__(self, tool_registry: Optional[ToolRegistry] = None):
        super().__init__(
            name="ResearchAgent",
            description="Researches and analyzes information",
            tool_registry=tool_registry
        )

    async def execute(
        self,
        context: AgentContext,
        prompt: str
    ) -> AgentResult:
        """Research information for workflow."""
        try:
            self.log_execution("Starting research", {"topic": prompt})

            # For now, mock research
            research_findings = {
                "topic": prompt,
                "findings": [
                    "Key insight 1",
                    "Key insight 2",
                    "Key insight 3"
                ],
                "sources": 5,
                "confidence": "high"
            }

            self.log_execution("Research complete")

            return self.create_result(
                success=True,
                data=research_findings,
                reasoning="Gathered relevant information",
                next_agent="PlannerAgent"
            )

        except Exception as e:
            return self.create_result(success=False, error=str(e))


class ExecutionAgent(Agent):
    """Executes actions through available tools."""

    def __init__(self, tool_registry: Optional[ToolRegistry] = None):
        super().__init__(
            name="ExecutionAgent",
            description="Executes actions through tools",
            tool_registry=tool_registry
        )

    async def execute(
        self,
        context: AgentContext,
        prompt: str
    ) -> AgentResult:
        """Execute an action using available tools."""
        try:
            self.log_execution("Starting action execution", {"action": prompt})

            # Parse action request
            available_tools = self.tool_registry.get_available_tools()

            if not available_tools:
                return self.create_result(
                    success=True,
                    data={"status": "preview", "message": "No connected tools available"},
                    reasoning="Action marked as preview (no API connections)"
                )

            # Execute with first available tool
            # This will be enhanced based on the specific action
            result = {
                "status": "completed",
                "message": f"Action executed successfully"
            }

            self.log_execution("Action execution complete")

            return self.create_result(
                success=True,
                data=result,
                reasoning="Executed action via available tools"
            )

        except Exception as e:
            return self.create_result(success=False, error=str(e))


class GrowthAgent(Agent):
    """Handles business-focused growth and revenue workflows."""

    def __init__(self, tool_registry: Optional[ToolRegistry] = None, gemini_client=None):
        super().__init__(
            name="GrowthAgent",
            description="Creates business growth workflows",
            tool_registry=tool_registry
        )
        self.gemini_client = gemini_client

    async def execute(
        self,
        context: AgentContext,
        prompt: str
    ) -> AgentResult:
        """Create business growth workflow."""
        try:
            self.log_execution("Starting growth workflow", {"goal": prompt})

            # Add business-specific context
            business_context = {
                "focus_areas": [
                    "Customer acquisition",
                    "Conversion optimization",
                    "Revenue growth",
                    "Customer retention",
                    "Market analysis"
                ],
                "metrics": [
                    "conversion_rate",
                    "average_order_value",
                    "customer_lifetime_value",
                    "churn_rate"
                ]
            }

            return self.create_result(
                success=True,
                data=business_context,
                reasoning="Initialized growth mode workflow",
                next_agent="PlannerAgent"
            )

        except Exception as e:
            return self.create_result(success=False, error=str(e))


class ReviewAgent(Agent):
    """Reviews and validates workflow progress."""

    def __init__(self, tool_registry: Optional[ToolRegistry] = None):
        super().__init__(
            name="ReviewAgent",
            description="Validates workflow progress",
            tool_registry=tool_registry
        )

    async def execute(
        self,
        context: AgentContext,
        prompt: str
    ) -> AgentResult:
        """Review workflow progress and status."""
        try:
            self.log_execution("Starting progress review")

            # Analyze progress
            review_data = {
                "workflow_id": context.workflow_id,
                "total_tasks": 15,
                "completed_tasks": context.completed_wins.__len__() if context.completed_wins else 0,
                "progress_percentage": 0,
                "status": "on_track",
                "blockers": [],
                "recommendations": [
                    "Continue with next micro-win",
                    "You're making great progress"
                ]
            }

            if context.completed_wins:
                review_data["progress_percentage"] = (
                    len(context.completed_wins) / review_data["total_tasks"] * 100
                )

            self.log_execution("Progress review complete", review_data)

            return self.create_result(
                success=True,
                data=review_data,
                reasoning="Reviewed workflow progress"
            )

        except Exception as e:
            return self.create_result(success=False, error=str(e))


class VoiceAgent(Agent):
    """Generates voice explanations for workflows."""

    def __init__(self, tool_registry: Optional[ToolRegistry] = None):
        super().__init__(
            name="VoiceAgent",
            description="Generates voice narration for workflows",
            tool_registry=tool_registry
        )

    async def execute(
        self,
        context: AgentContext,
        prompt: str
    ) -> AgentResult:
        """Generate voice explanation for current state."""
        try:
            self.log_execution("Starting voice generation")

            # Generate voice script
            script = f"""I understood your goal as: {context.goal}.

I've divided it into clear stages with small, achievable steps.

Your next action is to start the first micro-win.

Let's break this down together."""

            voice_data = {
                "script": script,
                "duration_estimate": 15,
                "stage": context.current_stage or 1
            }

            self.log_execution("Voice script generated")

            return self.create_result(
                success=True,
                data=voice_data,
                reasoning="Generated voice explanation"
            )

        except Exception as e:
            return self.create_result(success=False, error=str(e))
