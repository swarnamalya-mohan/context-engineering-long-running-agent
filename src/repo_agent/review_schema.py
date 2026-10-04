"""Typed boundary for repository review outputs."""
from pydantic import BaseModel, ConfigDict, Field, StrictBool


class Evidence(BaseModel):
    model_config = ConfigDict(extra='forbid')
    claim: str
    source: str
    snippet: str


class ReviewAnalysis(BaseModel):
    model_config = ConfigDict(extra='forbid')
    summary: str
    self_hosted: StrictBool | None
    rest_client: StrictBool | None
    graphql: StrictBool | None = None
    team_collaboration: StrictBool | None
    openapi: StrictBool | None = None
    enterprise_sso: StrictBool | None
    enterprise_sso_paid_only: StrictBool | None
    strengths: list[str]
    risks: list[str]
    evidence: list[Evidence]
    confidence: float = Field(ge=0, le=1)
