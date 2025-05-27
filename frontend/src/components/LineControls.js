import React from "react";
import styled from "styled-components";

const Container = styled.div`
  margin: 20px 0;
`;

const SliderContainer = styled.div`
  margin: 15px 0;
`;

const Label = styled.label`
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
`;

const Slider = styled.input`
  width: 100%;
  height: 25px;
`;

const LineControls = ({
  position,
  angle,
  onPositionChange,
  onAngleChange,
  disabled,
}) => {
  return (
    <Container>
      <SliderContainer>
        <Label htmlFor="linePosition">Положение линии:</Label>
        <Slider
          type="range"
          id="linePosition"
          min="0"
          max="100"
          value={position}
          onChange={(e) => onPositionChange(e.target.value)}
          disabled={disabled}
        />
      </SliderContainer>
      <SliderContainer>
        <Label htmlFor="lineAngle">Угол поворота (градусы):</Label>
        <Slider
          type="range"
          id="lineAngle"
          min="0"
          max="359"
          value={angle}
          onChange={(e) => onAngleChange(e.target.value)}
          disabled={disabled}
        />
      </SliderContainer>
    </Container>
  );
};

export default LineControls;
