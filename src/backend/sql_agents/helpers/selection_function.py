"""selection_function.py"""

from semantic_kernel.functions import KernelFunctionFromPrompt


def setup_selection_function(
    name, migrator_name, picker_name, syntax_checker_name, fixer_name
):
    """Setup the selection function."""
    selection_function = KernelFunctionFromPrompt(
        function_name=name,
        prompt=f"""
            Determine which participant takes the next turn in a conversation based on the the most recent participant.
            State only the name of the participant to take the next turn.
            No participant should take more than one turn in a row.

            Choose only from these participants:
            - {migrator_name.value}
            - {picker_name.value}
            - {syntax_checker_name.value}
            - {fixer_name.value}
        
            Follow these instructions to determine the next participant:
            1. After user input, it is always {migrator_name.value}'s turn.
            2. After {migrator_name.value}, it is always {picker_name.value}'s turn.
            3. After {picker_name.value}, it is always {syntax_checker_name.value}'s turn.
            
            The next two steps are repeated until the migration is complete:
            4. After {syntax_checker_name.value}, it is {fixer_name.value}'s turn.
            5. After {fixer_name.value}, it is {syntax_checker_name.value}'s turn.

            History:
            {{{{$history}}}}
            """,
    )

    return selection_function
