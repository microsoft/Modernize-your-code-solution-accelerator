"""Manages all agent communication and chat strategies for the SQL agents."""

import asyncio
import copy
import logging
import re
from typing import AsyncIterable, ClassVar

from semantic_kernel.agents import AgentGroupChat  # pylint: disable=E0611
from semantic_kernel.agents.strategies import (
    SequentialSelectionStrategy,
    TerminationStrategy,
)
from semantic_kernel.contents import ChatMessageContent
from semantic_kernel.exceptions import AgentInvokeException

from sql_agents.agents.migrator.response import MigratorResponse
from sql_agents.helpers.models import AgentType


class CommsManager:
    """Manages all agent communication and selection strategies for the SQL agents."""

    # Class level logger
    logger: ClassVar[logging.Logger] = logging.getLogger(__name__)

    # regex to extract the recommended wait time in seconds from response
    _EXTRACT_WAIT_TIME = r"in (\d+) seconds"
    
    # Rate limit error indicators
    _RATE_LIMIT_INDICATORS = [
        "rate limit",
        "too many requests",
        "quota exceeded",
        "throttled",
        "429",
    ]

    group_chat: AgentGroupChat = None

    class SelectionStrategy(SequentialSelectionStrategy):
        """A strategy for determining which agent should take the next turn in the chat."""

        # Select the next agent that should take the next turn in the chat
        async def select_agent(self, agents, history):
            """Check which agent should take the next turn in the chat."""
            match history[-1].name:
                case AgentType.MIGRATOR.value:
                    # The Migrator should go first
                    agent_name = AgentType.PICKER.value
                    return next(
                        (agent for agent in agents if agent.name == agent_name), None
                    )
                # The Incident Manager should go after the User or the Devops Assistant
                case AgentType.PICKER.value:
                    agent_name = AgentType.SYNTAX_CHECKER.value
                    return next(
                        (agent for agent in agents if agent.name == agent_name), None
                    )
                case AgentType.SYNTAX_CHECKER.value:
                    agent_name = AgentType.FIXER.value
                    return next(
                        (agent for agent in agents if agent.name == agent_name),
                        None,
                    )
                case AgentType.FIXER.value:
                    # The Fixer should always go after the Syntax Checker
                    agent_name = AgentType.SYNTAX_CHECKER.value
                    return next(
                        (agent for agent in agents if agent.name == agent_name), None
                    )
                case "candidate":
                    # The candidate message is created in the orchestration loop to pass the
                    # candidate and source sql queries to the Semantic Verifier
                    # It is created when the Syntax Checker returns an empty list of errors
                    agent_name = AgentType.SEMANTIC_VERIFIER.value
                    return next(
                        (agent for agent in agents if agent.name == agent_name),
                        None,
                    )
                case _:
                    # Start run with this one - no history
                    return next(
                        (
                            agent
                            for agent in agents
                            if agent.name == AgentType.MIGRATOR.value
                        ),
                        None,
                    )

    # class for termination strategy
    class ApprovalTerminationStrategy(TerminationStrategy):
        """
        A strategy for determining when an agent should terminate.
        This, combined with the maximum_iterations setting on the group chat, determines
        when the agents are finished processing a file when there are no errors.
        """

        async def should_agent_terminate(self, agent, history):
            """Check if the agent should terminate."""
            # May need to convert to models to get usable content using history[-1].name
            terminate: bool = False
            lower_case_hist: str = history[-1].content.lower()
            match history[-1].name:
                case AgentType.MIGRATOR.value:
                    response = MigratorResponse.model_validate_json(
                        lower_case_hist or ""
                    )
                    if (
                        response.input_error is not None
                        or response.rai_error is not None
                    ):
                        terminate = True
                case AgentType.SEMANTIC_VERIFIER.value:
                    # Always terminate after the Semantic Verifier runs
                    terminate = True
                case _:
                    # If the agent is not the Migrator or Semantic Verifier, don't terminate
                    # Note that the Syntax Checker and Fixer loop are only terminated by correct SQL
                    # or by iterations exceeding the max_iterations setting
                    pass

            return terminate

    def __init__(
        self, 
        agent_dict,
        exception_types: tuple = (Exception,),
        max_retries: int = 10,
        initial_delay: float = 0.5,
        backoff_factor: float = 1.5,
        simple_truncation: int = None,
    ):
        """Initialize the CommsManager and agent_chat with the given agents.
        
        Args:
            agent_dict: Dictionary of agents
            exception_types: Tuple of exception types that should trigger a retry
            max_retries: Maximum number of retry attempts (default: 10)
            initial_delay: Initial delay in seconds before first retry (default: 0.5)
            backoff_factor: Factor by which the delay increases with each retry (default: 1.5)
            simple_truncation: Optional truncation limit for chat history
        """
        # Initialize the group chat (exactly like original)
        self.group_chat = AgentGroupChat(
            agents=agent_dict.values(),
            termination_strategy=self.ApprovalTerminationStrategy(
                agents=[
                    agent_dict[AgentType.MIGRATOR],
                    agent_dict[AgentType.SEMANTIC_VERIFIER],
                ],
                maximum_iterations=10,
                automatic_reset=True,
            ),
            selection_strategy=self.SelectionStrategy(agents=agent_dict.values()),
        )
        
        # Store retry configuration (only used when needed)
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.exception_types = exception_types
        self.simple_truncation = simple_truncation
        
        # Performance optimization flags
        self._rate_limit_ever_detected = False
        self._consecutive_successes = 0
        self._use_fast_path = True

    def _is_rate_limit_error(self, error_message: str) -> bool:
        """Check if the error message indicates a rate limit issue."""
        error_lower = error_message.lower()
        return any(indicator in error_lower for indicator in self._RATE_LIMIT_INDICATORS)

    def _should_use_fast_path(self) -> bool:
        """Determine if we should use the fast path (no retry overhead)."""
        # Use fast path if we've never seen rate limits and have some successful calls
        return (
            not self._rate_limit_ever_detected 
            and self._consecutive_successes >= 3
            and self._use_fast_path
        )

    async def _fast_invoke(self) -> AsyncIterable[ChatMessageContent]:
        """Original invoke method with zero overhead - matches no-retry performance."""
        async for item in self.group_chat.invoke():
            yield item

    async def _safe_invoke_with_retry(self) -> AsyncIterable[ChatMessageContent]:
        """Retry logic with optimized snapshot handling."""
        attempt = 0
        current_delay = self.initial_delay
        
        # Only create snapshot when we actually need to retry
        history_snap = None

        while attempt < self.max_retries:
            try:
                # Apply truncation if configured (only on first attempt or retry)
                if (
                    attempt == 0
                    and self.simple_truncation
                    and len(self.group_chat.history) > self.simple_truncation
                ):
                    # Create snapshot only when truncating
                    if history_snap is None:
                        history_snap = copy.deepcopy(self.group_chat.history)
                    self.group_chat.history = history_snap[-self.simple_truncation:]

                # Get iterator and yield results
                async for item in self.group_chat.invoke():
                    yield item

                # Success - break out of retry loop
                break

            except AgentInvokeException as aie:
                # Create snapshot only when we need to retry
                if history_snap is None:
                    history_snap = copy.deepcopy(self.group_chat.history)
                
                attempt += 1
                if attempt >= self.max_retries:
                    self.logger.error(
                        "Function invoke failed after %d attempts. Final error: %s",
                        self.max_retries,
                        str(aie),
                    )
                    raise

                # Restore history for retry
                self.group_chat.history = history_snap

                # Extract wait time or use default
                wait_time_match = re.search(self._EXTRACT_WAIT_TIME, str(aie))
                if wait_time_match:
                    current_delay = int(wait_time_match.group(1))
                else:
                    current_delay = self.initial_delay

                self.logger.warning(
                    "Attempt %d/%d failed: %s. Retrying in %.2f seconds...",
                    attempt,
                    self.max_retries,
                    str(aie),
                    current_delay,
                )

                await asyncio.sleep(current_delay)
                
                if not wait_time_match:
                    current_delay *= self.backoff_factor

            except self.exception_types as e:
                # Create snapshot only when we need to retry
                if history_snap is None:
                    history_snap = copy.deepcopy(self.group_chat.history)
                
                attempt += 1
                if attempt >= self.max_retries:
                    self.logger.error(
                        "Function invoke failed after %d attempts. Final error: %s",
                        self.max_retries,
                        str(e),
                    )
                    raise

                self.logger.warning(
                    "Attempt %d/%d failed with %s: %s. Retrying in %.2f seconds...",
                    attempt,
                    self.max_retries,
                    type(e).__name__,
                    str(e),
                    current_delay,
                )

                await asyncio.sleep(current_delay)
                current_delay *= self.backoff_factor

    async def async_invoke(self) -> AsyncIterable[ChatMessageContent]:
        """
        Ultra-optimized invoke that achieves original performance when no rate limits are detected.
        
        Performance targets:
        - 200k tokens: 1.2 mins (matches no-retry performance)
        - 30k-50k tokens: 1.8 mins (minimal retry overhead)
        """
        
        # Fast path: Use original performance when safe
        if self._should_use_fast_path():
            try:
                async for item in self._fast_invoke():
                    yield item
                
                # Track success
                self._consecutive_successes += 1
                return
                
            except (AgentInvokeException, *self.exception_types) as e:
                # Check if it's a rate limit error
                if self._is_rate_limit_error(str(e)):
                    self.logger.info("Rate limit detected, switching to safe mode")
                    self._rate_limit_ever_detected = True
                    self._use_fast_path = False
                    # Fall through to retry logic
                else:
                    # Non-rate-limit error, re-raise immediately
                    raise
        
        # Safe path: Use retry logic
        try:
            async for item in self._safe_invoke_with_retry():
                yield item
            
            # Track success (but don't immediately switch back to fast path)
            self._consecutive_successes += 1
            
            # Re-enable fast path after many consecutive successes and no recent rate limits
            if (
                self._consecutive_successes >= 10 
                and self._rate_limit_ever_detected
            ):
                self.logger.info("Re-enabling fast path after sustained success")
                self._use_fast_path = True
                
        except Exception:
            # Reset success counter on any failure
            self._consecutive_successes = 0
            self._use_fast_path = False
            raise

    async def invoke_async(self):
        """Original invoke method - maintained for compatibility."""
        return self.group_chat.invoke()