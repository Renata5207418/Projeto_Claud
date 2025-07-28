import {
  Drawer as MuiDrawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Box,
  Typography,
  Divider,
  IconButton,
  styled,
  Theme,
  CSSObject,
} from '@mui/material';
import LogoutIcon from '@mui/icons-material/Logout';
import { useAuth } from '../auth/AuthContext';
import { useNavigate } from 'react-router-dom';
import DashboardIcon from '@mui/icons-material/Dashboard';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import FilterAltIcon from '@mui/icons-material/FilterAlt';
import MailIcon from '@mui/icons-material/Mail';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import MenuIcon from '@mui/icons-material/Menu';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import logo from '../static/img/logosc.png'; // Certifique-se que o caminho está correto

const drawerWidth = 240;

const menuItems = [
  { text: 'Cloud Status', icon: <DashboardIcon />, path: '/' },
  { text: 'Downloads', icon: <FileDownloadIcon />, path: '/downloads' },
  { text: 'Triagem', icon: <FilterAltIcon />, path: '/triagem' },
  { text: 'Mensagens', icon: <MailIcon />, path: '/mensagens' },
];

const sidebarColors = {
  background: '#FFFFFF',
  text: '#4B5563',
  textActive: '#1F2937',
  icon: '#6B7280',
  iconActive: '#F1C40F',
  activeIndicator: '#F1C40F',
  hoverBg: '#FEF3C7',
  divider: '#E5E7EB',
};

const openedMixin = (theme: Theme): CSSObject => ({
  width: drawerWidth,
  transition: theme.transitions.create('width', {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.enteringScreen,
  }),
  overflowX: 'hidden',
  backgroundColor: sidebarColors.background,
  borderRight: `1px solid ${sidebarColors.divider}`,
});

const closedMixin = (theme: Theme): CSSObject => ({
  transition: theme.transitions.create('width', {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.leavingScreen,
  }),
  overflowX: 'hidden',
  width: `calc(${theme.spacing(7)} + 1px)`,
  [theme.breakpoints.up('sm')]: {
    width: `calc(${theme.spacing(8)} + 1px)`,
  },
  backgroundColor: sidebarColors.background,
  borderRight: `1px solid ${sidebarColors.divider}`,
});

const Drawer = styled(MuiDrawer, { shouldForwardProp: (prop) => prop !== 'open' })(
  ({ theme, open }) => ({
    width: drawerWidth,
    flexShrink: 0,
    whiteSpace: 'nowrap',
    boxSizing: 'border-box',
    ...(open && {
      ...openedMixin(theme),
      '& .MuiDrawer-paper': openedMixin(theme),
    }),
    ...(!open && {
      ...closedMixin(theme),
      '& .MuiDrawer-paper': closedMixin(theme),
    }),
  }),
);

interface SidebarProps {
  open: boolean;
  handleDrawerOpen: () => void;
  handleDrawerClose: () => void;
  isMobile: boolean;
}

