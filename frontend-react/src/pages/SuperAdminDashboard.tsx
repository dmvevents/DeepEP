import { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  IconButton,
  Chip,
  Avatar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  Tabs,
  Tab,
  Tooltip,
  Badge,
  LinearProgress,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import VisibilityIcon from '@mui/icons-material/Visibility';
import SecurityIcon from '@mui/icons-material/Security';
import ShieldIcon from '@mui/icons-material/Shield';
import PersonIcon from '@mui/icons-material/Person';
import HistoryIcon from '@mui/icons-material/History';
import LockIcon from '@mui/icons-material/Lock';
import WarningIcon from '@mui/icons-material/Warning';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import Navbar from '../components/Navbar';
import type { AdminProfile, AuditLog } from '../types/admin';
import {
  formatPhoneNumber,
  formatDateTime,
  formatRelativeTime,
  formatNumber,
  formatPercentage,
} from '../utils/formatters';

const SuperAdminDashboard = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [admins, setAdmins] = useState<AdminProfile[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [openDialog, setOpenDialog] = useState(false);
  const [selectedAdmin, setSelectedAdmin] = useState<AdminProfile | null>(null);
  const [formData, setFormData] = useState({
    email: '',
    first_name: '',
    last_name: '',
    phone: '',
    license_number: '',
    nmls_id: '',
    territory: '',
    role: 'admin' as 'admin' | 'super_admin',
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);

      // TODO: Replace with actual API calls
      // const adminsResponse = await fetch('/api/admins/', {
      //   headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
      // });
      // const adminsData = await adminsResponse.json();

      // Mock data for super admin view
      const mockAdmins: AdminProfile[] = [
        {
          id: '1',
          user_id: 'u1',
          email: 'sarah.johnson@mortgageco.com',
          first_name: 'Sarah',
          last_name: 'Johnson',
          role: 'admin',
          phone: '(555) 234-5678',
          license_number: 'MLO123456',
          nmls_id: '987654',
          territory: ['MD', 'VA', 'DC'],
          is_active: true,
          two_factor_enabled: true,
          created_at: new Date(Date.now() - 180 * 24 * 60 * 60 * 1000).toISOString(),
          updated_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
          last_login: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
          applications_reviewed: 127,
          avg_review_time_hours: 18.5,
          approval_rate: 78,
        },
        {
          id: '2',
          user_id: 'u2',
          email: 'michael.chen@mortgageco.com',
          first_name: 'Michael',
          last_name: 'Chen',
          role: 'admin',
          phone: '(555) 345-6789',
          license_number: 'MLO234567',
          nmls_id: '876543',
          territory: ['CA', 'NV', 'AZ'],
          is_active: true,
          two_factor_enabled: false,
          created_at: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString(),
          updated_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
          last_login: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
          applications_reviewed: 65,
          avg_review_time_hours: 24.2,
          approval_rate: 82,
        },
        {
          id: '3',
          user_id: 'u3',
          email: 'jessica.rodriguez@mortgageco.com',
          first_name: 'Jessica',
          last_name: 'Rodriguez',
          role: 'admin',
          phone: '(555) 456-7890',
          license_number: 'MLO345678',
          nmls_id: '765432',
          territory: ['TX', 'OK', 'LA'],
          is_active: false,
          two_factor_enabled: true,
          created_at: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000).toISOString(),
          updated_at: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000).toISOString(),
          last_login: new Date(Date.now() - 20 * 24 * 60 * 60 * 1000).toISOString(),
          applications_reviewed: 43,
          avg_review_time_hours: 22.8,
          approval_rate: 75,
        },
      ];

      const mockAuditLogs: AuditLog[] = [
        {
          id: 'log1',
          admin_id: '1',
          admin_name: 'Sarah Johnson',
          action: 'viewed_application',
          resource_type: 'application',
          resource_id: 'app123',
          details: 'Viewed application for 123 Main St, Rockville, MD',
          ip_address: '192.168.1.10',
          timestamp: new Date(Date.now() - 1 * 60 * 60 * 1000).toISOString(),
          sensitive_data_accessed: true,
        },
        {
          id: 'log2',
          admin_id: '2',
          admin_name: 'Michael Chen',
          action: 'updated_status',
          resource_type: 'application',
          resource_id: 'app124',
          details: 'Changed status from Submitted to Under Review',
          ip_address: '192.168.1.15',
          timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
          sensitive_data_accessed: false,
        },
        {
          id: 'log3',
          admin_id: '1',
          admin_name: 'Sarah Johnson',
          action: 'viewed_document',
          resource_type: 'document',
          resource_id: 'doc456',
          details: 'Viewed W-2 document for user Emily Thompson',
          ip_address: '192.168.1.10',
          timestamp: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
          sensitive_data_accessed: true,
        },
      ];

      setAdmins(mockAdmins);
      setAuditLogs(mockAuditLogs);
      setLoading(false);
    } catch (error) {
      console.error('Error loading data:', error);
      setLoading(false);
    }
  };

  const handleOpenDialog = (admin?: AdminProfile) => {
    if (admin) {
      setSelectedAdmin(admin);
      setFormData({
        email: admin.email,
        first_name: admin.first_name,
        last_name: admin.last_name,
        phone: admin.phone,
        license_number: admin.license_number || '',
        nmls_id: admin.nmls_id || '',
        territory: admin.territory.join(', '),
        role: admin.role === 'super_admin' ? 'super_admin' : 'admin',
      });
    } else {
      setSelectedAdmin(null);
      setFormData({
        email: '',
        first_name: '',
        last_name: '',
        phone: '',
        license_number: '',
        nmls_id: '',
        territory: '',
        role: 'admin',
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setSelectedAdmin(null);
  };

  const handleSaveAdmin = async () => {
    try {
      // TODO: Replace with actual API call
      // if (selectedAdmin) {
      //   await fetch(`/api/admins/${selectedAdmin.id}/`, {
      //     method: 'PATCH',
      //     headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${localStorage.getItem('access_token')}` },
      //     body: JSON.stringify(formData)
      //   });
      // } else {
      //   await fetch('/api/admins/', {
      //     method: 'POST',
      //     headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${localStorage.getItem('access_token')}` },
      //     body: JSON.stringify(formData)
      //   });
      // }

      alert(selectedAdmin ? 'Admin updated successfully!' : 'Admin created successfully!');
      handleCloseDialog();
      loadData();
    } catch (error) {
      alert('Error saving admin: ' + (error as Error).message);
    }
  };

  const handleDeleteAdmin = async (_adminId: string) => {
    if (!window.confirm('Are you sure you want to delete this admin? This action cannot be undone.')) {
      return;
    }

    try {
      // TODO: Replace with actual API call
      // await fetch(`/api/admins/${_adminId}/`, {
      //   method: 'DELETE',
      //   headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
      // });

      alert('Admin deleted successfully!');
      loadData();
    } catch (error) {
      alert('Error deleting admin: ' + (error as Error).message);
    }
  };

  const handleToggleActive = async (admin: AdminProfile) => {
    try {
      // TODO: Replace with actual API call
      alert(`Admin ${admin.is_active ? 'deactivated' : 'activated'} successfully!`);
      loadData();
    } catch (error) {
      alert('Error toggling admin status: ' + (error as Error).message);
    }
  };


  const getStats = () => {
    const activeAdmins = admins.filter(a => a.is_active).length;
    const totalApplications = admins.reduce((sum, a) => sum + (a.applications_reviewed || 0), 0);
    const avgApprovalRate = admins.reduce((sum, a) => sum + (a.approval_rate || 0), 0) / admins.length;
    const adminsWithout2FA = admins.filter(a => a.is_active && !a.two_factor_enabled).length;

    return { activeAdmins, totalApplications, avgApprovalRate, adminsWithout2FA };
  };

  const stats = getStats();

  if (loading) {
    return (
      <>
        <Navbar title="Super Admin Dashboard" />
        <Box
          sx={{
            minHeight: 'calc(100vh - 64px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'linear-gradient(135deg, #1a237e 0%, #4a148c 100%)',
          }}
        >
          <LinearProgress sx={{ width: '50%', color: 'white' }} />
        </Box>
      </>
    );
  }

  return (
    <>
      <Navbar title="Super Admin Dashboard" />

      <Box
        sx={{
          minHeight: 'calc(100vh - 64px)',
          background: 'linear-gradient(135deg, #1a237e 0%, #4a148c 100%)',
          py: 4,
        }}
      >
        <Container maxWidth="xl">
          {/* Header */}
          <Box sx={{ mb: 4, textAlign: 'center' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 2 }}>
              <ShieldIcon sx={{ fontSize: 48, color: 'white', mr: 2 }} />
              <Typography variant="h3" sx={{ color: 'white', fontWeight: 700 }}>
                Super Admin Dashboard
              </Typography>
            </Box>
            <Typography variant="h6" sx={{ color: 'white', opacity: 0.9 }}>
              Manage administrators, monitor security, and oversee system operations
            </Typography>
          </Box>

          {/* Stats Cards */}
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} sm={6} md={3}>
              <Card
                sx={{
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  color: 'white',
                }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box>
                      <Typography variant="h4" sx={{ fontWeight: 700 }}>
                        {stats.activeAdmins}
                      </Typography>
                      <Typography variant="body2" sx={{ opacity: 0.9 }}>
                        Active Admins
                      </Typography>
                    </Box>
                    <PersonIcon sx={{ fontSize: 48, opacity: 0.8 }} />
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Card
                sx={{
                  background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                  color: 'white',
                }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box>
                      <Typography variant="h4" sx={{ fontWeight: 700 }}>
                        {stats.totalApplications}
                      </Typography>
                      <Typography variant="body2" sx={{ opacity: 0.9 }}>
                        Total Reviews
                      </Typography>
                    </Box>
                    <CheckCircleIcon sx={{ fontSize: 48, opacity: 0.8 }} />
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Card
                sx={{
                  background: 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)',
                  color: 'white',
                }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box>
                      <Typography variant="h4" sx={{ fontWeight: 700 }}>
                        {stats.avgApprovalRate.toFixed(0)}%
                      </Typography>
                      <Typography variant="body2" sx={{ opacity: 0.9 }}>
                        Avg Approval Rate
                      </Typography>
                    </Box>
                    <SecurityIcon sx={{ fontSize: 48, opacity: 0.8 }} />
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Card
                sx={{
                  background: stats.adminsWithout2FA > 0
                    ? 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)'
                    : 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                  color: 'white',
                }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box>
                      <Typography variant="h4" sx={{ fontWeight: 700 }}>
                        {stats.adminsWithout2FA}
                      </Typography>
                      <Typography variant="body2" sx={{ opacity: 0.9 }}>
                        Missing 2FA
                      </Typography>
                    </Box>
                    {stats.adminsWithout2FA > 0 ? (
                      <WarningIcon sx={{ fontSize: 48, opacity: 0.8 }} />
                    ) : (
                      <LockIcon sx={{ fontSize: 48, opacity: 0.8 }} />
                    )}
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Security Alert */}
          {stats.adminsWithout2FA > 0 && (
            <Alert severity="warning" sx={{ mb: 3 }}>
              <strong>Security Warning:</strong> {stats.adminsWithout2FA} admin(s) have not enabled 2FA. This poses a security risk for financial data access.
            </Alert>
          )}

          {/* Tabs */}
          <Paper sx={{ mb: 3 }}>
            <Tabs
              value={activeTab}
              onChange={(_, newValue) => setActiveTab(newValue)}
              variant="fullWidth"
              sx={{
                '& .MuiTab-root': { fontWeight: 600, fontSize: '1rem' },
              }}
            >
              <Tab icon={<PersonIcon />} label="Admin Management" />
              <Tab icon={<HistoryIcon />} label="Audit Log" />
              <Tab icon={<SecurityIcon />} label="Security Settings" />
            </Tabs>
          </Paper>

          {/* Tab Content */}
          {activeTab === 0 && (
            <Paper sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h5" sx={{ fontWeight: 600 }}>
                  Administrator Accounts
                </Typography>
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={() => handleOpenDialog()}
                  sx={{
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    fontWeight: 600,
                  }}
                >
                  Add New Admin
                </Button>
              </Box>

              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Admin</TableCell>
                      <TableCell>Contact</TableCell>
                      <TableCell>License</TableCell>
                      <TableCell>Territory</TableCell>
                      <TableCell>Performance</TableCell>
                      <TableCell>Security</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell align="right">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {admins.map((admin) => (
                      <TableRow key={admin.id} hover>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Avatar sx={{ mr: 2, bgcolor: admin.role === 'super_admin' ? '#ef4444' : '#667eea' }}>
                              {admin.first_name[0]}{admin.last_name[0]}
                            </Avatar>
                            <Box>
                              <Typography variant="body1" sx={{ fontWeight: 600 }}>
                                {admin.first_name} {admin.last_name}
                                {admin.role === 'super_admin' && (
                                  <Chip
                                    label="SUPER"
                                    size="small"
                                    color="error"
                                    sx={{ ml: 1, fontSize: '0.7rem', height: 20 }}
                                  />
                                )}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                Last login: {admin.last_login ? formatRelativeTime(admin.last_login) : 'Never'}
                              </Typography>
                            </Box>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">{admin.email}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {formatPhoneNumber(admin.phone)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">MLO: {admin.license_number}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            NMLS: {admin.nmls_id}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                            {admin.territory.map((state) => (
                              <Chip key={state} label={state} size="small" />
                            ))}
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">{formatNumber(admin.applications_reviewed || 0)} reviews</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {formatPercentage(admin.approval_rate || 0, 0)} approval • {admin.avg_review_time_hours}h avg
                          </Typography>
                        </TableCell>
                        <TableCell>
                          {admin.two_factor_enabled ? (
                            <Chip
                              icon={<LockIcon />}
                              label="2FA Enabled"
                              color="success"
                              size="small"
                            />
                          ) : (
                            <Chip
                              icon={<WarningIcon />}
                              label="No 2FA"
                              color="warning"
                              size="small"
                            />
                          )}
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={admin.is_active ? 'Active' : 'Inactive'}
                            color={admin.is_active ? 'success' : 'default'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell align="right">
                          <Tooltip title="View Profile">
                            <IconButton size="small" color="primary">
                              <VisibilityIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Edit Admin">
                            <IconButton size="small" color="primary" onClick={() => handleOpenDialog(admin)}>
                              <EditIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title={admin.is_active ? 'Deactivate' : 'Activate'}>
                            <IconButton size="small" onClick={() => handleToggleActive(admin)}>
                              {admin.is_active ? <LockIcon /> : <CheckCircleIcon />}
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Delete Admin">
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => handleDeleteAdmin(admin.id)}
                              disabled={admin.role === 'super_admin'}
                            >
                              <DeleteIcon />
                            </IconButton>
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          )}

          {activeTab === 1 && (
            <Paper sx={{ p: 3 }}>
              <Typography variant="h5" sx={{ fontWeight: 600, mb: 3 }}>
                Security Audit Log
              </Typography>

              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Timestamp</TableCell>
                      <TableCell>Admin</TableCell>
                      <TableCell>Action</TableCell>
                      <TableCell>Details</TableCell>
                      <TableCell>Sensitive Data</TableCell>
                      <TableCell>IP Address</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {auditLogs.map((log) => (
                      <TableRow key={log.id} hover>
                        <TableCell>
                          <Typography variant="body2">{formatDateTime(log.timestamp)}</Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            {log.admin_name}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={log.action.replace(/_/g, ' ')}
                            size="small"
                            color={
                              log.action.includes('delete') ? 'error' :
                              log.action.includes('update') ? 'warning' :
                              'default'
                            }
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">{log.details}</Typography>
                        </TableCell>
                        <TableCell>
                          {log.sensitive_data_accessed ? (
                            <Badge badgeContent="PII" color="error">
                              <Chip icon={<WarningIcon />} label="Yes" color="error" size="small" />
                            </Badge>
                          ) : (
                            <Chip label="No" size="small" />
                          )}
                        </TableCell>
                        <TableCell>
                          <Typography variant="caption">{log.ip_address}</Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          )}

          {activeTab === 2 && (
            <Paper sx={{ p: 3 }}>
              <Typography variant="h5" sx={{ fontWeight: 600, mb: 3 }}>
                Security Settings
              </Typography>

              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Two-Factor Authentication
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        Require all admins to enable 2FA for enhanced security
                      </Typography>
                      <Button variant="contained" color="primary">
                        Enforce 2FA for All Admins
                      </Button>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={12} md={6}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Session Timeout
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        Auto-logout inactive admin sessions for security
                      </Typography>
                      <FormControl fullWidth size="small">
                        <InputLabel>Timeout Duration</InputLabel>
                        <Select defaultValue="30" label="Timeout Duration">
                          <MenuItem value="15">15 minutes</MenuItem>
                          <MenuItem value="30">30 minutes</MenuItem>
                          <MenuItem value="60">1 hour</MenuItem>
                          <MenuItem value="120">2 hours</MenuItem>
                        </Select>
                      </FormControl>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={12} md={6}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        IP Whitelist
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        Restrict admin access to specific IP addresses
                      </Typography>
                      <Button variant="outlined">
                        Configure IP Whitelist
                      </Button>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={12} md={6}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Audit Log Retention
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        How long to retain security audit logs
                      </Typography>
                      <FormControl fullWidth size="small">
                        <InputLabel>Retention Period</InputLabel>
                        <Select defaultValue="365" label="Retention Period">
                          <MenuItem value="90">90 days</MenuItem>
                          <MenuItem value="180">180 days</MenuItem>
                          <MenuItem value="365">1 year</MenuItem>
                          <MenuItem value="730">2 years</MenuItem>
                        </Select>
                      </FormControl>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </Paper>
          )}
        </Container>
      </Box>

      {/* Add/Edit Admin Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {selectedAdmin ? 'Edit Administrator' : 'Add New Administrator'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="First Name"
                value={formData.first_name}
                onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Last Name"
                value={formData.last_name}
                onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Phone"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Role</InputLabel>
                <Select
                  value={formData.role}
                  label="Role"
                  onChange={(e) => setFormData({ ...formData, role: e.target.value as 'admin' | 'super_admin' })}
                >
                  <MenuItem value="admin">Admin</MenuItem>
                  <MenuItem value="super_admin">Super Admin</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="License Number (MLO)"
                value={formData.license_number}
                onChange={(e) => setFormData({ ...formData, license_number: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="NMLS ID"
                value={formData.nmls_id}
                onChange={(e) => setFormData({ ...formData, nmls_id: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Territory (comma-separated states)"
                placeholder="MD, VA, DC"
                value={formData.territory}
                onChange={(e) => setFormData({ ...formData, territory: e.target.value })}
                helperText="Enter state codes separated by commas"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleSaveAdmin}
            disabled={!formData.email || !formData.first_name || !formData.last_name}
          >
            {selectedAdmin ? 'Update Admin' : 'Create Admin'}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default SuperAdminDashboard;
