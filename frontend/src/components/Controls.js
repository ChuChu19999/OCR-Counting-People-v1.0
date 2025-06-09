import React from "react";
import { Stack, Button, CircularProgress } from "@mui/material";
import { PlayArrow, Stop, Settings } from "@mui/icons-material";

const Controls = ({
  onStart,
  onStartCounting,
  onStop,
  isRunning,
  isCountingStarted,
  isStoppingInProgress,
}) => {
  return (
    <Stack spacing={2} direction="column">
      <Button
        variant="contained"
        color="primary"
        startIcon={<Settings />}
        onClick={onStart}
        disabled={isRunning}
      >
        Начать настройку
      </Button>

      <Button
        variant="contained"
        color="secondary"
        startIcon={<PlayArrow />}
        onClick={onStartCounting}
        disabled={!isRunning || isCountingStarted}
      >
        Начать подсчет
      </Button>

      <Button
        variant="contained"
        color="error"
        startIcon={
          isStoppingInProgress ? (
            <CircularProgress size={20} color="inherit" />
          ) : (
            <Stop />
          )
        }
        onClick={onStop}
        disabled={!isRunning || isStoppingInProgress}
        sx={{
          backgroundColor: isStoppingInProgress ? "grey.400" : undefined,
          "&:hover": {
            backgroundColor: isStoppingInProgress ? "grey.400" : undefined,
          },
        }}
      >
        Остановить
      </Button>
    </Stack>
  );
};

export default Controls;
