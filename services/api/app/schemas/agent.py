from typing import Optional
from pydantic import BaseModel


class ToolCallSummary(BaseModel):
    tool: str
    sql_summary: str
    row_count: int
    latency_ms: int
    status: str = "success"


class AgentQueryRequest(BaseModel):
    project_id: str
    scene_id: str
    message: str


class AgentQueryResponse(BaseModel):
    answer: str
    tool_calls: list[ToolCallSummary]

