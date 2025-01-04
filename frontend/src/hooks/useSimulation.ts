import axios from "axios";
import { useState, useEffect, useRef } from "react";

interface Position {
  x: number;
  y: number;
}

interface Agent {
  position: Position;
  id: string;
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

const WS_BASE_URL = "ws://localhost:8000/ws"; // WebSocket URL

export const useSimulation = () => {
  const [simulationState, setSimulationState] = useState<SimulationState>({
    agents: [],
    obstacles: [],
    state: false,
  });
  const wsRef = useRef<WebSocket | null>(null);

  // Initialize WebSocket connection
  useEffect(() => {
    wsRef.current = new WebSocket(WS_BASE_URL);

    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setSimulationState(data);
    };

    return () => {
      wsRef.current?.close();
    };
  }, []);

  const initializeSimulation = (config: SimulationConfig) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
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

  return {
    simulationState,
    initializeSimulation,
    stepSimulation,
  };
};
