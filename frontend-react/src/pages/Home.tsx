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
  Avatar,
  Chip,
} from '@mui/material';
import HomeIcon from '@mui/icons-material/Home';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import DescriptionIcon from '@mui/icons-material/Description';
import CalculateIcon from '@mui/icons-material/Calculate';
import LoginIcon from '@mui/icons-material/Login';
import VerifiedUserIcon from '@mui/icons-material/VerifiedUser';
import LockIcon from '@mui/icons-material/Lock';
import SpeedIcon from '@mui/icons-material/Speed';
import SupportAgentIcon from '@mui/icons-material/SupportAgent';
import SearchIcon from '@mui/icons-material/Search';
import AssignmentTurnedInIcon from '@mui/icons-material/AssignmentTurnedIn';
import HomeWorkIcon from '@mui/icons-material/HomeWork';
import Navbar from '../components/Navbar';

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
    <>
      <Navbar title="Home" showUserMenu={true} />
      <Box
        sx={{
          minHeight: 'calc(100vh - 64px)',
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

          {/* Trust Badges */}
          <Box
            sx={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: { xs: 2, sm: 3 },
              justifyContent: 'center',
              alignItems: 'center',
              mt: 4,
            }}
          >
            <Chip
              icon={<VerifiedUserIcon />}
              label="Bank-Level Security"
              sx={{
                bgcolor: 'rgba(255,255,255,0.2)',
                color: 'white',
                backdropFilter: 'blur(10px)',
                px: 2,
                py: 2.5,
                fontSize: '0.95rem',
                fontWeight: 600,
              }}
            />
            <Chip
              icon={<LockIcon />}
              label="256-bit Encryption"
              sx={{
                bgcolor: 'rgba(255,255,255,0.2)',
                color: 'white',
                backdropFilter: 'blur(10px)',
                px: 2,
                py: 2.5,
                fontSize: '0.95rem',
                fontWeight: 600,
              }}
            />
            <Chip
              icon={<SpeedIcon />}
              label="Instant Results"
              sx={{
                bgcolor: 'rgba(255,255,255,0.2)',
                color: 'white',
                backdropFilter: 'blur(10px)',
                px: 2,
                py: 2.5,
                fontSize: '0.95rem',
                fontWeight: 600,
              }}
            />
            <Chip
              icon={<SupportAgentIcon />}
              label="Expert Support"
              sx={{
                bgcolor: 'rgba(255,255,255,0.2)',
                color: 'white',
                backdropFilter: 'blur(10px)',
                px: 2,
                py: 2.5,
                fontSize: '0.95rem',
                fontWeight: 600,
              }}
            />
          </Box>
        </Box>

        {/* How It Works Section */}
        <Box
          sx={{
            bgcolor: 'rgba(255,255,255,0.15)',
            backdropFilter: 'blur(10px)',
            borderRadius: 4,
            border: '1px solid rgba(255,255,255,0.2)',
            p: { xs: 3, sm: 4, md: 5 },
            mb: { xs: 4, sm: 6 },
          }}
        >
          <Typography
            variant="h4"
            align="center"
            gutterBottom
            sx={{
              color: 'white',
              fontWeight: 700,
              mb: 4,
              fontSize: { xs: '1.5rem', sm: '2rem', md: '2.125rem' },
            }}
          >
            How It Works - 3 Simple Steps
          </Typography>
          <Grid container spacing={4}>
            <Grid item xs={12} md={4}>
              <Box textAlign="center">
                <Avatar
                  sx={{
                    width: 80,
                    height: 80,
                    margin: '0 auto 16px',
                    bgcolor: 'white',
                    color: '#667eea',
                  }}
                >
                  <SearchIcon sx={{ fontSize: 40 }} />
                </Avatar>
                <Typography variant="h5" gutterBottom sx={{ color: 'white', fontWeight: 600 }}>
                  1. Enter Property
                </Typography>
                <Typography sx={{ color: 'white', opacity: 0.9 }}>
                  Simply enter the property address. We'll automatically fetch property taxes, insurance, and all
                  associated fees from official government sources.
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} md={4}>
              <Box textAlign="center">
                <Avatar
                  sx={{
                    width: 80,
                    height: 80,
                    margin: '0 auto 16px',
                    bgcolor: 'white',
                    color: '#667eea',
                  }}
                >
                  <CalculateIcon sx={{ fontSize: 40 }} />
                </Avatar>
                <Typography variant="h5" gutterBottom sx={{ color: 'white', fontWeight: 600 }}>
                  2. Get Instant Calculation
                </Typography>
                <Typography sx={{ color: 'white', opacity: 0.9 }}>
                  Our advanced calculator provides accurate monthly payments, DTI ratios, and closing costs. See 4
                  transfer tax scenarios with first-time buyer exemptions.
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} md={4}>
              <Box textAlign="center">
                <Avatar
                  sx={{
                    width: 80,
                    height: 80,
                    margin: '0 auto 16px',
                    bgcolor: 'white',
                    color: '#667eea',
                  }}
                >
                  <AssignmentTurnedInIcon sx={{ fontSize: 40 }} />
                </Avatar>
                <Typography variant="h5" gutterBottom sx={{ color: 'white', fontWeight: 600 }}>
                  3. Upload Documents
                </Typography>
                <Typography sx={{ color: 'white', opacity: 0.9 }}>
                  Upload income documents and let our AI-powered OCR extract data automatically. W-2s, pay stubs, and
                  tax returns processed in seconds.
                </Typography>
              </Box>
            </Grid>
          </Grid>
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

        {/* Testimonials Section */}
        <Box mt={{ xs: 6, sm: 8 }}>
          <Typography
            variant="h4"
            align="center"
            gutterBottom
            sx={{
              color: 'white',
              fontWeight: 700,
              mb: 4,
              fontSize: { xs: '1.75rem', sm: '2.125rem' },
            }}
          >
            What Our Customers Say
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <Card
                sx={{
                  height: '100%',
                  bgcolor: 'rgba(255,255,255,0.15)',
                  backdropFilter: 'blur(10px)',
                  border: '1px solid rgba(255,255,255,0.2)',
                  boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
                }}
              >
                <CardContent sx={{ p: 3 }}>
                  <Box display="flex" alignItems="center" mb={2}>
                    <Avatar sx={{ bgcolor: '#667eea', mr: 2 }}>E</Avatar>
                    <Box>
                      <Typography variant="h6" sx={{ color: 'white', fontWeight: 600 }}>
                        Emily R.
                      </Typography>
                      <Typography variant="body2" sx={{ color: 'white', opacity: 0.8 }}>
                        First-Time Homebuyer
                      </Typography>
                    </Box>
                  </Box>
                  <Typography sx={{ color: 'white', opacity: 0.9, lineHeight: 1.6 }}>
                    "This calculator made my first home purchase so much easier! The automatic tax lookup saved me
                    hours of research, and seeing all the costs upfront gave me confidence in my decision."
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card
                sx={{
                  height: '100%',
                  bgcolor: 'rgba(255,255,255,0.15)',
                  backdropFilter: 'blur(10px)',
                  border: '1px solid rgba(255,255,255,0.2)',
                  boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
                }}
              >
                <CardContent sx={{ p: 3 }}>
                  <Box display="flex" alignItems="center" mb={2}>
                    <Avatar sx={{ bgcolor: '#764ba2', mr: 2 }}>M</Avatar>
                    <Box>
                      <Typography variant="h6" sx={{ color: 'white', fontWeight: 600 }}>
                        Michael T.
                      </Typography>
                      <Typography variant="body2" sx={{ color: 'white', opacity: 0.8 }}>
                        Real Estate Investor
                      </Typography>
                    </Box>
                  </Box>
                  <Typography sx={{ color: 'white', opacity: 0.9, lineHeight: 1.6 }}>
                    "As an investor analyzing multiple properties, the speed and accuracy of this tool is
                    incredible. The DTI calculations and transfer tax scenarios help me make quick, informed
                    decisions."
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card
                sx={{
                  height: '100%',
                  bgcolor: 'rgba(255,255,255,0.15)',
                  backdropFilter: 'blur(10px)',
                  border: '1px solid rgba(255,255,255,0.2)',
                  boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
                }}
              >
                <CardContent sx={{ p: 3 }}>
                  <Box display="flex" alignItems="center" mb={2}>
                    <Avatar sx={{ bgcolor: '#10b981', mr: 2 }}>S</Avatar>
                    <Box>
                      <Typography variant="h6" sx={{ color: 'white', fontWeight: 600 }}>
                        Sarah L.
                      </Typography>
                      <Typography variant="body2" sx={{ color: 'white', opacity: 0.8 }}>
                        Mortgage Broker
                      </Typography>
                    </Box>
                  </Box>
                  <Typography sx={{ color: 'white', opacity: 0.9, lineHeight: 1.6 }}>
                    "The admin dashboard is a game-changer for managing multiple clients. The AI document extraction
                    saves us so much time, and clients love the transparency of the detailed breakdowns."
                  </Typography>
                </CardContent>
              </Card>
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
    </>
  );
};

export default Home;
