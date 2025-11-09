import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  Grid,
  Paper,
  CircularProgress,
  Alert,
  IconButton,
  Tooltip,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import VisibilityIcon from '@mui/icons-material/Visibility';
import DeleteIcon from '@mui/icons-material/Delete';
import SendIcon from '@mui/icons-material/Send';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import HourglassEmptyIcon from '@mui/icons-material/HourglassEmpty';
import RefreshIcon from '@mui/icons-material/Refresh';
import Navbar from '../components/Navbar';

interface Application {
  id: string;
  property_address: string;
  property_value: number;
  loan_amount: number;
  status: string;
  created_at: string;
  updated_at: string;
  submitted_at?: string;
  monthly_payment?: number;
  admin_feedback?: string;
}

const MyApplications = () => {
  const navigate = useNavigate();
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadApplications();
  }, []);

  const loadApplications = async () => {
    try {
      setLoading(true);
      // TODO: Replace with actual API call when backend is ready
      // const response = await fetch('http://localhost:8004/api/loan-estimates/?user=me', {
      //   headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
      // });
      // const data = await response.json();

      // Mock data for now
      const mockData: Application[] = [
        {
          id: '1',
          property_address: '123 Main St, Rockville, MD 20850',
          property_value: 500000,
          loan_amount: 400000,
          status: 'draft',
          created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
          updated_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
          monthly_payment: 2400,
        },
        {
          id: '2',
          property_address: '456 Oak Ave, Silver Spring, MD 20901',
          property_value: 650000,
          loan_amount: 520000,
          status: 'submitted',
          created_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
          updated_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
          submitted_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
          monthly_payment: 3100,
        },
        {
          id: '3',
          property_address: '789 Elm St, Bethesda, MD 20814',
          property_value: 800000,
          loan_amount: 640000,
          status: 'needs_correction',
          created_at: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(),
          updated_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
          submitted_at: new Date(Date.now() - 8 * 24 * 60 * 60 * 1000).toISOString(),
          monthly_payment: 3800,
          admin_feedback: 'Please update your income documentation. The W-2 form is unclear.',
        },
      ];

      setApplications(mockData);
      setLoading(false);
    } catch (err) {
      setError('Failed to load applications');
      setLoading(false);
    }
  };

  const getStatusConfig = (status: string) => {
    const configs: Record<string, { color: any; icon: JSX.Element; label: string }> = {
      draft: {
        color: 'default',
        icon: <EditIcon fontSize="small" />,
        label: 'Draft',
      },
      submitted: {
        color: 'info',
        icon: <SendIcon fontSize="small" />,
        label: 'Submitted',
      },
      under_review: {
        color: 'warning',
        icon: <HourglassEmptyIcon fontSize="small" />,
        label: 'Under Review',
      },
      needs_correction: {
        color: 'error',
        icon: <ErrorIcon fontSize="small" />,
        label: 'Needs Correction',
      },
      resubmitted: {
        color: 'info',
        icon: <RefreshIcon fontSize="small" />,
        label: 'Resubmitted',
      },
      approved: {
        color: 'success',
        icon: <CheckCircleIcon fontSize="small" />,
        label: 'Approved',
      },
      rejected: {
        color: 'error',
        icon: <ErrorIcon fontSize="small" />,
        label: 'Rejected',
      },
    };
    return configs[status] || configs.draft;
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const handleNewApplication = () => {
    // Clear any existing draft
    localStorage.removeItem('mortgage_application_draft');
    localStorage.removeItem('mortgage_application_draft_timestamp');
    navigate('/mortgage-application');
  };

  const handleResumeApplication = (app: Application) => {
    // TODO: Load application data into draft
    navigate('/mortgage-application');
  };

  const handleViewApplication = (app: Application) => {
    // TODO: Navigate to read-only detail view
    navigate(`/application/${app.id}`);
  };

  const handleDeleteApplication = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this application?')) {
      // TODO: API call to delete
      setApplications(applications.filter(app => app.id !== id));
    }
  };

  const getStatsCounts = () => {
    return {
      total: applications.length,
      draft: applications.filter(a => a.status === 'draft').length,
      submitted: applications.filter(a => a.status === 'submitted' || a.status === 'under_review' || a.status === 'resubmitted').length,
      needsAction: applications.filter(a => a.status === 'needs_correction').length,
      approved: applications.filter(a => a.status === 'approved').length,
    };
  };

  const stats = getStatsCounts();

  if (loading) {
    return (
      <>
        <Navbar title="My Applications" />
        <Box
          sx={{
            minHeight: 'calc(100vh - 64px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          }}
        >
          <CircularProgress size={60} sx={{ color: 'white' }} />
        </Box>
      </>
    );
  }

  return (
    <>
      <Navbar title="My Applications" />

      <Box
        sx={{
          minHeight: 'calc(100vh - 64px)',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          py: 4,
        }}
      >
        <Container maxWidth="lg">
          {/* Header */}
          <Box sx={{ mb: 4, textAlign: 'center' }}>
            <Typography
              variant="h3"
              sx={{ color: 'white', fontWeight: 700, mb: 2 }}
            >
              My Applications
            </Typography>
            <Typography variant="h6" sx={{ color: 'white', opacity: 0.9 }}>
              Track and manage your mortgage applications
            </Typography>
          </Box>

          {/* Stats Cards */}
          <Grid container spacing={2} sx={{ mb: 4 }}>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" color="primary">
                  {stats.total}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Applications
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" color="text.secondary">
                  {stats.draft}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Drafts
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" sx={{ color: '#2196f3' }}>
                  {stats.submitted}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  In Review
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Paper sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="h4" sx={{ color: '#f44336' }}>
                  {stats.needsAction}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Needs Action
                </Typography>
              </Paper>
            </Grid>
          </Grid>

          {/* New Application Button */}
          <Box sx={{ mb: 3, textAlign: 'center' }}>
            <Button
              variant="contained"
              size="large"
              startIcon={<AddIcon />}
              onClick={handleNewApplication}
              sx={{
                bgcolor: 'white',
                color: '#667eea',
                fontWeight: 600,
                px: 4,
                py: 1.5,
                '&:hover': {
                  bgcolor: 'rgba(255,255,255,0.9)',
                },
              }}
            >
              Start New Application
            </Button>
          </Box>

          {/* Error Alert */}
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          {/* Applications List */}
          {applications.length === 0 ? (
            <Paper
              sx={{
                p: 6,
                textAlign: 'center',
                bgcolor: 'rgba(255,255,255,0.95)',
              }}
            >
              <Typography variant="h6" gutterBottom>
                No applications yet
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Start your first mortgage application to get pre-qualified
              </Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={handleNewApplication}
              >
                Create Application
              </Button>
            </Paper>
          ) : (
            <Grid container spacing={3}>
              {applications.map((app) => {
                const statusConfig = getStatusConfig(app.status);
                return (
                  <Grid item xs={12} key={app.id}>
                    <Card
                      sx={{
                        bgcolor: 'rgba(255,255,255,0.95)',
                        backdropFilter: 'blur(10px)',
                        '&:hover': {
                          boxShadow: '0 8px 24px rgba(0,0,0,0.15)',
                          transform: 'translateY(-2px)',
                          transition: 'all 0.3s ease',
                        },
                      }}
                    >
                      <CardContent>
                        <Box
                          sx={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'flex-start',
                            mb: 2,
                          }}
                        >
                          <Box sx={{ flex: 1 }}>
                            <Typography variant="h6" gutterBottom>
                              {app.property_address}
                            </Typography>
                            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 1 }}>
                              <Typography variant="body2" color="text.secondary">
                                <strong>Property Value:</strong> {formatCurrency(app.property_value)}
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                <strong>Loan Amount:</strong> {formatCurrency(app.loan_amount)}
                              </Typography>
                              {app.monthly_payment && (
                                <Typography variant="body2" color="text.secondary">
                                  <strong>Monthly Payment:</strong> {formatCurrency(app.monthly_payment)}
                                </Typography>
                              )}
                            </Box>
                            <Typography variant="caption" color="text.secondary">
                              Created: {formatDate(app.created_at)} | Updated: {formatDate(app.updated_at)}
                            </Typography>
                          </Box>
                          <Chip
                            icon={statusConfig.icon}
                            label={statusConfig.label}
                            color={statusConfig.color}
                            sx={{ ml: 2 }}
                          />
                        </Box>

                        {/* Admin Feedback */}
                        {app.admin_feedback && (
                          <Alert severity="warning" sx={{ mb: 2 }}>
                            <strong>Admin Feedback:</strong> {app.admin_feedback}
                          </Alert>
                        )}
                      </CardContent>

                      <CardActions sx={{ justifyContent: 'flex-end', px: 2, pb: 2 }}>
                        {app.status === 'draft' && (
                          <>
                            <Tooltip title="Continue editing">
                              <IconButton
                                size="small"
                                color="primary"
                                onClick={() => handleResumeApplication(app)}
                              >
                                <EditIcon />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Delete draft">
                              <IconButton
                                size="small"
                                color="error"
                                onClick={() => handleDeleteApplication(app.id)}
                              >
                                <DeleteIcon />
                              </IconButton>
                            </Tooltip>
                          </>
                        )}

                        {(app.status === 'submitted' ||
                          app.status === 'under_review' ||
                          app.status === 'approved' ||
                          app.status === 'rejected') && (
                          <Button
                            size="small"
                            startIcon={<VisibilityIcon />}
                            onClick={() => handleViewApplication(app)}
                          >
                            View Details
                          </Button>
                        )}

                        {app.status === 'needs_correction' && (
                          <Button
                            variant="contained"
                            size="small"
                            startIcon={<EditIcon />}
                            onClick={() => handleResumeApplication(app)}
                          >
                            Make Corrections
                          </Button>
                        )}
                      </CardActions>
                    </Card>
                  </Grid>
                );
              })}
            </Grid>
          )}
        </Container>
      </Box>
    </>
  );
};

export default MyApplications;
