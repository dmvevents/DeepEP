import { useNavigate } from 'react-router-dom';
import {
  Container,
  Box,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  CardActions,
} from '@mui/material';
import HomeIcon from '@mui/icons-material/Home';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import DescriptionIcon from '@mui/icons-material/Description';
import CalculateIcon from '@mui/icons-material/Calculate';
import LoginIcon from '@mui/icons-material/Login';

const Home = () => {
  const navigate = useNavigate();

  const features = [
    {
      title: 'Mortgage Application',
      description: 'Complete mortgage application with automatic property lookup and tax calculations',
      icon: <HomeIcon sx={{ fontSize: 60, color: '#667eea' }} />,
      path: '/mortgage-application',
      color: '#667eea',
    },
    {
      title: 'Admin Dashboard',
      description: 'Manage borrowers, set qualification limits, and monitor DTI warnings',
      icon: <AdminPanelSettingsIcon sx={{ fontSize: 60, color: '#764ba2' }} />,
      path: '/admin',
      color: '#764ba2',
    },
    {
      title: 'Document Upload',
      description: 'Upload and process income documents with AI-powered OCR extraction',
      icon: <DescriptionIcon sx={{ fontSize: 60, color: '#10b981' }} />,
      path: '/documents',
      color: '#10b981',
    },
  ];

  return (
    <Box
      sx={{
        minHeight: '100vh',
        width: '100%',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        py: { xs: 4, sm: 6, md: 8 },
        px: { xs: 2, sm: 3, md: 4 },
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <Container
        maxWidth="xl"
        disableGutters
        sx={{
          width: '100%',
          px: { xs: 1, sm: 2, md: 3 },
        }}
      >
        <Box textAlign="center" mb={{ xs: 4, sm: 6, md: 8 }}>
          <Typography
            variant="h2"
            component="h1"
            gutterBottom
            sx={{
              color: 'white',
              fontWeight: 700,
              mb: 2,
              fontSize: { xs: '2rem', sm: '2.75rem', md: '3.75rem' },
            }}
          >
            🏠 Real Estate Mortgage Calculator
          </Typography>
          <Typography
            variant="h5"
            sx={{
              color: 'white',
              opacity: 0.9,
              mb: 4,
              fontSize: { xs: '1rem', sm: '1.25rem', md: '1.5rem' },
              px: { xs: 1, sm: 2 },
            }}
          >
            Smart qualification system with automatic property lookup and AI-powered document processing
          </Typography>
          <Box
            sx={{
              display: 'flex',
              flexDirection: { xs: 'column', sm: 'row' },
              gap: 2,
              justifyContent: 'center',
              alignItems: 'center',
            }}
          >
            <Button
              variant="contained"
              size="large"
              onClick={() => navigate('/mortgage-application')}
              fullWidth={false}
              sx={{
                bgcolor: 'white',
                color: '#667eea',
                px: { xs: 3, sm: 4 },
                py: { xs: 1.5, sm: 1.5 },
                fontSize: { xs: '1rem', sm: '1.1rem' },
                minWidth: { xs: '100%', sm: 220 },
                boxShadow: '0 4px 14px 0 rgba(0,0,0,0.15)',
                transition: 'all 0.3s ease',
                '&:hover': {
                  bgcolor: 'rgba(255,255,255,0.95)',
                  transform: 'translateY(-3px) scale(1.02)',
                  boxShadow: '0 6px 20px 0 rgba(0,0,0,0.25)',
                },
              }}
              startIcon={<CalculateIcon />}
            >
              Start Application
            </Button>
            <Button
              variant="outlined"
              size="large"
              onClick={() => navigate('/login')}
              fullWidth={false}
              sx={{
                borderColor: 'white',
                borderWidth: 2,
                color: 'white',
                px: { xs: 3, sm: 4 },
                py: { xs: 1.5, sm: 1.5 },
                fontSize: { xs: '1rem', sm: '1.1rem' },
                minWidth: { xs: '100%', sm: 220 },
                backdropFilter: 'blur(10px)',
                bgcolor: 'rgba(255,255,255,0.05)',
                transition: 'all 0.3s ease',
                '&:hover': {
                  borderColor: 'white',
                  borderWidth: 2,
                  bgcolor: 'rgba(255,255,255,0.15)',
                  transform: 'translateY(-3px) scale(1.02)',
                  boxShadow: '0 6px 20px 0 rgba(255,255,255,0.2)',
                },
              }}
              startIcon={<LoginIcon />}
            >
              Login
            </Button>
          </Box>
        </Box>

        <Grid container spacing={{ xs: 2, sm: 3, md: 4 }}>
          {features.map((feature) => (
            <Grid item xs={12} sm={6} md={4} key={feature.title}>
              <Card
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  borderRadius: 3,
                  boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
                  overflow: 'hidden',
                  position: 'relative',
                  transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
                  '&::before': {
                    content: '""',
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    height: '4px',
                    background: `linear-gradient(90deg, ${feature.color}, ${feature.color}dd)`,
                    transform: 'scaleX(0)',
                    transformOrigin: 'left',
                    transition: 'transform 0.4s ease',
                  },
                  '&:hover': {
                    transform: 'translateY(-12px) scale(1.02)',
                    boxShadow: '0 16px 48px rgba(0,0,0,0.18)',
                    '&::before': {
                      transform: 'scaleX(1)',
                    },
                  },
                }}
              >
                <CardContent
                  sx={{
                    flexGrow: 1,
                    textAlign: 'center',
                    p: { xs: 3, sm: 3, md: 4 },
                  }}
                >
                  <Box mb={2}>{feature.icon}</Box>
                  <Typography
                    variant="h5"
                    component="h2"
                    gutterBottom
                    fontWeight={600}
                    sx={{ fontSize: { xs: '1.25rem', sm: '1.5rem' } }}
                  >
                    {feature.title}
                  </Typography>
                  <Typography
                    variant="body1"
                    color="text.secondary"
                    sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}
                  >
                    {feature.description}
                  </Typography>
                </CardContent>
                <CardActions sx={{ p: { xs: 2, sm: 3 }, pt: 0 }}>
                  <Button
                    fullWidth
                    variant="contained"
                    onClick={() => navigate(feature.path)}
                    sx={{
                      bgcolor: feature.color,
                      py: { xs: 1.25, sm: 1.5 },
                      fontWeight: 600,
                      fontSize: '1rem',
                      textTransform: 'none',
                      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                      transition: 'all 0.3s ease',
                      '&:hover': {
                        bgcolor: feature.color,
                        opacity: 0.9,
                        transform: 'translateY(-2px)',
                        boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
                      },
                    }}
                  >
                    Explore →
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>

        <Box
          mt={{ xs: 6, sm: 8 }}
          p={{ xs: 3, sm: 4 }}
          sx={{
            bgcolor: 'rgba(255,255,255,0.12)',
            backdropFilter: 'blur(10px)',
            borderRadius: 4,
            border: '1px solid rgba(255,255,255,0.18)',
            boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
          }}
        >
          <Typography
            variant="h4"
            gutterBottom
            sx={{
              color: 'white',
              fontWeight: 700,
              fontSize: { xs: '1.75rem', sm: '2.125rem' },
              mb: 3,
            }}
          >
            ✨ Key Features
          </Typography>
          <Grid container spacing={3} mt={1}>
            <Grid item xs={12} sm={6}>
              <Typography sx={{ color: 'white', mb: 1 }}>
                ✓ <strong>Automatic Property Lookup:</strong> Get property taxes, insurance, and fees instantly
              </Typography>
              <Typography sx={{ color: 'white', mb: 1 }}>
                ✓ <strong>Transfer Tax Calculator:</strong> 4 scenarios with first-time buyer exemptions
              </Typography>
              <Typography sx={{ color: 'white', mb: 1 }}>
                ✓ <strong>AI-Powered OCR:</strong> Extract data from pay stubs, W-2s, and tax returns
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Typography sx={{ color: 'white', mb: 1 }}>
                ✓ <strong>Multi-Guideline Qualification:</strong> Fannie Mae, FHA, and VA loans
              </Typography>
              <Typography sx={{ color: 'white', mb: 1 }}>
                ✓ <strong>Admin Dashboard:</strong> Manage borrowers and set qualification limits
              </Typography>
              <Typography sx={{ color: 'white', mb: 1 }}>
                ✓ <strong>DTI Monitoring:</strong> Real-time warnings for high debt-to-income ratios
              </Typography>
            </Grid>
          </Grid>
        </Box>

        <Box mt={4} textAlign="center">
          <Typography variant="body2" sx={{ color: 'white', opacity: 0.8 }}>
            © 2025 Real Estate Mortgage Calculator | Created by Anton Alexander
          </Typography>
        </Box>
      </Container>
    </Box>
  );
};

export default Home;
