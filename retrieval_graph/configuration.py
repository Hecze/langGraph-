"""Define the configurable parameters for the agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Annotated

import prompts


@dataclass(kw_only=True)
class AgentConfiguration():
    """The configuration for the agent."""

    # models

    model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default="anthropic/anthropic.claude-3-haiku-20240307-v1:0",
        metadata={
            "description": "The language model used for conversation. Should be in the form: provider/model-name."
        },
    )

    # prompts

    router_system_prompt: str = field(
        default=prompts.ROUTER_PROMPT,
        metadata={
            "description": "The system prompt used for classifying user questions to route them to the correct node."
        },
    )

    more_info_system_prompt: str = field(
        default=prompts.ASK_FOR_MORE_INFO_PROMPT,
        metadata={
            "description": "The system prompt used for asking for more information from the user."
        },
    )

    general_system_prompt: str = field(
        default=prompts.GENERAL_PROMPT,
        metadata={
            "description": "The system prompt used for responding to general questions."
        },
    )

    research_plan_system_prompt: str = field(
        default=prompts.RESPOND_TO_SAME_CONTEXT_PROMPT,
        metadata={
            "description": "The system prompt used for generating a research plan based on the user's question."
        },
    )

    generate_queries_system_prompt: str = field(
        default=prompts.RESPOND_TO_SAME_CONTEXT_PROMPT,
        metadata={
            "description": "The system prompt used by the researcher to generate queries based on a step in the research plan."
        },
    )

    response_system_prompt: str = field(
        default=prompts.RESPOND_TO_SAME_CONTEXT_PROMPT,
        metadata={"description": "The system prompt used for generating responses."},
    )
