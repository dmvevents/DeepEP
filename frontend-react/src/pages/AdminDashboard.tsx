import { useState } from 'react';
import {
  Container,
  Box,
  Typography,
  Button,
  Paper,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  Card,
  CardContent,
  Alert,
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import ToggleOffIcon from '@mui/icons-material/ToggleOff';
import ToggleOnIcon from '@mui/icons-material/ToggleOn';
import VisibilityIcon from '@mui/icons-material/Visibility';

interface Borrower {
  id: number;
  loanNumber: string;
  name: string;
  propertyAddress: string;
  maxLoanAmount: number;
  dtiRatio: number;
  status: 'active' | 'disabled' | 'pending';
  notes: string;
  documents: Document[];
}

interface Document {
  id: number;
  type: string;
  name: string;
  uploadDate: string;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

const AdminDashboard = () => {
  const [tabValue, setTabValue] = useState(0);
  const [borrowers, setBorrowers] = useState<Borrower[]>([
    {
      id: 1,
      loanNumber: 'LN-2025-001',
      name: 'John Doe',
      propertyAddress: '123 Main St, Rockville, MD 20850',
      maxLoanAmount: 500000,
      dtiRatio: 38.5,
      status: 'active',
      notes: 'First-time home buyer',
      documents: [
        { id: 1, type: 'W-2', name: 'w2_2024.pdf', uploadDate: '2025-01-10' },
        { id: 2, type: 'Paystub', name: 'paystub_jan.pdf', uploadDate: '2025-01-15' },
      ],
    },
    {
      id: 2,
      loanNumber: 'LN-2025-002',
      name: 'Jane Smith',
      propertyAddress: '456 Oak Ave, Bethesda, MD 20814',
      maxLoanAmount: 750000,
      dtiRatio: 45.2,
      status: 'active',
      notes: 'High DTI - needs review',
      documents: [
        { id: 3, type: 'W-2', name: 'w2_2024.pdf', uploadDate: '2025-01-12' },
        { id: 4, type: 'Tax Return', name: 'tax_2024.pdf', uploadDate: '2025-01-12' },
      ],
    },
    {
      id: 3,
      loanNumber: 'LN-2025-003',
      name: 'Bob Johnson',
      propertyAddress: '789 Elm Dr, Silver Spring, MD 20910',
      maxLoanAmount: 600000,
      dtiRatio: 32.1,
      status: 'pending',
      notes: 'Waiting for additional documents',
      documents: [],
    },
  ]);

  const [openModal, setOpenModal] = useState(false);
  const [editingBorrower, setEditingBorrower] = useState<Borrower | null>(null);
  const [formData, setFormData] = useState({
    loanNumber: '',
    name: '',
    propertyAddress: '',
    maxLoanAmount: 0,
    status: 'active' as 'active' | 'disabled' | 'pending',
    notes: '',
  });
  const [selectedBorrowerForDocs, setSelectedBorrowerForDocs] = useState<number | null>(null);

  const stats = {
    totalBorrowers: borrowers.length,
    activeApplications: borrowers.filter((b) => b.status === 'active').length,
    approvedThisMonth: borrowers.filter((b) => b.status === 'active').length,
    avgDti: (borrowers.reduce((sum, b) => sum + b.dtiRatio, 0) / borrowers.length).toFixed(1),
  };

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleOpenModal = (borrower?: Borrower) => {
    if (borrower) {
      setEditingBorrower(borrower);
      setFormData({
        loanNumber: borrower.loanNumber,
        name: borrower.name,
        propertyAddress: borrower.propertyAddress,
        maxLoanAmount: borrower.maxLoanAmount,
        status: borrower.status,
        notes: borrower.notes,
      });
    } else {
      setEditingBorrower(null);
      setFormData({
        loanNumber: `LN-2025-${String(borrowers.length + 1).padStart(3, '0')}`,
        name: '',
        propertyAddress: '',
        maxLoanAmount: 500000,
        status: 'active',
        notes: '',
      });
    }
    setOpenModal(true);
  };

  const handleCloseModal = () => {
    setOpenModal(false);
    setEditingBorrower(null);
  };

  const handleSaveBorrower = () => {
    if (editingBorrower) {
      // Update existing borrower
      setBorrowers((prev) =>
        prev.map((b) =>
          b.id === editingBorrower.id
            ? { ...b, ...formData }
            : b
        )
      );
    } else {
      // Create new borrower
      const newBorrower: Borrower = {
        id: borrowers.length + 1,
        ...formData,
        dtiRatio: 0,
        documents: [],
      };
      setBorrowers((prev) => [...prev, newBorrower]);
    }
    handleCloseModal();
  };

  const handleToggleStatus = (id: number) => {
    setBorrowers((prev) =>
      prev.map((b) =>
        b.id === id
          ? { ...b, status: b.status === 'active' ? 'disabled' : 'active' }
          : b
      )
    );
  };

  const handleDeleteBorrower = (id: number) => {
    if (window.confirm('Are you sure you want to delete this borrower?')) {
      setBorrowers((prev) => prev.filter((b) => b.id !== id));
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'disabled':
        return 'error';
      case 'pending':
        return 'warning';
      default:
        return 'default';
    }
  };

  const dtiWarnings = borrowers.filter((b) => b.dtiRatio > 43);

  return (
    <Box
      sx={{
        minHeight: '100vh',
        width: '100%',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        py: { xs: 2, sm: 3, md: 4 },
        px: { xs: 1, sm: 2, md: 3 },
      }}
    >
      <Container maxWidth="xl" disableGutters sx={{ width: '100%', px: { xs: 1, sm: 2, md: 3 } }}>
        {/* Header */}
        <Paper sx={{
          p: { xs: 2, sm: 3 },
          mb: { xs: 2, sm: 3 },
          display: 'flex',
          flexDirection: { xs: 'column', sm: 'row' },
          justifyContent: 'space-between',
          alignItems: { xs: 'flex-start', sm: 'center' },
          gap: { xs: 2, sm: 0 },
        }}>
          <Typography
            variant="h4"
            component="h1"
            sx={{
              color: '#667eea',
              fontWeight: 700,
              fontSize: { xs: '1.5rem', sm: '2rem', md: '2.125rem' },
            }}
          >
            🏦 Admin Dashboard
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: { xs: '100%', sm: 'auto' } }}>
            <Typography sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}>👤 Admin User</Typography>
            <Button
              variant="outlined"
              color="secondary"
              size="small"
              sx={{ whiteSpace: 'nowrap' }}
            >
              Logout
            </Button>
          </Box>
        </Paper>

        {/* Stats */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="body2" sx={{ opacity: 0.9 }}>
                  Total Borrowers
                </Typography>
                <Typography variant="h3" sx={{ my: 1, fontWeight: 700 }}>
                  {stats.totalBorrowers}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="body2" sx={{ opacity: 0.9 }}>
                  Active Applications
                </Typography>
                <Typography variant="h3" sx={{ my: 1, fontWeight: 700 }}>
                  {stats.activeApplications}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="body2" sx={{ opacity: 0.9 }}>
                  Approved This Month
                </Typography>
                <Typography variant="h3" sx={{ my: 1, fontWeight: 700 }}>
                  {stats.approvedThisMonth}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="body2" sx={{ opacity: 0.9 }}>
                  Avg. DTI Ratio
                </Typography>
                <Typography variant="h3" sx={{ my: 1, fontWeight: 700 }}>
                  {stats.avgDti}%
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Tabs */}
        <Paper>
          <Tabs
            value={tabValue}
            onChange={handleTabChange}
            variant="scrollable"
            scrollButtons="auto"
            allowScrollButtonsMobile
            sx={{ borderBottom: 1, borderColor: 'divider' }}
          >
            <Tab label="📋 Manage Borrowers" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }} />
            <Tab label="📄 View Documents" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }} />
            <Tab label="⚠️ DTI Warnings" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }} />
          </Tabs>

          {/* Tab 1: Manage Borrowers */}
          <TabPanel value={tabValue} index={0}>
            <Box sx={{ p: { xs: 2, sm: 3 } }}>
              <Box sx={{
                display: 'flex',
                flexDirection: { xs: 'column', sm: 'row' },
                justifyContent: 'space-between',
                alignItems: { xs: 'flex-start', sm: 'center' },
                gap: 2,
                mb: 3,
              }}>
                <Typography variant="h5" sx={{ fontSize: { xs: '1.25rem', sm: '1.5rem' } }}>
                  Borrower Profiles
                </Typography>
                <Button
                  variant="contained"
                  color="secondary"
                  onClick={() => handleOpenModal()}
                  sx={{ whiteSpace: 'nowrap', width: { xs: '100%', sm: 'auto' } }}
                >
                  + Create New Borrower
                </Button>
              </Box>

              <TableContainer sx={{ overflowX: 'auto' }}>
                <Table sx={{ minWidth: 650 }}>
                  <TableHead>
                    <TableRow>
                      <TableCell>Loan Number</TableCell>
                      <TableCell>Name</TableCell>
                      <TableCell>Property Address</TableCell>
                      <TableCell>Max Loan Amount</TableCell>
                      <TableCell>DTI Ratio</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {borrowers.map((borrower) => (
                      <TableRow key={borrower.id} hover>
                        <TableCell>{borrower.loanNumber}</TableCell>
                        <TableCell>{borrower.name}</TableCell>
                        <TableCell>{borrower.propertyAddress}</TableCell>
                        <TableCell>${borrower.maxLoanAmount.toLocaleString()}</TableCell>
                        <TableCell>{borrower.dtiRatio.toFixed(1)}%</TableCell>
                        <TableCell>
                          <Chip label={borrower.status} color={getStatusColor(borrower.status)} size="small" />
                        </TableCell>
                        <TableCell>
                          <IconButton size="small" onClick={() => handleOpenModal(borrower)} color="primary">
                            <EditIcon />
                          </IconButton>
                          <IconButton size="small" onClick={() => handleToggleStatus(borrower.id)} color="secondary">
                            {borrower.status === 'active' ? <ToggleOnIcon /> : <ToggleOffIcon />}
                          </IconButton>
                          <IconButton size="small" onClick={() => handleDeleteBorrower(borrower.id)} color="error">
                            <DeleteIcon />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          </TabPanel>

          {/* Tab 2: View Documents */}
          <TabPanel value={tabValue} index={1}>
            <Box sx={{ p: { xs: 2, sm: 3 } }}>
              <Typography variant="h5" gutterBottom sx={{ fontSize: { xs: '1.25rem', sm: '1.5rem' } }}>
                Uploaded Documents by Borrower
              </Typography>
              <FormControl fullWidth sx={{ mb: 3, maxWidth: 400 }}>
                <InputLabel>Select Borrower</InputLabel>
                <Select
                  value={selectedBorrowerForDocs || ''}
                  label="Select Borrower"
                  onChange={(e) => setSelectedBorrowerForDocs(Number(e.target.value))}
                >
                  <MenuItem value="">-- Select Borrower --</MenuItem>
                  {borrowers.map((borrower) => (
                    <MenuItem key={borrower.id} value={borrower.id}>
                      {borrower.name} ({borrower.loanNumber})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {selectedBorrowerForDocs ? (
                <Box>
                  {borrowers
                    .find((b) => b.id === selectedBorrowerForDocs)
                    ?.documents.map((doc) => (
                      <Paper key={doc.id} sx={{ p: 2, mb: 2, display: 'flex', justifyContent: 'space-between' }}>
                        <Box>
                          <Typography variant="body1" fontWeight={600}>
                            {doc.name}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Type: {doc.type} | Uploaded: {doc.uploadDate}
                          </Typography>
                        </Box>
                        <Box>
                          <IconButton color="primary">
                            <VisibilityIcon />
                          </IconButton>
                          <IconButton color="error">
                            <DeleteIcon />
                          </IconButton>
                        </Box>
                      </Paper>
                    ))}
                  {borrowers.find((b) => b.id === selectedBorrowerForDocs)?.documents.length === 0 && (
                    <Alert severity="info">No documents uploaded for this borrower yet.</Alert>
                  )}
                </Box>
              ) : (
                <Typography color="text.secondary">Select a borrower to view their uploaded documents</Typography>
              )}
            </Box>
          </TabPanel>

          {/* Tab 3: DTI Warnings */}
          <TabPanel value={tabValue} index={2}>
            <Box sx={{ p: { xs: 2, sm: 3 } }}>
              <Typography variant="h5" gutterBottom sx={{ fontSize: { xs: '1.25rem', sm: '1.5rem' } }}>
                DTI Ratio Warnings
              </Typography>
              <Typography color="text.secondary" sx={{ mb: 3 }}>
                Borrowers with DTI ratios approaching or exceeding limits
              </Typography>

              {dtiWarnings.length > 0 ? (
                dtiWarnings.map((borrower) => (
                  <Alert key={borrower.id} severity="warning" sx={{ mb: 2 }}>
                    <Typography variant="body1" fontWeight={600}>
                      {borrower.name} ({borrower.loanNumber})
                    </Typography>
                    <Typography variant="body2">
                      DTI Ratio: <strong>{borrower.dtiRatio.toFixed(1)}%</strong> | Max Loan Amount: ${borrower.maxLoanAmount.toLocaleString()}
                    </Typography>
                    <Typography variant="body2" sx={{ mt: 1 }}>
                      <strong>Suggestions:</strong>
                      <ul style={{ marginTop: 4, marginLeft: 20 }}>
                        <li>Consider FHA loan with manual underwriting (up to 50% DTI)</li>
                        <li>Reduce monthly debt obligations before applying</li>
                        <li>Increase down payment to reduce loan amount</li>
                        <li>Consider co-borrower to increase income</li>
                      </ul>
                    </Typography>
                  </Alert>
                ))
              ) : (
                <Alert severity="success">No borrowers currently have high DTI warnings. All ratios are within acceptable limits.</Alert>
              )}
            </Box>
          </TabPanel>
        </Paper>
      </Container>

      {/* Create/Edit Borrower Modal */}
      <Dialog open={openModal} onClose={handleCloseModal} maxWidth="sm" fullWidth>
        <DialogTitle>{editingBorrower ? 'Edit Borrower' : 'Create New Borrower'}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Loan Number"
                value={formData.loanNumber}
                onChange={(e) => setFormData({ ...formData, loanNumber: e.target.value })}
                disabled={!!editingBorrower}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Borrower Name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Property Address"
                value={formData.propertyAddress}
                onChange={(e) => setFormData({ ...formData, propertyAddress: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Max Loan Amount"
                type="number"
                value={formData.maxLoanAmount}
                onChange={(e) => setFormData({ ...formData, maxLoanAmount: Number(e.target.value) })}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={formData.status}
                  label="Status"
                  onChange={(e) => setFormData({ ...formData, status: e.target.value as any })}
                >
                  <MenuItem value="active">Active</MenuItem>
                  <MenuItem value="pending">Pending</MenuItem>
                  <MenuItem value="disabled">Disabled</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Notes"
                multiline
                rows={3}
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseModal}>Cancel</Button>
          <Button onClick={handleSaveBorrower} variant="contained">
            {editingBorrower ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AdminDashboard;
