from __future__ import annotations
from pathlib import Path
from typing import Optional
from .schema import Event , Trajectory

# For managing stored trajectories->
class TrajectoryStore :

    def __init__(self, storage_dir: str = "trajectories") -> None:
        self._dir = Path(storage_dir)
        self._dir.mkdir(parents=True , exist_ok=True)

    def path_for(self, trajectory_id: str) -> Path:
        return self._dir/f"{trajectory_id}.json"

    def save_trajectory(self, trajectory: Trajectory) -> None:
        path = self.path_for(trajectory.trajectory_id)
        path.write_text(trajectory.model_dump_json(indent=2))

    def append_event(self, trajectory_id: str, event: Event)-> None:
        trajectory = self.get_trajectory(trajectory_id)
        if trajectory is None :
            raise f"Cannot append because the trajectory {trajectory_id} does not exist yet."

        # if event already exists then just update it
        for i, cur in enumerate(trajectory.events):
            if cur.event_id == event.event_id:
                trajectory.events[i] = event
                break

        else :
            trajectory.events.append(event)

        self.save_trajectory(trajectory)

    def get_trajectory(self, trajectory_id: str)-> Optional[Trajectory]:
        path = self.path_for(trajectory_id)
        if not path.exists():
            return None

        # Reading JSON back into pydantic 
        trajectory = Trajectory.model_validate_json(path.read_text())
        trajectory.events.sort(key=lambda e: e.sequence)

        return trajectory

    # List all the trajectories with the matching agent_id and final_status
    def list_trajectory(self, agent_id: Optional[str]=None, final_status: Optional[str]=None)->list[str]:
        matching = []
        for path in self._dir.glob("*.json"):

            trajectory = Trajectory.model_validate_json(path.read_text())

            if agent_id is not None and trajectory.agent_id != agent_id:
                continue
            if final_status is not None and trajectory.final_status != final_status:
                continue

            matching.append(trajectory.trajectory_id)

        return matching

    def delete_trajectory(self, trajectory_id:str)-> None:
        path = self.path_for(trajectory_id)
        if path.exists():
            path.unlink()


    