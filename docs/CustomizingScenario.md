## [Optional]: Customizing scenario

This template pattern can be used for other types of conversions requiring the same or similar agent workflows.  This document provides a suggested path to modifying the template to support a new scenario - for example an infrastructure as code template conversion. Generally the API backend is modified with the API used to support a new user experience / UI. This document will focus on necessary backend changes.

The first step is to determine the overall architecture for the system, how the agents will interact, and details regarding the step by step architecture. If the conversion needs to be validated by a tool or tested in an environment, full details on how to configure and run this are also necessary. After this, follow the steps below to quickly create a proof of concept for the new system.

1. Copy the agent workflow folder (sql_agents) into a new sibling folder within src/backend and name it as appropriate to your scenario
1. Modify the agent folder and file names as appropriate to support new agent types
1. Modify the agent response class to represent the structured response needed from the agent
1. Modify the agents prompting in the associated prompt.txt file. Note that changing the conversion inputs and outputs will also require changes to agent_config.py as well as src/backend/api/api_routes in the definition of start-processing.
1. If workflow modification is necessary, those changes would take place in the src/backend/sql_agents/helper/comms_manager.py file as well as the src/backend/sql_agents/convert_script.py file.
1. There are two primary ways of messaging state changes to the front end.  The first results from state storage in Cosmos. This is updated primarily in the convert_script.py file with the creation of file logs. The second is for transitory state changes that are communicated through websockets to the client. These are also primarily in the convert_script.py file.
1. Create a function to validate conversions using a test environment or utility. Provide this function to an agent to perform the validation role and iterate with another agent which can attempt to fix any issues. You can follow the plug in example within the current Syntax checker agent.

Agent code in src/backend/agents including agent_base.py, agent_factory.py, and agent_config.py is designed to be largely reused in any scenario. Code in sql_agents/helpers is aso designed for reuse.