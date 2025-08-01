// src/theme.js
import { createTheme } from '@mui/material/styles';
import { green, purple, grey, red } from '@mui/material/colors';


// Create a theme instance with light and dark modes
const getTheme = (mode) => createTheme({
  palette: {
    mode,
    ...(mode === 'light' ? {
        // Light mode
        primary: { 
          main: "#7b003f",
          accent: "#E64164"
        },
        secondary: { 
          main: grey[50] 
        },
        background: { 
          default: "#f5f5f5",
          paper: "#ffffff"
        },
      } : {
        // Dark mode
        primary: { 
          main: '#ffffff',
          accent: green[500]
        },
        secondary: { 
          main: purple[300]
        },
        background: {
          default: "#121212",
          paper: "#121212"
        }
      }
    ),
  }
});

export default getTheme;