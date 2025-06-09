import React from "react";
import { AppBar, Toolbar, Typography, Box } from "@mui/material";
import { PeopleAlt } from "@mui/icons-material";

const Header = () => {
  return (
    <AppBar
      position="sticky"
      sx={{
        backgroundColor: "white",
        boxShadow: "0 2px 4px rgba(0, 0, 0, 0.1)",
        mb: 4,
      }}
    >
      <Toolbar>
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            width: "100%",
            maxWidth: 1200,
            margin: "0 auto",
            py: 1,
          }}
        >
          <PeopleAlt
            sx={{
              fontSize: 40,
              color: "primary.main",
              mr: 2,
            }}
          />
          <Box>
            <Typography
              variant="h5"
              sx={{
                color: "primary.main",
                fontWeight: 600,
                letterSpacing: "0.5px",
              }}
            >
              Система распознавания людей
            </Typography>
            <Typography
              variant="subtitle1"
              sx={{
                color: "text.secondary",
                fontWeight: 400,
              }}
            >
              ООО «Газпром добыча Ямбург»
            </Typography>
          </Box>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;
