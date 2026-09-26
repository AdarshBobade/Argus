from pydantic import BaseModel , Field
from typing import Literal , Union 

RiskTier = Literal["read_only" , "side_effecting"]
VerdictDecision = Literal["pass", "flag", "halt", "redirect"]


# Payload specific to an llm reasoning call
class LLMCallDetails(BaseModel):
    prompt : str
    output :str

# Payload specific to a Tool invocation
class ToolCallDetails(BaseModel):
    tool_name : str
    tool_args : dict
    tool_output : str


class Verdict(BaseModel):
    decision : VerdictDecision
    confidence : float
    check_name : str

class Event(BaseModel):
    trajectory_id : str
    event_id : str
    sequence : int      # position within the trajectory
    event_type : Literal["llm_call" , "tool_call"] 
    details : Union[LLMCallDetails , ToolCallDetails] # Either or
    risk_tier : RiskTier = "read_only"       # LLM_calls are read_only by default
    timestamp : int
    cost : float
    latency_ms : int
    verdict : Verdict | None = None

class Step(BaseModel):
    step_id : str
    trajectory_id : str
    sequence : int 
    llm_event : Event
    tool_event : Event | None = None

class Trajectory(BaseModel): 
    agent_id : str
    trajectory_id : str
    goal : str
    started_at : int 
    ended_at : int | None = None
    final_status: Literal["completed", "halted", "errored", "in_progress"]
    events : list[Event] = Field(default_factory=list)  # giving an empty list by default
    steps : list[Step] = Field(default_factory=list)

    @property  
    def total_cost(self) -> float:
        return sum(event.cost for event in self.events)

    @property
    def total_latency_ms(self) -> int:
        return sum(event.latency_ms for event in self.events)




