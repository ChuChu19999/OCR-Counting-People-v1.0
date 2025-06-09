import React from "react";
import { Box } from "@mui/material";
import { API_BASE_URL, ENDPOINTS } from "../constants";

const VideoFeed = ({ isRunning, onError }) => {
  return (
    <Box
      sx={{
        width: "100%",
        height: "100%",
        position: "relative",
        backgroundColor: "#000",
        borderRadius: 2,
        overflow: "hidden",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <Box
        component="img"
        src={isRunning ? `${API_BASE_URL}${ENDPOINTS.VIDEO_FEED}` : ""}
        alt="Видео с камеры"
        onError={onError}
        sx={{
          maxWidth: "100%",
          maxHeight: "100%",
          objectFit: "contain",
          backgroundColor: "black",
        }}
      />
    </Box>
  );
};

export default VideoFeed;
