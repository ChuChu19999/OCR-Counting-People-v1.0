import React from "react";
import { Box, Typography, Slider } from "@mui/material";
import { Timeline, RotateRight } from "@mui/icons-material";

const LineControls = ({
  position,
  angle,
  onPositionChange,
  onAngleChange,
  disabled,
}) => {
  return (
    <Box sx={{ width: "100%", px: 3 }}>
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
          <Timeline sx={{ mr: 1, color: "primary.main" }} />
          <Typography variant="h6" color="primary">
            Положение линии
          </Typography>
        </Box>
        <Slider
          value={position}
          onChange={(_, value) => onPositionChange(value)}
          disabled={disabled}
          min={0}
          max={100}
          valueLabelDisplay="auto"
          sx={{
            color: "primary.main",
            "& .MuiSlider-thumb": {
              width: 24,
              height: 24,
            },
            "& .MuiSlider-rail": {
              opacity: 0.5,
            },
          }}
        />
      </Box>

      <Box sx={{ mb: 2 }}>
        <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
          <RotateRight sx={{ mr: 1, color: "primary.main" }} />
          <Typography variant="h6" color="primary">
            Угол поворота (градусы)
          </Typography>
        </Box>
        <Slider
          value={angle}
          onChange={(_, value) => onAngleChange(value)}
          disabled={disabled}
          min={0}
          max={359}
          valueLabelDisplay="auto"
          sx={{
            color: "primary.main",
            "& .MuiSlider-thumb": {
              width: 24,
              height: 24,
            },
            "& .MuiSlider-rail": {
              opacity: 0.5,
            },
          }}
        />
      </Box>
    </Box>
  );
};

export default LineControls;
