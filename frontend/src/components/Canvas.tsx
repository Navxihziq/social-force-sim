import { Stage, Layer, Rect, Circle } from "react-konva";
import { SimulationState, Agent } from "../hooks/useSimulation";

const hashCode = (str: string): number => {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = (hash << 5) - hash + str.charCodeAt(i);
    hash = hash & hash; // Convert to 32-bit integer
  }
  return Math.abs(hash * 11117);
};

const Canvas = ({
  simulationState,
  pathImage,
  showPath,
}: {
  simulationState: SimulationState;
  pathImage: string[];
  showPath: boolean;
}) => {
  return (
    <Stage width={500} height={400}>
      <Layer>
        {showPath &&
          pathImage.map((color, index) => (
            <Rect
              key={index}
              x={(index % 50) * 10}
              y={Math.floor(index / 50) * 10}
              width={10}
              height={10}
              fill={color}
              opacity={0.5}
            />
          ))}
      </Layer>
      <Layer>
        <Rect x={490} y={150} width={10} height={100} fill="green" />
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
        {simulationState.agents.map((agent: Agent) =>
          agent.exited ? null : (
            <Circle
              key={agent.id}
              x={agent.position.x}
              y={agent.position.y}
              radius={5}
              fill={`hsl(${hashCode(agent.id) % 360}, 70%, 50%)`}
              stroke="black"
              strokeWidth={1}
              opacity={0.8}
            />
          )
        )}
      </Layer>
    </Stage>
  );
};

export default Canvas;
