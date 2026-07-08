from pydantic import BaseModel, Field


class OpportunitySignalRead(BaseModel):
    key: str
    label: str
    category: str
    direction: str
    score: int
    summary: str
    evidence: list[str] = Field(default_factory=list)
