import { Flex, Text, Grid, GridItem, Button } from "@chakra-ui/react";
import { Slider } from "@components/ui/slider";
import { useState } from "react";

interface ControlsProps {
  numAgents: number;
  setNumAgents: (numAgents: number) => void;
  numObstacles: number;
  setNumObstacles: (numObstacles: number) => void;
  agentSpeed: number;
  setAgentSpeed: (agentSpeed: number) => void;
  setSimStarted: (simStarted: boolean) => void;
}

const PropSlider = ({
  title,
  value,
  setValue,
  min,
  max,
}: {
  title: string;
  value: number;
  setValue: (value: number) => void;
  min: number;
  max: number;
}) => {
  const [valDisplay, setValDisplay] = useState(value);
  return (
    <Flex direction="column" align="start" justify="space-between" gap={0}>
      <Text>{title}</Text>
      <Flex direction="row" align="center" justify="space-between" gap={3}>
        <Slider
          width="200px"
          min={min}
          max={max}
          variant="solid"
          size="sm"
          defaultValue={[value]}
          onValueChange={(e) => {
            setValDisplay(e.value[0]);
          }}
          onValueChangeEnd={(e) => {
            setValue(e.value[0]);
          }}
        />
        <Text>{valDisplay}</Text>
      </Flex>
    </Flex>
  );
};

const Buttons = ({
  setSimStarted,
}: {
  setSimStarted: (simStarted: boolean) => void;
}) => {
  return (
    <Flex direction="row" align="center" justify="space-between" gap={1}>
      <Button onClick={() => setSimStarted(true)}>Start</Button>
      <Button onClick={() => setSimStarted(false)}>Stop</Button>
      <Button onClick={() => setSimStarted(false)}>Reset</Button>
    </Flex>
  );
};

const Controls = ({
  numAgents,
  setNumAgents,
  numObstacles,
  setNumObstacles,
  agentSpeed,
  setAgentSpeed,
  setSimStarted,
}: ControlsProps) => {
  return (
    <Grid
      templateColumns="repeat(2, 1fr)"
      templateRows="repeat(2, 1fr)"
      width="100%"
      alignItems="center"
      justifyItems="between"
      gap={2}
    >
      <GridItem>
        <PropSlider
          title="Number of Agents"
          value={numAgents}
          setValue={setNumAgents}
          min={1}
          max={20}
        />
      </GridItem>
      <GridItem>
        <PropSlider
          title="Number of Obstacles"
          value={numObstacles}
          setValue={setNumObstacles}
          min={1}
          max={3}
        />
      </GridItem>
      <GridItem>
        <PropSlider
          title="Agent Speed"
          value={agentSpeed}
          setValue={setAgentSpeed}
          min={1}
          max={100}
        />
      </GridItem>
      <GridItem>
        <Buttons setSimStarted={setSimStarted} />
      </GridItem>
    </Grid>
  );
};

export default Controls;
