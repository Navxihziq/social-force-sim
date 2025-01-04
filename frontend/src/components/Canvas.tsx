import { Stage, Layer, Rect, Circle } from "react-konva";
import { SimulationState, Agent, Obstacle } from "../hooks/useSimulation";

const Canvas = ({ simulationState }: { simulationState: SimulationState }) => {
  return (
    <Stage width={500} height={400}>
      <Layer>
        <Rect x={490} y={150} width={10} height={100} fill="green" />
        {simulationState.agents.map((agent: Agent) => (
          <Circle
            key={agent.id}
            x={agent.position.x}
            y={agent.position.y}
            radius={5}
            fill="red"
          />
        ))}
        {simulationState.obstacles.map((obstacle, index) => (
          <Rect
            key={index}
            x={obstacle.position.x}
            y={obstacle.position.y}
            width={obstacle.size[0]}
            height={obstacle.size[1]}
            fill="blue"
          />
        ))}
      </Layer>
    </Stage>
  );
};

export default Canvas;
