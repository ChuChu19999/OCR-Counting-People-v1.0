import React from "react";
import styled from "styled-components";

const Container = styled.div`
  display: flex;
  gap: 15px;
  justify-content: center;
  margin: 20px 0;
`;

const Button = styled.button`
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  background-color: ${(props) =>
    props.isStoppingInProgress ? "#ccc" : "#007bff"};
  color: white;
  font-size: 16px;
  cursor: ${(props) =>
    props.disabled || props.isStoppingInProgress ? "not-allowed" : "pointer"};
  transition: background-color 0.3s ease;

  &:hover:not(:disabled):not([data-stopping="true"]) {
    background-color: #0056b3;
  }

  &:disabled {
    background-color: #ccc;
    cursor: not-allowed;
  }
`;

const Controls = ({
  onStart,
  onStartCounting,
  onStop,
  isRunning,
  isCountingStarted,
  isStoppingInProgress,
}) => {
  return (
    <Container>
      <Button onClick={onStart} disabled={isRunning}>
        Начать настройку
      </Button>
      <Button
        onClick={onStartCounting}
        disabled={!isRunning || isCountingStarted}
      >
        Начать подсчет
      </Button>
      <Button
        onClick={onStop}
        disabled={!isRunning}
        isStoppingInProgress={isStoppingInProgress}
        data-stopping={isStoppingInProgress}
      >
        {isStoppingInProgress ? "Останавливается..." : "Остановить"}
      </Button>
    </Container>
  );
};

export default Controls;
