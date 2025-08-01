'use client'

import { useState, useMemo, createContext, useEffect } from 'react'
import { ThemeProvider } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
// import { NextIntlClientProvider } from 'next-intl'
import getTheme from '@/theme'
import { usePathname } from 'next/navigation'

// Create a theme context for toggling between light and dark modes
export const ColorModeContext = createContext({ 
  toggleColorMode: () => {},
  mode: 'light'
});

export default function Providers({ children, messages, locale, excludedPaths }) {
  const [mode, setMode] = useState('light');
  const [mounted, setMounted] = useState(false);
  const pathname = usePathname();
  

  // Load saved theme from localStorage on component mount
  useEffect(() => {
    setMounted(true);
    const savedMode = localStorage.getItem('theme-mode');
    if (savedMode === 'light' || savedMode === 'dark') {
      setMode(savedMode);
    }
  }, []);

  // Theme toggle functionality
  const colorMode = useMemo(
    () => ({
      mode,
      toggleColorMode: () => {
        const newMode = mode === 'light' ? 'dark' : 'light';
        setMode(newMode);
        localStorage.setItem('theme-mode', newMode);
      },
    }),
    [mode]
  );

  // Create the theme based on current mode
  const theme = useMemo(() => getTheme(mode), [mode]);

  // Prevent hydration mismatch
  if (!mounted) {
    return null;
  }

  // If the current path is in the excludedPaths array, don't apply the providers
  if(excludedPaths.includes(pathname)) {
    return children;
  }

  return (
    <ColorModeContext.Provider value={colorMode}>
      <ThemeProvider theme={theme}>
        <CssBaseline /> {/* Provides CSS baseline and theme background */}
        {/* <NextIntlClientProvider messages={messages} locale={locale}> */}
          {children}
        {/* </NextIntlClientProvider> */}
      </ThemeProvider>
    </ColorModeContext.Provider>
  )
}