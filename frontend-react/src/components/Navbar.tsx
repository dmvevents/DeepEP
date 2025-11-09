import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Menu,
  MenuItem,
  Avatar,
  Box,
  ListItemIcon,
  Divider,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import AssignmentIcon from '@mui/icons-material/Assignment';
import PersonIcon from '@mui/icons-material/Person';
import LogoutIcon from '@mui/icons-material/Logout';
import HomeIcon from '@mui/icons-material/Home';
import ShieldIcon from '@mui/icons-material/Shield';
import { getInitials } from '../utils/formatters';

interface NavbarProps {
  title?: string;
  showUserMenu?: boolean;
}

const Navbar = ({ title = 'Mortgage Calculator', showUserMenu = true }: NavbarProps) => {
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const menuOpen = Boolean(anchorEl);

  // Get user from localStorage
  const userStr = localStorage.getItem('user');
  const user = userStr ? JSON.parse(userStr) : null;

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    // Clear all authentication and draft data
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    localStorage.removeItem('mortgage_application_draft');
    localStorage.removeItem('mortgage_application_draft_timestamp');

    handleMenuClose();
    navigate('/');
  };

  const handleNavigation = (path: string) => {
    handleMenuClose();
    navigate(path);
  };


  return (
    <AppBar
      position="sticky"
      sx={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
      }}
    >
      <Toolbar>
        {/* Logo / Home Button */}
        <IconButton
          edge="start"
          color="inherit"
          onClick={() => navigate('/')}
          sx={{ mr: 2 }}
        >
          <HomeIcon />
        </IconButton>

        {/* Page Title */}
        <Typography
          variant={isMobile ? 'body1' : 'h6'}
          component="div"
          sx={{
            flexGrow: 1,
            fontWeight: 600,
            display: { xs: 'none', sm: 'block' },
          }}
        >
          {title}
        </Typography>

        {/* Mobile Title (shorter) */}
        <Typography
          variant="body1"
          component="div"
          sx={{
            flexGrow: 1,
            fontWeight: 600,
            display: { xs: 'block', sm: 'none' },
          }}
        >
          {isMobile ? 'Mortgage App' : title}
        </Typography>

        {/* User Menu */}
        {showUserMenu && user && (
          <>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {!isMobile && (
                <Typography variant="body2" sx={{ mr: 1 }}>
                  {user.username || user.email || 'User'}
                </Typography>
              )}
              <IconButton
                onClick={handleMenuOpen}
                sx={{
                  bgcolor: 'rgba(255,255,255,0.2)',
                  '&:hover': {
                    bgcolor: 'rgba(255,255,255,0.3)',
                  },
                }}
              >
                <Avatar
                  sx={{
                    width: 32,
                    height: 32,
                    bgcolor: 'rgba(255,255,255,0.3)',
                    fontSize: '0.875rem',
                    fontWeight: 600,
                  }}
                  src={user.profile_picture}
                >
                  {!user.profile_picture && getInitials(user.username || user.email || 'User')}
                </Avatar>
              </IconButton>
            </Box>

            <Menu
              anchorEl={anchorEl}
              open={menuOpen}
              onClose={handleMenuClose}
              anchorOrigin={{
                vertical: 'bottom',
                horizontal: 'right',
              }}
              transformOrigin={{
                vertical: 'top',
                horizontal: 'right',
              }}
              PaperProps={{
                sx: {
                  mt: 1.5,
                  minWidth: 220,
                  borderRadius: 2,
                  boxShadow: '0 8px 24px rgba(0,0,0,0.12)',
                },
              }}
            >
              {/* User Info Header */}
              <Box sx={{ px: 2, py: 1.5 }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                  {user.username || 'User'}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {user.email || ''}
                </Typography>
                {user.is_admin && (
                  <Typography
                    variant="caption"
                    sx={{
                      display: 'block',
                      mt: 0.5,
                      color: 'primary.main',
                      fontWeight: 600,
                    }}
                  >
                    Admin Account
                  </Typography>
                )}
              </Box>

              <Divider />

              {/* Navigation Items */}
              {!user.is_admin && (
                <MenuItem onClick={() => handleNavigation('/my-applications')}>
                  <ListItemIcon>
                    <AssignmentIcon fontSize="small" />
                  </ListItemIcon>
                  My Applications
                </MenuItem>
              )}

              {user.is_super_admin && (
                <MenuItem onClick={() => handleNavigation('/super-admin')}>
                  <ListItemIcon>
                    <ShieldIcon fontSize="small" />
                  </ListItemIcon>
                  Super Admin
                </MenuItem>
              )}

              {user.is_admin && !user.is_super_admin && (
                <MenuItem onClick={() => handleNavigation('/admin')}>
                  <ListItemIcon>
                    <AssignmentIcon fontSize="small" />
                  </ListItemIcon>
                  Admin Dashboard
                </MenuItem>
              )}

              <MenuItem onClick={() => handleNavigation('/profile')}>
                <ListItemIcon>
                  <PersonIcon fontSize="small" />
                </ListItemIcon>
                Profile
              </MenuItem>

              <Divider />

              {/* Logout */}
              <MenuItem onClick={handleLogout} sx={{ color: 'error.main' }}>
                <ListItemIcon>
                  <LogoutIcon fontSize="small" color="error" />
                </ListItemIcon>
                Logout
              </MenuItem>
            </Menu>
          </>
        )}

        {/* Show login button if not logged in */}
        {showUserMenu && !user && (
          <IconButton
            color="inherit"
            onClick={() => navigate('/login')}
            sx={{
              bgcolor: 'rgba(255,255,255,0.2)',
              '&:hover': {
                bgcolor: 'rgba(255,255,255,0.3)',
              },
            }}
          >
            <PersonIcon />
          </IconButton>
        )}
      </Toolbar>
    </AppBar>
  );
};

export default Navbar;
