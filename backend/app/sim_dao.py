from app.models.sim import Agent as SimAgent, Obstacle as SimObstacle
from pydantic import BaseModel


class Position(BaseModel):
    x: int
    y: int

class AgentDTO(BaseModel):
    id: str
    position: Position
    exited: bool

class ObstacleDTO(BaseModel):
    size: tuple[int, int]
    position: Position

class SimulationDAO:
    @staticmethod
    def map_agent_to_dto(agent: SimAgent) -> AgentDTO:
        return AgentDTO(
            id=agent.id,
            position=Position(
                x=int(agent.position[1]),  # Convert from (row, col) to (x, y)
                y=int(agent.position[0])
            ),
            exited=agent.exited
        )

    @staticmethod
    def map_obstacle_to_dto(obstacle: SimObstacle) -> ObstacleDTO:
        return ObstacleDTO(
            size=obstacle.size,
            position=Position(
                x=obstacle.position[0],
                y=obstacle.position[1]
            )
        )