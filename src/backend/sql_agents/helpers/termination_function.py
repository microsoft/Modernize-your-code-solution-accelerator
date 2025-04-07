"""Helper function to set up the termination function for the semantic kernel."""

from semantic_kernel.functions import KernelFunctionFromPrompt


def setup_termination_function(name, termination_keyword):
    """Set up the termination function for the semantic kernel."""
    termination_function = KernelFunctionFromPrompt(
        function_name=name,
        prompt=f"""
            Examine the response and determine whether the query migration is complete.
            If so, respond with a single word without explanation: {termination_keyword}.

            INPUT:
            - Your input will be a JSON structure that contains a "syntax_errors" key.

            RULES:
            - If "syntax_errors" is an empty list, migration is complete.
            - If "syntax_errors" is not empty, migration is not complete.

            RESPONSE:
            {{{{$history}}}}
            """,
    )

    return termination_function
