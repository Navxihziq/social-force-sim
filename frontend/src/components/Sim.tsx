import { Container, Flex } from "@chakra-ui/react";
import Canvas from "@components/Canvas";
import Controls from "@components/Controls";
import { useState, useEffect } from "react";
import { useSimulation } from "../hooks/useSimulation";

const Sim = () => {
  const [numAgents, setNumAgents] = useState(10);
  const [numObstacles, setNumObstacles] = useState(1);
  const [agentSpeed, setAgentSpeed] = useState(20);
  const [simStarted, setSimStarted] = useState(false);

  const { simulationState, initializeSimulation, stepSimulation } =
    useSimulation();

  // Initialize simulation when configuration changes
  useEffect(() => {
    initializeSimulation({
      numAgents,
      numObstacles,
      state: simStarted,
    });
  }, [numAgents, numObstacles]);

  useEffect(() => {
    if (simStarted) {
      stepSimulation();
    }
  }, [simStarted]);

  return (
    <Flex direction="column" align="center" justify="between">
      <Container width="100%" padding={0} border="1px solid black">
        <Canvas simulationState={simulationState} />
      </Container>
      <Controls
        numAgents={numAgents}
        setNumAgents={setNumAgents}
        numObstacles={numObstacles}
        setNumObstacles={setNumObstacles}
        agentSpeed={agentSpeed}
        setAgentSpeed={setAgentSpeed}
        setSimStarted={setSimStarted}
      />
    </Flex>
  );
};

export default Sim;
