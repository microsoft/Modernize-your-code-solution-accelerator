from unittest.mock import MagicMock

import pytest

from semantic_kernel.agents import Agent

from sql_agents.helpers.comms_manager import CommsManager
from sql_agents.helpers.models import AgentType


class DummyAgent:
    def __init__(self, name):
        self.name = name


class DummyHistory:
    def __init__(self, name, content):
        self.name = name
        self.content = content


def mock_agent(name: str) -> Agent:
    agent = MagicMock(spec=Agent)
    agent.name = name
    return agent


@pytest.fixture
def agents():
    return {
        AgentType.MIGRATOR: mock_agent("migrator"),
        AgentType.PICKER: mock_agent("picker"),
        AgentType.SYNTAX_CHECKER: mock_agent("syntax_checker"),
        AgentType.FIXER: mock_agent("fixer"),
        AgentType.SEMANTIC_VERIFIER: mock_agent("semantic_verifier"),
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("last_agent, expected_next_agent", [
    (AgentType.MIGRATOR.value, AgentType.PICKER.value),
    (AgentType.PICKER.value, AgentType.SYNTAX_CHECKER.value),
    (AgentType.SYNTAX_CHECKER.value, AgentType.FIXER.value),
    (AgentType.FIXER.value, AgentType.SYNTAX_CHECKER.value),
    ("candidate", AgentType.SEMANTIC_VERIFIER.value),
    ("unknown", AgentType.MIGRATOR.value),
])
async def test_selection_strategy_select_agent(last_agent, expected_next_agent, agents):
    strategy = CommsManager.SelectionStrategy(agents=agents.values())
    history = [DummyHistory(last_agent, "")]  # dummy history item
    result = await strategy.select_agent(list(agents.values()), history)
    assert result.name == expected_next_agent


@pytest.mark.asyncio
async def test_should_agent_terminate_semantic_verifier(agents):
    strategy = CommsManager.ApprovalTerminationStrategy(
        agents=[agents[AgentType.MIGRATOR], agents[AgentType.SEMANTIC_VERIFIER]],
        maximum_iterations=10,
        automatic_reset=True,
    )
    history = [DummyHistory(AgentType.SEMANTIC_VERIFIER.value, "content")]
    terminate = await strategy.should_agent_terminate(agents[AgentType.SEMANTIC_VERIFIER], history)
    assert terminate is True


@pytest.mark.asyncio
async def test_should_agent_terminate_other_agents(agents):
    strategy = CommsManager.ApprovalTerminationStrategy(
        agents=[agents[AgentType.MIGRATOR], agents[AgentType.SEMANTIC_VERIFIER]],
        maximum_iterations=10,
        automatic_reset=True,
    )
    history = [DummyHistory(AgentType.SYNTAX_CHECKER.value, "content")]
    terminate = await strategy.should_agent_terminate(agents[AgentType.SYNTAX_CHECKER], history)
    assert terminate is False
