import React, { useState, useEffect, useCallback } from "react";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import {
  Container,
  Typography,
  Paper,
  Box,
  CssBaseline,
  Grid,
} from "@mui/material";
import VideoFeed from "./components/VideoFeed";
import LineControls from "./components/LineControls";
import Controls from "./components/Controls";
import Header from "./components/Header";
import Footer from "./components/Footer";
import * as api from "./services/api";
import "./styles/theme.css";

const theme = createTheme({
  palette: {
    primary: {
      main: "#1a237e",
    },
    secondary: {
      main: "#0d47a1",
    },
    background: {
      default: "#f5f5f5",
    },
    text: {
      primary: "#1f2937",
      secondary: "#4b5563",
    },
  },
  typography: {
    fontFamily:
      '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji"',
    h1: {
      fontSize: "2.5rem",
      fontWeight: 600,
      letterSpacing: "-0.02em",
      color: "#1a237e",
    },
    h2: {
      fontSize: "2rem",
      fontWeight: 600,
      letterSpacing: "-0.01em",
      color: "#0d47a1",
    },
    h5: {
      fontWeight: 600,
      letterSpacing: "-0.01em",
    },
    h6: {
      fontWeight: 600,
      letterSpacing: "-0.01em",
    },
    subtitle1: {
      fontSize: "1rem",
      fontWeight: 500,
      letterSpacing: "-0.01em",
    },
    body1: {
      fontSize: "1rem",
      letterSpacing: "-0.01em",
    },
    button: {
      fontWeight: 600,
      letterSpacing: "-0.01em",
      textTransform: "none",
    },
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)",
          transition: "all 0.3s ease",
          "&:hover": {
            transform: "translateY(-2px)",
            boxShadow: "0 6px 12px rgba(0, 0, 0, 0.15)",
          },
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: "10px 24px",
          fontSize: "0.9375rem",
        },
      },
    },
    MuiSlider: {
      styleOverrides: {
        root: {
          "& .MuiSlider-thumb": {
            width: 20,
            height: 20,
          },
          "& .MuiSlider-rail": {
            opacity: 0.3,
          },
        },
      },
    },
  },
});

function App() {
  const [isRunning, setIsRunning] = useState(false);
  const [isCountingStarted, setIsCountingStarted] = useState(false);
  const [isStoppingInProgress, setIsStoppingInProgress] = useState(false);
  const [peopleCount, setPeopleCount] = useState(0);
  const [linePosition, setLinePosition] = useState(50);
  const [lineAngle, setLineAngle] = useState(0);
  const [countUpdateInterval, setCountUpdateInterval] = useState(null);
  const [streamVersion, setStreamVersion] = useState(0);

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
      setStreamVersion((v) => v + 1);
      // Сбрасываем локальные состояния к дефолту
      setPeopleCount(0);
      setLinePosition(50);
      setLineAngle(0);
      // Синхронизируем дефолтные настройки линии с бэкендом
      try {
        await api.updateLineSettings(50, 0);
      } catch (e) {
        console.error("Не удалось применить дефолтные настройки линии на бэкенде:", e);
      }
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
        // Инкрементируем версию, чтобы принудительно размонтировать/перемонтировать img
        setStreamVersion((v) => v + 1);
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
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box
        sx={{
          minHeight: "100vh",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <Container
          maxWidth="lg"
          sx={{
            height: "100%",
            display: "flex",
            flexDirection: "column",
          }}
        >
          <Header />
          <Box
            sx={{
              flex: 1,
              display: "flex",
              flexDirection: { xs: "column", md: "row" },
              gap: 1,
              minHeight: 0,
              mt: 0.25,
            }}
          >
            <Box
              sx={{
                flex: 1,
                minHeight: 0,
                display: "flex",
                flexDirection: "column",
              }}
            >
              <Paper
                sx={{
                  flex: 1,
                  display: "flex",
                  flexDirection: "column",
                  overflow: "hidden",
                  p: 1,
                }}
              >
                <VideoFeed
                  isRunning={isRunning}
                  streamVersion={streamVersion}
                  onError={handleVideoError}
                />
              </Paper>
            </Box>
            <Box
              sx={{
                width: { xs: "100%", md: "300px" },
                display: "flex",
                flexDirection: "column",
                gap: 1,
              }}
            >
              {isCountingStarted && (
                <Paper
                  sx={{
                    p: 1.5,
                    backgroundColor: "primary.main",
                    color: "white",
                    textAlign: "center",
                    display: "flex",
                    flexDirection: "column",
                    gap: 0.5,
                  }}
                >
                  <Typography
                    variant="subtitle2"
                    sx={{
                      opacity: 0.9,
                      fontWeight: 500,
                    }}
                  >
                    Людей в помещении
                  </Typography>
                  <Typography
                    variant="h4"
                    sx={{
                      fontWeight: 600,
                      lineHeight: 1,
                    }}
                  >
                    {peopleCount}
                  </Typography>
                </Paper>
              )}
              <Paper sx={{ p: 1.5 }}>
                <LineControls
                  position={linePosition}
                  angle={lineAngle}
                  onPositionChange={handlePositionChange}
                  onAngleChange={handleAngleChange}
                  disabled={!isRunning || isCountingStarted}
                />
              </Paper>
              <Paper sx={{ p: 1.5 }}>
                <Controls
                  onStart={handleStart}
                  onStartCounting={handleStartCounting}
                  onStop={handleStop}
                  isRunning={isRunning}
                  isCountingStarted={isCountingStarted}
                  isStoppingInProgress={isStoppingInProgress}
                />
              </Paper>
            </Box>
          </Box>
          <Box sx={{ mt: 0.5 }}>
            <Footer />
          </Box>
        </Container>
      </Box>
    </ThemeProvider>
  );
}

export default App;
