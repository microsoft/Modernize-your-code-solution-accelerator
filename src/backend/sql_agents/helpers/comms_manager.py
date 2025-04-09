"""Manages all agent communication and chat strategies for the SQL agents."""

from semantic_kernel.agents import AgentGroupChat  # pylint: disable=E0611
from semantic_kernel.agents.strategies import (
    SequentialSelectionStrategy,
    TerminationStrategy,
)

from sql_agents.helpers.models import AgentType
from sql_agents.migrator.response import MigratorResponse


class CommsManager:
    """Manages all agent communication and selection strategies for the SQL agents."""

    group_chat: AgentGroupChat = None

    class SelectionStrategy(SequentialSelectionStrategy):
        """A strategy for determining which agent should take the next turn in the chat."""

        # Select the next agent that should take the next turn in the chat
        async def select_agent(self, agents, history):
            """ "Check which agent should take the next turn in the chat."""

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

    def __init__(self, agent_dict):
        """Initialize the CommsManager and agent_chat with the given agents."""
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
