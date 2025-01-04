import { Flex } from "@chakra-ui/react";
import Sim from "@components/Sim";
import "@/App.css";

function App() {
  return (
    <Flex
      direction={{ base: "column", md: "row" }}
      align="center"
      justify="center"
      mx="10px"
    >
      <Sim />
    </Flex>
  );
}

export default App;
