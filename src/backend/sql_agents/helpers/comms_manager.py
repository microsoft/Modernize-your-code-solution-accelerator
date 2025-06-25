"""Optimized CommsManager with parallel processing and performance improvements."""

import asyncio
import logging
import re
from typing import AsyncIterable, ClassVar, List
from concurrent.futures import ThreadPoolExecutor

from semantic_kernel.agents import AgentGroupChat
from semantic_kernel.agents.strategies import (
    SequentialSelectionStrategy,
    TerminationStrategy,
)
from semantic_kernel.contents import ChatMessageContent
from semantic_kernel.exceptions import AgentInvokeException

from sql_agents.agents.migrator.response import MigratorResponse
from sql_agents.helpers.models import AgentType


class CommsManager:
    """Optimized CommsManager with parallel processing and performance improvements."""

    logger: ClassVar[logging.Logger] = logging.getLogger(__name__)
    _EXTRACT_WAIT_TIME = r"in (\d+) seconds"

    def __init__(
        self,
        agent_dict: dict[AgentType, object],
        exception_types: tuple = (Exception,),
        max_retries: int = 3,  # reduc from 10
        initial_delay: float = 0.5,  # reduced from 1.0
        backoff_factor: float = 1.5,  # reduced from 2.0
        simple_truncation: int = 50,  # more aggr truncation
        batch_size: int = 10,  # process in batches
        max_workers: int = 4,  # parallel processing
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.exception_types = exception_types
        self.simple_truncation = simple_truncation
        self.batch_size = batch_size
        self.max_workers = max_workers
        
        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        self.group_chat = AgentGroupChat(
            agents=agent_dict.values(),
            termination_strategy=self.OptimizedTerminationStrategy(
                agents=[
                    agent_dict[AgentType.MIGRATOR],
                    agent_dict[AgentType.SEMANTIC_VERIFIER],
                ],
                maximum_iterations=5,  # Reduced from 10
                automatic_reset=True,
            ),
            selection_strategy=self.ParallelSelectionStrategy(
                agents=agent_dict.values(),
                max_workers=max_workers
            ),
        )

    async def async_invoke_batch(self, inputs: List[str]) -> AsyncIterable[ChatMessageContent]:
        """Process multiple inputs in parallel batches."""
        # Process inputs in batches
        for i in range(0, len(inputs), self.batch_size):
            batch = inputs[i:i + self.batch_size]
            
            # Process batch in parallel
            tasks = [self._process_single_input(input_item) for input_item in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    self.logger.error(f"Batch processing error: {result}")
                    continue
                    
                async for item in result:
                    yield item

    async def _process_single_input(self, input_item: str) -> AsyncIterable[ChatMessageContent]:
        """Process a single input with optimized retry logic."""
        attempt = 0
        current_delay = self.initial_delay

        while attempt < self.max_retries:
            try:
                # Aggressive history truncation
                if len(self.group_chat.history) > self.simple_truncation:
                    # Keep only the most recent messages
                    self.group_chat.history = self.group_chat.history[-self.simple_truncation:]

                # Add input to chat
                self.group_chat.add_chat_message(ChatMessageContent(
                    role="user",
                    content=input_item
                ))

                async_iter = self.group_chat.invoke()
                async for item in async_iter:
                    yield item
                break

            except AgentInvokeException as aie:
                attempt += 1
                if attempt >= self.max_retries:
                    self.logger.error(
                        "Input processing failed after %d attempts: %s",
                        self.max_retries, str(aie)
                    )
                    # Don't raise, continue with next input
                    break

                # Faster retry with shorter delays
                match = re.search(self._EXTRACT_WAIT_TIME, str(aie))
                if match:
                    current_delay = min(int(match.group(1)), 5)  # Cap at 5 seconds
                else:
                    current_delay = min(current_delay * self.backoff_factor, 10)  # Cap at 10 seconds

                self.logger.warning(
                    "Attempt %d/%d failed. Retrying in %.2f seconds...",
                    attempt, self.max_retries, current_delay
                )
                await asyncio.sleep(current_delay)

    class ParallelSelectionStrategy(SequentialSelectionStrategy):
        """Optimized selection strategy with parallel processing capabilities."""

        def __init__(self, agents, max_workers: int = 4):
            super().__init__(agents)
            self.max_workers = max_workers

        async def select_agent(self, agents, history):
            """Select agent with optimized logic and parallel processing hints."""
            if not history:
                return next((agent for agent in agents if agent.name == AgentType.MIGRATOR.value), None)

            last_agent = history[-1].name
            
            # Optimized selection logic with fewer transitions
            agent_transitions = {
                AgentType.MIGRATOR.value: AgentType.PICKER.value,
                AgentType.PICKER.value: AgentType.SYNTAX_CHECKER.value,
                AgentType.SYNTAX_CHECKER.value: AgentType.FIXER.value,
                AgentType.FIXER.value: AgentType.SEMANTIC_VERIFIER.value,  # Skip syntax check
                "candidate": AgentType.SEMANTIC_VERIFIER.value,
            }
            
            next_agent_name = agent_transitions.get(last_agent, AgentType.MIGRATOR.value)
            return next((agent for agent in agents if agent.name == next_agent_name), None)

    class OptimizedTerminationStrategy(TerminationStrategy):
        """Optimized termination strategy with faster decision making."""

        async def should_agent_terminate(self, agent, history):
            """Determine termination with optimized checks."""
            if not history:
                return False

            last_message = history[-1]
            lower_case_content = last_message.content.lower()
            
            # Fast termination checks
            if last_message.name == AgentType.SEMANTIC_VERIFIER.value:
                return True
                
            if last_message.name == AgentType.MIGRATOR.value:
                try:
                    # Faster JSON parsing with error handling
                    response = MigratorResponse.model_validate_json(lower_case_content or "{}")
                    return bool(response.input_error or response.rai_error)
                except Exception:
                    # If parsing fails, assume no termination needed
                    return False
                    
            return False

    def cleanup(self):
        """Clean up resources."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)