export default function Sidebar({ open, handleDrawerOpen, handleDrawerClose, isMobile }: SidebarProps) {
  const location = useLocation();
  const { logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
  logout();
  navigate('/login');
}

  return (
    <Drawer variant={isMobile ? 'temporary' : 'permanent'} open={open} onClose={handleDrawerClose}>
      {/* CABEÇALHO DA SIDEBAR */}
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          px: 2.5,
          height: '80px',
          boxSizing: 'border-box',
        }}
      >
        {open ? (
          // --- VERSÃO ABERTA ---
          <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                width: '100%',
                gap: 1,
                opacity: open ? 1 : 0,
                transition: 'opacity 0.2s ease-in-out',
              }}
            >
              {/* Agrupa o logo e o título */}
              <Box component={RouterLink} to="/" sx={{ display: 'flex', alignItems: 'center', gap: 1.5, textDecoration: 'none' }}>
                <img src={logo} alt="Logo Cloud Triagem" height="50" />
                <Typography
                  variant="h6"
                  noWrap
                  sx={{
                    color: sidebarColors.textActive,
                    fontFamily: "'Poppins', sans-serif",
                    fontWeight: 600,
                    fontSize: '1rem',
                  }}
                >
                  Triagem Cloud
                </Typography>
              </Box>
              {/* Empurra o botão para a direita */}
              <IconButton onClick={handleDrawerClose} sx={{ color: sidebarColors.icon, marginLeft: 'auto' }}>
                <ChevronLeftIcon />
              </IconButton>
            </Box>
        ) : (
          // --- VERSÃO FECHADA ---
          !isMobile && (
            <IconButton onClick={handleDrawerOpen} sx={{ color: sidebarColors.iconActive }}>
              <MenuIcon />
            </IconButton>
          )
        )}
      </Box>

      <Divider sx={{ borderColor: sidebarColors.divider }} />

      {/* LISTA DE ITENS DO MENU */}
      <List sx={{ mt: 2, px: 2 }}>
        {menuItems.map((item) => {
          const isSelected = location.pathname === item.path;
          return (
            <ListItemButton
              key={item.text}
              component={RouterLink}
              to={item.path}
              selected={isSelected}
              sx={{
                minHeight: 48,
                justifyContent: open ? 'initial' : 'center',
                px: 2.5,
                borderRadius: '12px',
                marginBottom: '8px',
                color: isSelected ? sidebarColors.textActive : sidebarColors.text,
                backgroundColor: isSelected ? sidebarColors.hoverBg : 'transparent',
                borderLeft: `4px solid ${isSelected ? sidebarColors.activeIndicator : 'transparent'}`,
                transition: 'background-color 0.3s, color 0.3s',
                '&:hover': {
                    backgroundColor: sidebarColors.hoverBg,
                    color: sidebarColors.textActive,
                    '& .MuiListItemIcon-root': {
                        color: sidebarColors.iconActive,
                    },
                },
                '&.Mui-selected': {
                  color: sidebarColors.textActive,
                  fontWeight: 'bold',
                  '&:hover': {
                     backgroundColor: sidebarColors.hoverBg,
                  }
                },
              }}
            >
              <ListItemIcon sx={{
                minWidth: 0,
                mr: open ? 3 : 'auto',
                justifyContent: 'center',
                color: isSelected ? sidebarColors.iconActive : sidebarColors.icon,
                transition: 'color 0.3s',
              }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText
                primary={item.text}
                primaryTypographyProps={{
                  fontWeight: isSelected ? 600 : 500,
                  fontSize: '0.9rem',
                  fontFamily: "'Poppins', sans-serif",
                }}
                sx={{
                  opacity: open ? 1 : 0,
                  transition: 'opacity 0.2s ease',
                }}
              />
            </ListItemButton>
          );
        })}
      </List>

      {/* --- botão Logout --- */}
      <Divider sx={{ borderColor: sidebarColors.divider, mt: 1 }} />

      <List sx={{ px: 2, pb: 2 }}>
        <ListItemButton
          onClick={handleLogout}
          sx={{
            minHeight: 48,
            justifyContent: open ? 'initial' : 'center',
            px: 2.5,
            borderRadius: '12px',
            color: sidebarColors.text,
            '&:hover': {
              backgroundColor: sidebarColors.hoverBg,
              color: sidebarColors.textActive,
              '& .MuiListItemIcon-root': { color: sidebarColors.iconActive },
            },
          }}
        >
          <ListItemIcon
            sx={{
              minWidth: 0,
              mr: open ? 3 : 'auto',
              justifyContent: 'center',
              color: sidebarColors.icon,
              transition: 'color 0.3s',
            }}
          >
            <LogoutIcon />
          </ListItemIcon>

          <ListItemText
            primary="Logout"
            primaryTypographyProps={{
              fontWeight: 500,
              fontSize: '0.9rem',
              fontFamily: "'Poppins', sans-serif",
            }}
            sx={{ opacity: open ? 1 : 0, transition: 'opacity 0.2s' }}
          />
        </ListItemButton>
      </List>
    </Drawer>
  );
}