"""
AI Job Matcher v2.0 — Base Agent Class
Shared functionality for all agents: LLM calling, guardrails, logging.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any

from models import AgentMemory
from guardrails import (
    validate_agent_input, filter_output_pii,
    sign_agent_output, sanitize_text,
)
from llm_engine import call_llm
from config import MODEL_MAP


logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the pipeline.
    Provides shared LLM calling, guardrails, timing, and error handling.
    """

    agent_name: str = "base_agent"
    agent_description: str = "Base agent"

    def __init__(self, model_display_name: str = "SmolLM2 1.7B (Fast & Light)"):
        self.model_id = MODEL_MAP.get(
            model_display_name,
            "HuggingFaceTB/SmolLM2-1.7B-Instruct",
        )
        self.model_display_name = model_display_name
        self._start_time: float = 0.0
        self._end_time: float = 0.0

    @abstractmethod
    def run(self, memory: AgentMemory) -> AgentMemory:
        """
        Execute the agent's task.
        Reads from and writes to the shared AgentMemory.
        Must return the updated memory.
        """
        pass

    def call_model(self, system_prompt: str, user_content: str,
                   max_tokens: int = 2048) -> str:
        """
        Call the LLM with guardrails validation on input and output.
        """
        # Validate input
        is_valid, error = validate_agent_input(self.agent_name, user_content)
        if not is_valid:
            logger.warning(f"[{self.agent_name}] Input validation failed: {error}")
            return f"Input validation failed: {error}"

        # Call LLM
        raw_output = call_llm(
            model_id=self.model_id,
            system_prompt=system_prompt,
            user_content=user_content,
            max_tokens=max_tokens,
        )

        # Filter PII from output
        filtered_output = filter_output_pii(raw_output)

        return filtered_output

    def start_timer(self) -> None:
        """Start timing the agent's execution."""
        self._start_time = time.time()

    def stop_timer(self) -> float:
        """Stop timing and return elapsed seconds."""
        self._end_time = time.time()
        return self._end_time - self._start_time

    @property
    def elapsed_time(self) -> float:
        """Return elapsed time in seconds."""
        if self._end_time > 0:
            return self._end_time - self._start_time
        elif self._start_time > 0:
            return time.time() - self._start_time
        return 0.0

    def safe_execute(self, memory: AgentMemory) -> AgentMemory:
        """
        Execute the agent with error handling, timing, and logging.
        Wraps the `run()` method.
        """
        self.start_timer()
        logger.info(f"[{self.agent_name}] Starting execution...")

        try:
            memory = self.run(memory)
            elapsed = self.stop_timer()
            logger.info(f"[{self.agent_name}] Completed in {elapsed:.1f}s")
            return memory

        except Exception as e:
            elapsed = self.stop_timer()
            error_msg = f"[{self.agent_name}] Failed after {elapsed:.1f}s: {str(e)}"
            logger.error(error_msg)
            memory.add_error(error_msg)
            return memory
