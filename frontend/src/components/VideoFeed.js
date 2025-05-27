import React from "react";
import styled from "styled-components";
import { API_BASE_URL, ENDPOINTS } from "../constants";

const VideoContainer = styled.div`
  width: 100%;
  max-width: 800px;
  margin: 20px auto;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
`;

const Video = styled.img`
  width: 100%;
  height: auto;
  display: block;
`;

const VideoFeed = ({ isRunning, onError }) => {
  return (
    <VideoContainer>
      <Video
        src={isRunning ? `${API_BASE_URL}${ENDPOINTS.VIDEO_FEED}` : ""}
        alt="Видео с камеры"
        onError={onError}
      />
    </VideoContainer>
  );
};

export default VideoFeed;
