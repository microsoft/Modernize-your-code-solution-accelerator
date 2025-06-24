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
        
        # Store retry configuration
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.exception_types = exception_types
        self.simple_truncation = simple_truncation
        
        # Adaptive retry state - starts optimistic
        self._rate_limit_detected_recently = False
        self._consecutive_successes = 0
        self._session_has_rate_limits = False

    def _is_rate_limit_error(self, error_message: str) -> bool:
        """Check if the error message indicates a rate limit issue."""
        error_lower = error_message.lower()
        return any(indicator in error_lower for indicator in self._RATE_LIMIT_INDICATORS)

    def _should_use_zero_overhead_path(self) -> bool:
        """
        Determine if we should use zero-overhead path.
        
        Use zero overhead when:
        - No rate limits detected in current session AND
        - We have some successful calls OR this is the first call
        """
        return (
            not self._session_has_rate_limits 
            and (self._consecutive_successes >= 1 or self._consecutive_successes == 0)
        )

    async def _zero_overhead_invoke(self) -> AsyncIterable[ChatMessageContent]:
        """Pure delegation to original group_chat.invoke() - zero overhead."""
        async for item in self.group_chat.invoke():
            yield item

    async def _retry_enabled_invoke(self) -> AsyncIterable[ChatMessageContent]:
        """Invoke with retry logic - only used when rate limits are expected."""
        attempt = 0
        current_delay = self.initial_delay
        
        # Create history snapshot only when we need it
        history_snapshot = None

        while attempt < self.max_retries:
            try:
                # Apply truncation if configured and on first attempt
                if (
                    attempt == 0
                    and self.simple_truncation
                    and len(self.group_chat.history) > self.simple_truncation
                ):
                    if history_snapshot is None:
                        history_snapshot = copy.deepcopy(self.group_chat.history)
                    self.group_chat.history = history_snapshot[-self.simple_truncation:]

                # Execute and yield results
                async for item in self.group_chat.invoke():
                    yield item

                # Success - exit retry loop
                return

            except AgentInvokeException as aie:
                # Create snapshot only when we actually need to retry
                if history_snapshot is None:
                    history_snapshot = copy.deepcopy(self.group_chat.history)
                
                attempt += 1
                if attempt >= self.max_retries:
                    self.logger.error(
                        "AgentInvokeException: Max retries (%d) exceeded. Final error: %s",
                        self.max_retries,
                        str(aie),
                    )
                    raise

                # Restore history from snapshot
                self.group_chat.history = copy.deepcopy(history_snapshot)

                # Check for rate limit specific wait time
                wait_time_match = re.search(self._EXTRACT_WAIT_TIME, str(aie))
                if wait_time_match:
                    current_delay = int(wait_time_match.group(1))
                    self.logger.info(
                        "Rate limit detected, waiting %d seconds as requested",
                        current_delay
                    )
                else:
                    current_delay = self.initial_delay * (self.backoff_factor ** (attempt - 1))

                self.logger.warning(
                    "Attempt %d/%d failed with AgentInvokeException: %s. Retrying in %.2f seconds...",
                    attempt,
                    self.max_retries,
                    str(aie),
                    current_delay,
                )

                await asyncio.sleep(current_delay)

            except self.exception_types as e:
                if history_snapshot is None:
                    history_snapshot = copy.deepcopy(self.group_chat.history)
                
                attempt += 1
                if attempt >= self.max_retries:
                    self.logger.error(
                        "Generic exception: Max retries (%d) exceeded. Final error: %s",
                        self.max_retries,
                        str(e),
                    )
                    raise

                # Restore history from snapshot
                self.group_chat.history = copy.deepcopy(history_snapshot)

                current_delay = self.initial_delay * (self.backoff_factor ** (attempt - 1))
                
                self.logger.warning(
                    "Attempt %d/%d failed with %s: %s. Retrying in %.2f seconds...",
                    attempt,
                    self.max_retries,
                    type(e).__name__,
                    str(e),
                    current_delay,
                )

                await asyncio.sleep(current_delay)

    async def async_invoke(self) -> AsyncIterable[ChatMessageContent]:
        """
        Optimized invoke method that dynamically chooses between zero-overhead and retry modes.
        
        Performance targets:
        - 200k tokens: 1.2 mins (zero overhead when no rate limits expected)
        - 30k-50k tokens: 1.8-2 mins (retry overhead only when needed)
        """
        
        # Decide which path to take
        use_zero_overhead = self._should_use_zero_overhead_path()
        
        if use_zero_overhead:
            # Zero overhead path - matches original performance exactly
            try:
                async for item in self._zero_overhead_invoke():
                    yield item
                
                # Track success
                self._consecutive_successes += 1
                return
                
            except (AgentInvokeException, *self.exception_types) as e:
                # Check if this is a rate limit error
                error_str = str(e)
                if self._is_rate_limit_error(error_str):
                    self.logger.info(
                        "Rate limit detected on zero-overhead path, switching to retry mode for this session"
                    )
                    self._session_has_rate_limits = True
                    self._rate_limit_detected_recently = True
                    # Fall through to retry logic below
                else:
                    # Non-rate-limit error, re-raise immediately (fail fast)
                    self.logger.error("Non-rate-limit error in zero-overhead path: %s", error_str)
                    raise
        
        # Retry-enabled path - used when rate limits are expected or detected
        try:
            async for item in self._retry_enabled_invoke():
                yield item
            
            # Track success
            self._consecutive_successes += 1
            
            # Gradually become more optimistic about rate limits
            if self._consecutive_successes >= 5:
                self._rate_limit_detected_recently = False
                # Note: We keep _session_has_rate_limits = True to remember for this session
                
        except Exception as e:
            # Reset success counter on failure
            self._consecutive_successes = 0
            self._rate_limit_detected_recently = True
            raise

    async def invoke_async(self):
        """Legacy method - maintained for compatibility."""
        return self.group_chat.invoke()

    def reset_rate_limit_state(self):
        """
        Reset rate limit detection state - call this between different processing sessions
        if you want to reset the adaptive behavior.
        """
        self._rate_limit_detected_recently = False
        self._consecutive_successes = 0
        self._session_has_rate_limits = False
        self.logger.info("Rate limit detection state reset")