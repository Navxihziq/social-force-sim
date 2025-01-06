import { useState, useEffect, useRef } from "react";

interface Position {
  x: number;
  y: number;
}

interface Agent {
  position: Position;
  id: string;
  exited: boolean;
}

interface Obstacle {
  position: Position;
  size: [number, number];
}

interface SimulationState {
  agents: Agent[];
  obstacles: Obstacle[];
  state: boolean;
}

interface SimulationConfig {
  numAgents: number;
  numObstacles: number;
  state: boolean;
}

export type { SimulationState, SimulationConfig, Agent, Obstacle };

const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
const wsHost = window.location.host;

const WS_BASE_URL = `${wsProtocol}//${wsHost}/ws`;

export const useSimulation = () => {
  const [simulationState, setSimulationState] = useState<SimulationState>({
    agents: [],
    obstacles: [],
    state: true,
  });

  const [pathImage, setPathImage] = useState<string[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  // Initialize WebSocket connection
  useEffect(() => {
    wsRef.current = new WebSocket(WS_BASE_URL);

    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "path_image") {
        setPathImage(data.data);
      } else if (data.type === "simulation_state") {
        setSimulationState(data.data);
      }
    };

    return () => {
      wsRef.current?.close();
    };
  }, []);

  const initializeSimulation = (config: SimulationConfig) => {
    // Create new WebSocket if closed or doesn't exist
    if (!wsRef.current || wsRef.current.readyState === WebSocket.CLOSED) {
      wsRef.current = new WebSocket(WS_BASE_URL);

      // Wait for connection to open before sending data
      wsRef.current.onopen = () => {
        wsRef.current?.send(
          JSON.stringify({
            type: "init",
            data: config,
          })
        );
      };

      // Reattach message handler
      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "path_image") {
          setPathImage(data.data);
        } else if (data.type === "simulation_state") {
          setSimulationState(data.data);
        }
      };
    } else if (wsRef.current.readyState === WebSocket.OPEN) {
      // If connection is already open, just send the data
      wsRef.current.send(
        JSON.stringify({
          type: "init",
          data: config,
        })
      );
    }
  };

  const stepSimulation = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: "step",
        })
      );
    }
  };

  const getPath = () => {
    if (simulationState.agents.length === 0) {
      return;
    } else if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: "get_path",
        })
      );
    }
  };

  return {
    simulationState,
    pathImage,
    initializeSimulation,
    stepSimulation,
    getPath,
  };
};
