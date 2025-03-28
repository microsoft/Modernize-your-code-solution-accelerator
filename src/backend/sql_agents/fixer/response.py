from pydantic import BaseModel


class FixerResponse(BaseModel):
    """
    Model for the response of the fixer
    """

    thought: str
    fixed_query: str
    summary: str | None
