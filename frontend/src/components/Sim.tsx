import { Container, Flex } from "@chakra-ui/react";
import Canvas from "@components/Canvas";
import Controls from "@components/Controls";
import { useState, useEffect } from "react";
import { useSimulation } from "../hooks/useSimulation";

const Sim = () => {
  const [numAgents, setNumAgents] = useState(10);
  const [numObstacles, setNumObstacles] = useState(1);
  const [simStarted, setSimStarted] = useState(false);

  const {
    simulationState,
    pathImage,
    initializeSimulation,
    stepSimulation,
    getPath,
  } = useSimulation();

  useEffect(() => {
    initializeSimulation({
      numAgents,
      numObstacles,
      state: true,
    });
  }, [numAgents, numObstacles]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (simStarted && simulationState.state) {
      interval = setInterval(() => {
        stepSimulation();
      }, 0.1);
    }
    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [simStarted]);

  const [showPath, setShowPath] = useState(false);

  useEffect(() => {
    if (showPath) {
      getPath();
    }
  }, [showPath, numAgents, numObstacles]);

  return (
    <Flex direction="column" align="center" justify="between">
      <Container width="100%" padding={0} border="1px solid black">
        <Canvas
          simulationState={simulationState}
          pathImage={pathImage}
          showPath={showPath}
        />
      </Container>
      <Controls
        numAgents={numAgents}
        setNumAgents={setNumAgents}
        numObstacles={numObstacles}
        setNumObstacles={setNumObstacles}
        setSimStarted={setSimStarted}
        showPath={showPath}
        setShowPath={setShowPath}
      />
    </Flex>
  );
};

export default Sim;
