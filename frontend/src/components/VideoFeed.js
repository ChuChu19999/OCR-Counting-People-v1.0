import React from "react";
import { Box } from "@mui/material";
import { API_BASE_URL, ENDPOINTS } from "../constants";

const VideoFeed = ({ isRunning, streamVersion, onError }) => {
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
      {isRunning ? (
        <Box
          component="img"
          key={streamVersion}
          src={`${API_BASE_URL}${ENDPOINTS.VIDEO_FEED}?v=${streamVersion}`}
          alt="Видео с камеры"
          onError={onError}
          sx={{
            maxWidth: "100%",
            maxHeight: "100%",
            objectFit: "contain",
            backgroundColor: "black",
          }}
        />
      ) : null}
    </Box>
  );
};

export default VideoFeed;
