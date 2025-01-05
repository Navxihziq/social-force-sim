"""FastAPI application module for the Social Force Model Simulation."""
import uuid
import logging


logger = logging.getLogger("uvicorn")


from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from models.sim import Simulation
from sim_dao import AgentDTO, ObstacleDTO, SimulationDAO

class SimulationConfig(BaseModel):
    numAgents: int
    numObstacles: int
    state: bool


class SimulationState(BaseModel):
    agents: list[AgentDTO]
    obstacles: list[ObstacleDTO]
    state: bool


app = FastAPI()

# Add this route before mounting static files
@app.get("/")
async def read_root():
    return FileResponse("./dist/index.html")

# Mount static files for assets only, not at root
app.mount("/assets", StaticFiles(directory="./dist/assets"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",
                   "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active WebSocket connections
active_connections: dict[str, WebSocket] = {}


@app.post("/init")
def init(config: SimulationConfig) -> SimulationState:
    """Initialize the simulation."""
    sim = Simulation(config.numAgents, config.numObstacles, config.state)
    sim.initialize()
    return SimulationState(
        agents=[SimulationDAO.map_agent_to_dto(agent) for agent in sim.agents],
        obstacles=[SimulationDAO.map_obstacle_to_dto(obstacle) for obstacle in sim.obstacles],
        state=config.state
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Websocket endpoint for the simulation."""
    await websocket.accept()

    client_id = str(uuid.uuid4())
    active_connections[client_id] = {websocket: websocket}
    try:
        while True:
            message = await websocket.receive_json()
            if message["type"] == "init":
                config = SimulationConfig(**message["data"])
                sim = Simulation(config.numAgents, config.numObstacles, config.state)
                active_connections[client_id]["simulation"] = sim

                state = SimulationState(
                    agents=[SimulationDAO.map_agent_to_dto(agent) 
                            for agent in sim.agents],
                    obstacles=[SimulationDAO.map_obstacle_to_dto(obstacle) 
                               for obstacle in sim.obstacles],
                    state=config.state
                )
                await websocket.send_json(
                    {
                        "type": "simulation_state",
                        "data": state.model_dump()
                    }
                )

            elif message["type"] == "step":
                sim = active_connections.get(client_id, {}).get("simulation")
                if sim is not None:
                    sim.step()
                    state = SimulationState(
                        agents=[SimulationDAO.map_agent_to_dto(agent) 
                                for agent in sim.agents],
                        obstacles=[SimulationDAO.map_obstacle_to_dto(obstacle) 
                                   for obstacle in sim.obstacles],
                        state=sim.state
                    )
                    await websocket.send_json(
                        {
                            "type": "simulation_state",
                            "data": state.model_dump()
                        }
                    )
                    logger.info(f"simulation state: {sim.state}")
                    if not sim.state:
                        await websocket.close()
                else:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": "Simulation not initialized"
                        }
                    )

            elif message["type"] == "get_path":
                sim = active_connections.get(client_id, {}).get("simulation")
                if sim is not None:
                    await websocket.send_json(
                        {
                            "type": "path_image",
                            "data": sim.get_path_image()
                        }
                    )
                else:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": "Simulation not initialized"
                        }
                    )

    except Exception as e:
        print(e)
    finally:
        del active_connections[client_id]