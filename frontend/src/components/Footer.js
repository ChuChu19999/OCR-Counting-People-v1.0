import React from "react";
import { Box, Typography, Link } from "@mui/material";
import { Email, Phone, LocationOn } from "@mui/icons-material";

const Footer = () => {
  return (
    <Box
      component="footer"
      sx={{
        backgroundColor: "white",
        borderTop: "1px solid",
        borderColor: "rgba(0, 0, 0, 0.1)",
        py: 2,
        mt: "auto",
      }}
    >
      <Box
        sx={{
          maxWidth: 1200,
          margin: "0 auto",
          px: 3,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 2,
        }}
      >
        <Box>
          <Typography variant="body2" color="text.secondary">
            © 2025 ООО «Газпром добыча Ямбург»
          </Typography>
        </Box>

        <Box
          sx={{
            display: "flex",
            gap: 4,
            alignItems: "center",
            flexWrap: "wrap",
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <LocationOn sx={{ fontSize: 20, color: "primary.main" }} />
            <Typography variant="body2" color="text.secondary">
              г. Новый Уренгой
            </Typography>
          </Box>

          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <Phone sx={{ fontSize: 20, color: "primary.main" }} />
            <Link
              href="tel:+73494966003"
              color="text.secondary"
              sx={{
                textDecoration: "none",
                "&:hover": { color: "primary.main" },
              }}
            >
              <Typography variant="body2">+7 (349) 496-60-03</Typography>
            </Link>
          </Box>

          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <Email sx={{ fontSize: 20, color: "primary.main" }} />
            <Link
              href="mailto:yamburg@yamburg.gazprom.ru"
              color="text.secondary"
              sx={{
                textDecoration: "none",
                "&:hover": { color: "primary.main" },
              }}
            >
              <Typography variant="body2">
                yamburg@yamburg.gazprom.ru
              </Typography>
            </Link>
          </Box>
        </Box>
      </Box>
    </Box>
  );
};

export default Footer;
