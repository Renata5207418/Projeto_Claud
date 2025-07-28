import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Box, useMediaQuery, useTheme } from '@mui/material';
import { useState } from 'react';
import Sidebar from './components/Sidebar';
import DashboardPage from './pages/DashboardPage';
import DownloadsPage from './pages/DownloadsPage';
import TriagemPage from './pages/TriagemPage';
import MensagensPage from './pages/MensagensPage';
import LoginPage from './pages/LoginPage';
import ResetPage from './pages/ResetPage';
import { AuthProvider } from './auth/AuthContext';
import PrivateRoute from './auth/PrivateRoute';

const DRAWER_WIDTH = 240;
const COLLAPSED_WIDTH = 65;

export default function App() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [open, setOpen] = useState(!isMobile);

  return (
    <AuthProvider>
      <BrowserRouter>
        <Box sx={{ backgroundColor: '#f4f6f8', minHeight: '100vh' }}>
          <Box
            component="main"
            sx={{
              flexGrow: 1,
              p: 3,
              transition: 'margin-left .3s',
              marginLeft: isMobile
                ? 0
                : open
                ? `${DRAWER_WIDTH}px`
                : `${COLLAPSED_WIDTH}px`,
            }}
          >
            <Routes>
              {/* Rotas públicas */}
              <Route path="/login" element={<LoginPage />} />
              <Route path="/reset" element={<ResetPage />} />

              {/* Rotas protegidas: sidebar aparece só aqui! */}
              <Route
                path="/"
                element={
                  <PrivateRoute>
                    <>
                      <Sidebar
                        open={open}
                        handleDrawerOpen={() => setOpen(true)}
                        handleDrawerClose={() => setOpen(false)}
                        isMobile={isMobile}
                      />
                      <DashboardPage />
                    </>
                  </PrivateRoute>
                }
              />
              <Route
                path="/downloads"
                element={
                  <PrivateRoute>
                    <>
                      <Sidebar
                        open={open}
                        handleDrawerOpen={() => setOpen(true)}
                        handleDrawerClose={() => setOpen(false)}
                        isMobile={isMobile}
                      />
                      <DownloadsPage />
                    </>
                  </PrivateRoute>
                }
              />
              <Route
                path="/triagem"
                element={
                  <PrivateRoute>
                    <>
                      <Sidebar
                        open={open}
                        handleDrawerOpen={() => setOpen(true)}
                        handleDrawerClose={() => setOpen(false)}
                        isMobile={isMobile}
                      />
                      <TriagemPage />
                    </>
                  </PrivateRoute>
                }
              />
              <Route
                path="/mensagens"
                element={
                  <PrivateRoute>
                    <>
                      <Sidebar
                        open={open}
                        handleDrawerOpen={() => setOpen(true)}
                        handleDrawerClose={() => setOpen(false)}
                        isMobile={isMobile}
                      />
                      <MensagensPage />
                    </>
                  </PrivateRoute>
                }
              />
            </Routes>
          </Box>
        </Box>
      </BrowserRouter>
    </AuthProvider>
  );
}
