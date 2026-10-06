import time
from __future__ import annotations
from typing import Callable

from ..core.schema import Event, RiskTier
from ..core.bus import EventBus
from .base import BaseAdapter
from ..core.store import TrajectoryStore

# RawAdapter for a raw agent implemented without any frameworks :
class RawAgentAdapter(BaseAdapter):

    # factory method
    def create(cls, agent_id: str, trajectory_id: str, store: TrajectoryStore) -> RawAgentAdapter:
        bus = EventBus(trajectory_id=trajectory_id)

        def persist(event: Event) -> None:
            store.append_event(trajectory_id, event)

        # whenever llm or tool call happens call persist() to store it :
        bus.subscribe(persist, event_type="llm_call")
        bus.subscribe(persist, event_type="tool_call")

        return cls(agent_id=agent_id, bus=bus)

    def call_llm(self, llm_fn: Callable[[str],str], prompt: str, cost: float = 0.0) -> str:

        start = time.perf_counter()
        output = llm_fn(prompt)

        latency_ms = int(time.perf_counter() - start)*1000

        self.record_llm_call(prompt=prompt, output=output, cost=cost, latnecy_ms=latency_ms)

        return output