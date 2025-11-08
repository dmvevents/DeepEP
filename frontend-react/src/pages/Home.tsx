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
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        py: 8,
      }}
    >
      <Container maxWidth="lg">
        <Box textAlign="center" mb={8}>
          <Typography
            variant="h2"
            component="h1"
            gutterBottom
            sx={{ color: 'white', fontWeight: 700, mb: 2 }}
          >
            🏠 Real Estate Mortgage Calculator
          </Typography>
          <Typography variant="h5" sx={{ color: 'white', opacity: 0.9, mb: 4 }}>
            Smart qualification system with automatic property lookup and AI-powered document processing
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button
              variant="contained"
              size="large"
              onClick={() => navigate('/mortgage-application')}
              sx={{
                bgcolor: 'white',
                color: '#667eea',
                px: 4,
                py: 1.5,
                fontSize: '1.1rem',
                '&:hover': {
                  bgcolor: 'rgba(255,255,255,0.9)',
                  transform: 'translateY(-2px)',
                },
              }}
              startIcon={<CalculateIcon />}
            >
              Start Application
            </Button>
          </Box>
        </Box>

        <Grid container spacing={4}>
          {features.map((feature) => (
            <Grid item xs={12} md={4} key={feature.title}>
              <Card
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    transform: 'translateY(-8px)',
                    boxShadow: '0 12px 40px rgba(0,0,0,0.3)',
                  },
                }}
              >
                <CardContent sx={{ flexGrow: 1, textAlign: 'center', p: 4 }}>
                  <Box mb={2}>{feature.icon}</Box>
                  <Typography variant="h5" component="h2" gutterBottom fontWeight={600}>
                    {feature.title}
                  </Typography>
                  <Typography variant="body1" color="text.secondary">
                    {feature.description}
                  </Typography>
                </CardContent>
                <CardActions sx={{ p: 3, pt: 0 }}>
                  <Button
                    fullWidth
                    variant="contained"
                    onClick={() => navigate(feature.path)}
                    sx={{
                      bgcolor: feature.color,
                      '&:hover': {
                        bgcolor: feature.color,
                        opacity: 0.9,
                      },
                    }}
                  >
                    Open
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>

        <Box mt={8} p={4} bgcolor="rgba(255,255,255,0.1)" borderRadius={3}>
          <Typography variant="h4" gutterBottom sx={{ color: 'white', fontWeight: 600 }}>
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
