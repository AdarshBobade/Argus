import time
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel
from ..core.bus import EventBus
from ..core.schema import Event, LLMCallDetails, ToolCallDetails, Trajectory, RiskTier, FinalStatus

# Represents a tool call before its execution:
class ProposedAction(BaseModel):
    trajectory_id: str
    event_id: str
    sequence: int 
    event_type: str = "proposed action"
    tool_name: str
    tool_args: dict
    risk_tier: RiskTier


class BaseAdapter(BaseModel):
    def __init__(self, agent_id: str, bus: EventBus) -> None:
        self.agent_id = agent_id 
        self.bus = bus
        self.trajectory_id = bus.trajectory_id
        self.trajectory : Optional[Trajectory] = None
        self.sequence = 0

    def next_sequence(self) -> int:
        seq = self.sequence
        self.sequence += 1
        return seq

    def time_ms(self) -> int:
        return int(time.time() * 1000)

    # marks start of the agent run:
    def start_trajectory(self, goal: str)-> Trajectory :
        self.trajectory = Trajectory(
                                        trajectory_id= self.trajectory_id,
                                        agent_id= self.agent_id,
                                        goal= goal,
                                        started_at= self.time_ms(),
                                        final_status="in_progress",
                                    )

        return self.trajectory

    # marks the end of the agent run :
    def end_trajectory(self, final_status: FinalStatus) -> None:

        if self.trajectory is None:
            raise RuntimeError("end_trajectory() called before start_trajectory()")
        
        self.trajectory.ended_at = self.time_ms()
        self.trajectory.final_status = final_status


    def record_llm_call(self, prompt: str, output: str, cost: float, latnecy_ms: int) -> Event:

        event = Event(
                       trajectory_id= self.trajectory_id,
                       event_id= f"{self.trajectory_id}-{self.sequence}" ,
                       sequence= self.next_sequence(),
                       event_type="llm_call",
                       details= LLMCallDetails(prompt= prompt, output= output),
                       timestamp=self.time_ms(),
                       cost=cost,
                       latency_ms=latnecy_ms

                    )
        self.record(event)
        self.bus.publish(event)
        return event

    def record(self, event: Event) -> None:
        if self.trajectory is not None:
            self.trajectory.events.append(event)

    # gets called after llm proposed the tool call , but before execution of the tool:
    def on_action_proposed(self, tool_name: str, tool_args: dict, risk_tier: RiskTier) -> ProposedAction:
        proposed = ProposedAction(
                                    trajectory_id=self.trajectory_id,
                                    event_id=f"{self.trajectory_id}-{self.sequence}-proposed",
                                    sequence= self.sequence,
                                    tool_name=tool_name,
                                    tool_args=tool_args,
                                    risk_tier=risk_tier                       
                                )

        self.bus.publish(proposed)
        return proposed

    # tool has executed
    def record_tool_result(self, tool_name:str, tool_args: dict, tool_output: str, risk_tier: RiskTier, cost: float, latency_ms: int) -> Event:
        tool_event = Event(
                        trajectory_id=self.trajectory_id,
                        event_id=f"{self.trajectory_id}-{self.sequence}",
                        sequnce= self.next_sequence(),
                        event_type="tool_call",
                        details= ToolCallDetails(tool_name=tool_name, tool_args= tool_args, tool_output= tool_output),
                        risk_tier=risk_tier,
                        cost=cost,
                        latency_ms=latency_ms,
                        timestamp=self.time_ms()

                    )
        self.record(tool_event)
        self.bus.publish(tool_event)

        return tool_event

    



