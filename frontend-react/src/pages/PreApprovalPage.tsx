import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Container,
  Box,
  Typography,
  Paper,
  Grid,
  TextField,
  Button,
  MenuItem,
  Alert,
  AlertTitle,
  CircularProgress,
  Stepper,
  Step,
  StepLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Card,
  CardContent,
  Divider,
  Chip,
} from '@mui/material';
import {
  Save as SaveIcon,
  Send as SendIcon,
  Preview as PreviewIcon,
  Check as CheckIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import Navbar from '../components/Navbar';
import { preApprovalApi, type PreApprovalData } from '../services/api';

const steps = ['Borrower Information', 'Financial Details', 'Property & Loan', 'Review & Submit'];

const PreApprovalPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const preApprovalId = searchParams.get('id');

  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewHtml, setPreviewHtml] = useState('');

  // Form state
  const [formData, setFormData] = useState<Partial<PreApprovalData>>({
    borrower_name: '',
    co_borrower_name: '',
    borrower_email: '',
    borrower_phone: '',
    annual_income: 0,
    monthly_income: 0,
    total_assets: 0,
    total_liabilities: 0,
    credit_score_estimate: 700,
    front_end_dti: 0,
    back_end_dti: 0,
    property_address: '',
    property_value_estimate: 0,
    down_payment_amount: 0,
    loan_type: 'conventional',
    max_loan_amount: 0,
    max_purchase_price: 0,
    estimated_rate: 0,
    expiration_date: '',
    internal_notes: '',
    conditions: '',
  });

  // Check RBAC - only loan officers and admins
  useEffect(() => {
    const user = localStorage.getItem('user');
    if (user) {
      const userData = JSON.parse(user);
      if (!userData.is_admin && !userData.is_loan_officer) {
        setError('Access denied. This page is only available to loan officers and admins.');
        return;
      }
    }
  }, []);

  // Load existing pre-approval if ID provided
  useEffect(() => {
    if (preApprovalId) {
      loadPreApproval(Number(preApprovalId));
    } else {
      // Set default expiration date (90 days from now)
      const expirationDate = new Date();
      expirationDate.setDate(expirationDate.getDate() + 90);
      setFormData((prev) => ({
        ...prev,
        expiration_date: expirationDate.toISOString().split('T')[0],
      }));
    }
  }, [preApprovalId]);

  const loadPreApproval = async (id: number) => {
    try {
      setLoading(true);
      const data = await preApprovalApi.get(id);
      setFormData(data);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load pre-approval');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field: keyof PreApprovalData) => (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const value = event.target.value;
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));

    // Auto-calculate monthly income from annual
    if (field === 'annual_income') {
      setFormData((prev) => ({
        ...prev,
        annual_income: Number(value),
        monthly_income: Number(value) / 12,
      }));
    }

    // Auto-calculate max purchase price and loan amount
    if (field === 'property_value_estimate' || field === 'down_payment_amount') {
      const propertyValue = field === 'property_value_estimate' ? Number(value) : formData.property_value_estimate || 0;
      const downPayment = field === 'down_payment_amount' ? Number(value) : formData.down_payment_amount || 0;
      const loanAmount = propertyValue - downPayment;

      setFormData((prev) => ({
        ...prev,
        [field]: Number(value),
        max_loan_amount: loanAmount,
        max_purchase_price: propertyValue,
      }));
    }

    // Calculate DTI ratios
    if (['monthly_income', 'total_liabilities', 'property_value_estimate', 'down_payment_amount', 'estimated_rate'].includes(field)) {
      calculateDTI();
    }
  };

  const calculateDTI = () => {
    const monthlyIncome = formData.monthly_income || 0;
    if (monthlyIncome === 0) return;

    // Estimate monthly housing payment (PITI)
    const loanAmount = (formData.property_value_estimate || 0) - (formData.down_payment_amount || 0);
    const monthlyRate = ((formData.estimated_rate || 6) / 100) / 12;
    const numPayments = 30 * 12;
    const monthlyPI = monthlyRate === 0 ? 0 :
      (loanAmount * monthlyRate * Math.pow(1 + monthlyRate, numPayments)) /
      (Math.pow(1 + monthlyRate, numPayments) - 1);

    // Rough estimate: add 30% for taxes and insurance
    const housingPayment = monthlyPI * 1.3;

    const totalDebts = (formData.total_liabilities || 0) / 12; // Convert annual to monthly
    const frontEndDti = (housingPayment / monthlyIncome) * 100;
    const backEndDti = ((housingPayment + totalDebts) / monthlyIncome) * 100;

    setFormData((prev) => ({
      ...prev,
      front_end_dti: Number(frontEndDti.toFixed(2)),
      back_end_dti: Number(backEndDti.toFixed(2)),
    }));
  };

  const handleNext = () => {
    setActiveStep((prev) => prev + 1);
  };

  const handleBack = () => {
    setActiveStep((prev) => prev - 1);
  };

  const handleSave = async (status: 'draft' | 'submitted' = 'draft') => {
    try {
      setLoading(true);
      setError(null);

      const dataToSubmit = {
        ...formData,
        status,
      };

      let result;
      if (formData.id) {
        result = await preApprovalApi.update(formData.id, dataToSubmit);
      } else {
        result = await preApprovalApi.create(dataToSubmit);
      }

      setFormData(result);
      setSuccess(`Pre-approval ${status === 'draft' ? 'saved' : 'submitted'} successfully!`);

      if (status === 'submitted') {
        setTimeout(() => {
          navigate('/pre-approvals');
        }, 2000);
      }
    } catch (err: any) {
      setError(err.response?.data?.message || `Failed to ${status === 'draft' ? 'save' : 'submit'} pre-approval`);
    } finally {
      setLoading(false);
    }
  };

  const handlePreview = async () => {
    if (!formData.id) {
      setError('Please save the pre-approval first before previewing the letter');
      return;
    }

    try {
      setLoading(true);
      const letter = await preApprovalApi.previewLetter(formData.id);
      setPreviewHtml(letter.html);
      setPreviewOpen(true);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to preview letter');
    } finally {
      setLoading(false);
    }
  };

  const handlePublish = async () => {
    if (!formData.id) {
      setError('Please save the pre-approval first');
      return;
    }

    try {
      setLoading(true);
      await preApprovalApi.generateLetter(formData.id);
      setSuccess('Pre-approval letter published successfully!');
      setPreviewOpen(false);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to publish letter');
    } finally {
      setLoading(false);
    }
  };

  const renderStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                required
                label="Borrower Name"
                value={formData.borrower_name}
                onChange={handleChange('borrower_name')}
                inputProps={{ 'aria-label': 'Borrower full name' }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Co-Borrower Name"
                value={formData.co_borrower_name}
                onChange={handleChange('co_borrower_name')}
                helperText="Optional"
                inputProps={{ 'aria-label': 'Co-borrower full name' }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="email"
                label="Email Address"
                value={formData.borrower_email}
                onChange={handleChange('borrower_email')}
                inputProps={{ 'aria-label': 'Borrower email address' }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Phone Number"
                value={formData.borrower_phone}
                onChange={handleChange('borrower_phone')}
                inputProps={{ 'aria-label': 'Borrower phone number' }}
              />
            </Grid>
          </Grid>
        );

      case 1:
        return (
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                required
                type="number"
                label="Annual Income"
                value={formData.annual_income}
                onChange={handleChange('annual_income')}
                InputProps={{ startAdornment: '$' }}
                helperText="Monthly income will be calculated automatically"
                inputProps={{ 'aria-label': 'Annual income', min: 0 }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                required
                type="number"
                label="Monthly Income"
                value={formData.monthly_income?.toFixed(2)}
                InputProps={{ startAdornment: '$', readOnly: true }}
                disabled
                helperText="Auto-calculated from annual income"
                inputProps={{ 'aria-label': 'Monthly income (calculated)' }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                required
                type="number"
                label="Total Assets"
                value={formData.total_assets}
                onChange={handleChange('total_assets')}
                InputProps={{ startAdornment: '$' }}
                helperText="Cash, investments, etc."
                inputProps={{ 'aria-label': 'Total assets', min: 0 }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                required
                type="number"
                label="Total Liabilities"
                value={formData.total_liabilities}
                onChange={handleChange('total_liabilities')}
                InputProps={{ startAdornment: '$' }}
                helperText="Credit cards, car loans, etc."
                inputProps={{ 'aria-label': 'Total liabilities', min: 0 }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                required
                type="number"
                label="Credit Score Estimate"
                value={formData.credit_score_estimate}
                onChange={handleChange('credit_score_estimate')}
                inputProps={{ 'aria-label': 'Credit score estimate', min: 300, max: 850 }}
                helperText="300-850"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    DTI Ratios (Auto-calculated)
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 2, mt: 1 }}>
                    <Chip
                      label={`Front-End: ${formData.front_end_dti?.toFixed(1) || 0}%`}
                      color={formData.front_end_dti && formData.front_end_dti <= 28 ? 'success' : 'warning'}
                      size="small"
                    />
                    <Chip
                      label={`Back-End: ${formData.back_end_dti?.toFixed(1) || 0}%`}
                      color={formData.back_end_dti && formData.back_end_dti <= 36 ? 'success' : 'warning'}
                      size="small"
                    />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        );

      case 2:
        return (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Property Address"
                value={formData.property_address}
                onChange={handleChange('property_address')}
                multiline
                rows={2}
                helperText="Optional - for specific property"
                inputProps={{ 'aria-label': 'Property address' }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                required
                type="number"
                label="Property Value Estimate"
                value={formData.property_value_estimate}
                onChange={handleChange('property_value_estimate')}
                InputProps={{ startAdornment: '$' }}
                inputProps={{ 'aria-label': 'Estimated property value', min: 0 }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                required
                type="number"
                label="Down Payment Amount"
                value={formData.down_payment_amount}
                onChange={handleChange('down_payment_amount')}
                InputProps={{ startAdornment: '$' }}
                inputProps={{ 'aria-label': 'Down payment amount', min: 0 }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                required
                select
                label="Loan Type"
                value={formData.loan_type}
                onChange={handleChange('loan_type')}
                inputProps={{ 'aria-label': 'Loan type' }}
              >
                <MenuItem value="conventional">Conventional</MenuItem>
                <MenuItem value="fha">FHA</MenuItem>
                <MenuItem value="va">VA</MenuItem>
                <MenuItem value="usda">USDA</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Estimated Interest Rate"
                value={formData.estimated_rate}
                onChange={handleChange('estimated_rate')}
                InputProps={{ endAdornment: '%' }}
                inputProps={{ 'aria-label': 'Estimated interest rate', min: 0, step: 0.125 }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                required
                type="number"
                label="Max Loan Amount"
                value={formData.max_loan_amount}
                onChange={handleChange('max_loan_amount')}
                InputProps={{ startAdornment: '$' }}
                helperText="Auto-calculated from property value minus down payment"
                inputProps={{ 'aria-label': 'Maximum loan amount', min: 0 }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                required
                type="number"
                label="Max Purchase Price"
                value={formData.max_purchase_price}
                onChange={handleChange('max_purchase_price')}
                InputProps={{ startAdornment: '$' }}
                inputProps={{ 'aria-label': 'Maximum purchase price', min: 0 }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                required
                type="date"
                label="Expiration Date"
                value={formData.expiration_date}
                onChange={handleChange('expiration_date')}
                InputLabelProps={{ shrink: true }}
                helperText="Pre-approval valid until this date"
                inputProps={{ 'aria-label': 'Expiration date' }}
              />
            </Grid>
          </Grid>
        );

      case 3:
        return (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Special Conditions"
                value={formData.conditions}
                onChange={handleChange('conditions')}
                multiline
                rows={4}
                helperText="Any special conditions or requirements (will be shown on letter)"
                inputProps={{ 'aria-label': 'Special conditions' }}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Internal Notes"
                value={formData.internal_notes}
                onChange={handleChange('internal_notes')}
                multiline
                rows={4}
                helperText="Internal notes (NOT shown on letter)"
                inputProps={{ 'aria-label': 'Internal notes' }}
              />
            </Grid>
            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Typography variant="h6" gutterBottom>
                Review Summary
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="body2" color="text.secondary">
                    Borrower:
                  </Typography>
                  <Typography variant="body1" fontWeight={600}>
                    {formData.borrower_name}
                    {formData.co_borrower_name && ` & ${formData.co_borrower_name}`}
                  </Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="body2" color="text.secondary">
                    Max Loan Amount:
                  </Typography>
                  <Typography variant="body1" fontWeight={600} color="primary.main">
                    ${formData.max_loan_amount?.toLocaleString()}
                  </Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="body2" color="text.secondary">
                    Loan Type:
                  </Typography>
                  <Typography variant="body1" fontWeight={600}>
                    {formData.loan_type?.toUpperCase()}
                  </Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="body2" color="text.secondary">
                    Back-End DTI:
                  </Typography>
                  <Typography variant="body1" fontWeight={600}>
                    {formData.back_end_dti?.toFixed(1)}%
                  </Typography>
                </Grid>
              </Grid>
            </Grid>
          </Grid>
        );

      default:
        return null;
    }
  };

  if (loading && !formData.id) {
    return (
      <>
        <Navbar title="Pre-Approval Letter" />
        <Box
          sx={{
            minHeight: 'calc(100vh - 64px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <CircularProgress />
        </Box>
      </>
    );
  }

  return (
    <>
      <Navbar title="Pre-Approval Letter" />
      <Box
        sx={{
          minHeight: 'calc(100vh - 64px)',
          width: '100%',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          py: { xs: 2, sm: 3, md: 4 },
          px: { xs: 1, sm: 2, md: 3 },
        }}
      >
        <Container maxWidth="lg">
          {/* Header */}
          <Box textAlign="center" mb={4}>
            <Typography
              variant="h3"
              component="h1"
              gutterBottom
              sx={{
                color: 'white',
                fontWeight: 700,
                fontSize: { xs: '1.75rem', sm: '2.5rem', md: '3rem' },
              }}
            >
              Pre-Approval Letter Generator
            </Typography>
            <Typography
              variant="h6"
              sx={{
                color: 'white',
                opacity: 0.9,
                fontSize: { xs: '1rem', sm: '1.125rem', md: '1.25rem' },
              }}
            >
              Create and manage pre-approval letters for borrowers
            </Typography>
          </Box>

          {/* Alerts */}
          {error && (
            <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 3 }}>
              <AlertTitle>Error</AlertTitle>
              {error}
            </Alert>
          )}
          {success && (
            <Alert severity="success" onClose={() => setSuccess(null)} sx={{ mb: 3 }}>
              <AlertTitle>Success</AlertTitle>
              {success}
            </Alert>
          )}

          {/* Stepper */}
          <Paper sx={{ mb: 3, p: 3 }}>
            <Stepper activeStep={activeStep} alternativeLabel>
              {steps.map((label) => (
                <Step key={label}>
                  <StepLabel>{label}</StepLabel>
                </Step>
              ))}
            </Stepper>
          </Paper>

          {/* Form Content */}
          <Paper sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
            {renderStepContent(activeStep)}

            {/* Navigation Buttons */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
              <Button
                disabled={activeStep === 0}
                onClick={handleBack}
                variant="outlined"
                aria-label="Go to previous step"
              >
                Back
              </Button>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button
                  variant="outlined"
                  startIcon={<SaveIcon />}
                  onClick={() => handleSave('draft')}
                  disabled={loading}
                  aria-label="Save as draft"
                >
                  Save Draft
                </Button>
                {activeStep === steps.length - 1 ? (
                  <>
                    {formData.id && (
                      <Button
                        variant="outlined"
                        startIcon={<PreviewIcon />}
                        onClick={handlePreview}
                        disabled={loading}
                        aria-label="Preview letter"
                      >
                        Preview Letter
                      </Button>
                    )}
                    <Button
                      variant="contained"
                      startIcon={<SendIcon />}
                      onClick={() => handleSave('submitted')}
                      disabled={loading}
                      aria-label="Submit pre-approval"
                    >
                      Submit
                    </Button>
                  </>
                ) : (
                  <Button
                    variant="contained"
                    onClick={handleNext}
                    aria-label="Go to next step"
                  >
                    Next
                  </Button>
                )}
              </Box>
            </Box>
          </Paper>
        </Container>
      </Box>

      {/* Letter Preview Dialog */}
      <Dialog
        open={previewOpen}
        onClose={() => setPreviewOpen(false)}
        maxWidth="md"
        fullWidth
        aria-labelledby="letter-preview-dialog"
      >
        <DialogTitle id="letter-preview-dialog">
          Pre-Approval Letter Preview
        </DialogTitle>
        <DialogContent>
          <Box
            sx={{
              border: '1px solid #ccc',
              borderRadius: 1,
              p: 2,
              maxHeight: '70vh',
              overflow: 'auto',
            }}
            dangerouslySetInnerHTML={{ __html: previewHtml }}
          />
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => setPreviewOpen(false)}
            startIcon={<CloseIcon />}
            aria-label="Close preview"
          >
            Close
          </Button>
          {formData.status === 'approved' && (
            <Button
              onClick={handlePublish}
              variant="contained"
              startIcon={<CheckIcon />}
              disabled={loading}
              aria-label="Publish letter"
            >
              Publish Letter
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </>
  );
};

export default PreApprovalPage;
