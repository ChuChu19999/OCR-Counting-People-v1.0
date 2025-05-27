import React, { useState, useEffect, useCallback } from "react";
import styled from "styled-components";
import VideoFeed from "./components/VideoFeed";
import LineControls from "./components/LineControls";
import Controls from "./components/Controls";
import * as api from "./services/api";

const Container = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
`;

const Title = styled.h1`
  text-align: center;
  color: #333;
  margin-bottom: 30px;
`;

const Counter = styled.div`
  text-align: center;
  margin: 20px 0;
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

  h2 {
    margin: 0;
    color: #333;
  }

  span {
    color: #007bff;
    font-weight: bold;
    font-size: 1.2em;
  }
`;

function App() {
  const [isRunning, setIsRunning] = useState(false);
  const [isCountingStarted, setIsCountingStarted] = useState(false);
  const [isStoppingInProgress, setIsStoppingInProgress] = useState(false);
  const [peopleCount, setPeopleCount] = useState(0);
  const [linePosition, setLinePosition] = useState(50);
  const [lineAngle, setLineAngle] = useState(0);
  const [countUpdateInterval, setCountUpdateInterval] = useState(null);

  const updateCount = useCallback(async () => {
    try {
      const count = await api.getPeopleCount();
      setPeopleCount(count);
    } catch (error) {
      console.error("Ошибка при обновлении счетчика:", error);
    }
  }, []);

  const handleLineSettingsChange = useCallback(async (position, angle) => {
    try {
      await api.updateLineSettings(position, angle);
    } catch (error) {
      console.error("Ошибка при обновлении настроек линии:", error);
    }
  }, []);

  const handlePositionChange = useCallback(
    (newPosition) => {
      setLinePosition(newPosition);
      handleLineSettingsChange(newPosition, lineAngle);
    },
    [lineAngle, handleLineSettingsChange],
  );

  const handleAngleChange = useCallback(
    (newAngle) => {
      setLineAngle(newAngle);
      handleLineSettingsChange(linePosition, newAngle);
    },
    [linePosition, handleLineSettingsChange],
  );

  const handleStart = async () => {
    try {
      await api.startSystem();
      setIsRunning(true);
    } catch (error) {
      console.error("Ошибка при запуске системы:", error);
    }
  };

  const handleStartCounting = async () => {
    try {
      await api.startCounting();
      setIsCountingStarted(true);
      const interval = setInterval(updateCount, 1000);
      setCountUpdateInterval(interval);
    } catch (error) {
      console.error("Ошибка при запуске подсчета:", error);
    }
  };

  const handleStop = async () => {
    if (isStoppingInProgress) {
      return;
    }

    try {
      setIsStoppingInProgress(true);
      const response = await api.stopSystem();

      if (response.status === 200) {
        setIsRunning(false);
        setIsCountingStarted(false);
        if (countUpdateInterval) {
          clearInterval(countUpdateInterval);
          setCountUpdateInterval(null);
        }
      }
    } catch (error) {
      console.error("Ошибка при остановке системы:", error);
    } finally {
      setIsStoppingInProgress(false);
    }
  };

  const handleVideoError = useCallback(() => {
    console.error("Ошибка при загрузке видеопотока");
    handleStop();
  }, []);

  useEffect(() => {
    return () => {
      if (countUpdateInterval) {
        clearInterval(countUpdateInterval);
      }
    };
  }, [countUpdateInterval]);

  return (
    <Container>
      <Title>Система подсчета людей</Title>
      <VideoFeed isRunning={isRunning} onError={handleVideoError} />
      <LineControls
        position={linePosition}
        angle={lineAngle}
        onPositionChange={handlePositionChange}
        onAngleChange={handleAngleChange}
        disabled={isCountingStarted}
      />
      <Controls
        onStart={handleStart}
        onStartCounting={handleStartCounting}
        onStop={handleStop}
        isRunning={isRunning}
        isCountingStarted={isCountingStarted}
        isStoppingInProgress={isStoppingInProgress}
      />
      <Counter>
        <h2>
          Количество людей в помещении: <span>{peopleCount}</span>
        </h2>
      </Counter>
    </Container>
  );
}

export default App;
