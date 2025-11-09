import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Box,
  Typography,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Checkbox,
  FormControlLabel,
  Paper,
  Stepper,
  Step,
  StepLabel,
  Grid,
  Alert,
  CircularProgress,
  Dialog,
  DialogContent,
  DialogTitle,
  DialogActions,
  Card,
  CardContent,
  Chip,
  Tooltip,
  IconButton,
  LinearProgress,
  Snackbar,
} from '@mui/material';
import HomeIcon from '@mui/icons-material/Home';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import VerifiedUserIcon from '@mui/icons-material/VerifiedUser';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import SaveIcon from '@mui/icons-material/Save';
import RestoreIcon from '@mui/icons-material/Restore';
import DeleteIcon from '@mui/icons-material/Delete';
import { propertyApi, calculateQualification } from '../services/api';
import type { PropertyLookupResponse } from '../services/api';
import Navbar from '../components/Navbar';

interface UploadedFiles {
  paystub: File[];
  w2: File[];
  tax: File[];
}

const steps = ['Property Address', 'Loan Details', 'Upload Documents', 'Other Debts', 'Results'];

const DRAFT_KEY = 'mortgage_application_draft';
const DRAFT_TIMESTAMP_KEY = 'mortgage_application_draft_timestamp';

const MortgageApplication = () => {
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('');

  // Save/Resume state
  const [showResumeDialog, setShowResumeDialog] = useState(false);
  const [showSaveNotification, setShowSaveNotification] = useState(false);
  const [draftLastSaved, setDraftLastSaved] = useState<Date | null>(null);

  // Step 1: Property Address
  const [propertyAddress, setPropertyAddress] = useState('');
  const [propertyData, setPropertyData] = useState<PropertyLookupResponse | null>(null);

  // Step 2: Loan Details
  const [propertyValue, setPropertyValue] = useState(500000);
  const [loanAmount, setLoanAmount] = useState(400000);
  const [interestRate, setInterestRate] = useState(6.5);
  const [loanTerm, setLoanTerm] = useState(30);
  const [loanType, setLoanType] = useState('fannie_mae');
  const [creditScore, setCreditScore] = useState(740);
  const [propertyType, setPropertyType] = useState('resale');
  const [firstTimeBuyer, setFirstTimeBuyer] = useState(false);
  const [propertyTaxMonthly, setPropertyTaxMonthly] = useState(0);
  const [insuranceMonthly, setInsuranceMonthly] = useState(0);
  const [hoaFees, setHoaFees] = useState(0);

  // Step 3: Documents
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFiles>({
    paystub: [],
    w2: [],
    tax: [],
  });

  // Step 4: Debts
  const [carPayments, setCarPayments] = useState(0);
  const [studentLoans, setStudentLoans] = useState(0);
  const [creditCards, setCreditCards] = useState(0);
  const [personalLoans, setPersonalLoans] = useState(0);
  const [otherDebts, setOtherDebts] = useState(0);

  // Step 5: Results
  const [qualificationResults, setQualificationResults] = useState<any>(null);

  // Snackbar state
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');

  // Check for existing draft on mount
  useEffect(() => {
    const draftData = localStorage.getItem(DRAFT_KEY);
    const draftTimestamp = localStorage.getItem(DRAFT_TIMESTAMP_KEY);

    if (draftData && draftTimestamp) {
      const savedDate = new Date(draftTimestamp);
      const hoursSinceSave = (Date.now() - savedDate.getTime()) / (1000 * 60 * 60);

      // Only show resume dialog if draft is less than 7 days old
      if (hoursSinceSave < 168) {
        setDraftLastSaved(savedDate);
        setShowResumeDialog(true);
      } else {
        // Clear old drafts
        localStorage.removeItem(DRAFT_KEY);
        localStorage.removeItem(DRAFT_TIMESTAMP_KEY);
      }
    }
  }, []);

  // Auto-save draft whenever form data changes
  useEffect(() => {
    // Don't auto-save if we're on the results step or if form is empty
    if (activeStep === steps.length - 1 || !propertyAddress) {
      return;
    }

    const draftData = {
      activeStep,
      propertyAddress,
      propertyValue,
      loanAmount,
      interestRate,
      loanTerm,
      loanType,
      creditScore,
      propertyType,
      firstTimeBuyer,
      propertyTaxMonthly,
      insuranceMonthly,
      hoaFees,
      carPayments,
      studentLoans,
      creditCards,
      personalLoans,
      otherDebts,
    };

    localStorage.setItem(DRAFT_KEY, JSON.stringify(draftData));
    localStorage.setItem(DRAFT_TIMESTAMP_KEY, new Date().toISOString());
  }, [
    activeStep,
    propertyAddress,
    propertyValue,
    loanAmount,
    interestRate,
    loanTerm,
    loanType,
    creditScore,
    propertyType,
    firstTimeBuyer,
    propertyTaxMonthly,
    insuranceMonthly,
    hoaFees,
    carPayments,
    studentLoans,
    creditCards,
    personalLoans,
    otherDebts,
  ]);

  const loadDraft = () => {
    const draftData = localStorage.getItem(DRAFT_KEY);
    if (draftData) {
      const draft = JSON.parse(draftData);
      setActiveStep(draft.activeStep || 0);
      setPropertyAddress(draft.propertyAddress || '');
      setPropertyValue(draft.propertyValue || 500000);
      setLoanAmount(draft.loanAmount || 400000);
      setInterestRate(draft.interestRate || 6.5);
      setLoanTerm(draft.loanTerm || 30);
      setLoanType(draft.loanType || 'fannie_mae');
      setCreditScore(draft.creditScore || 740);
      setPropertyType(draft.propertyType || 'resale');
      setFirstTimeBuyer(draft.firstTimeBuyer || false);
      setPropertyTaxMonthly(draft.propertyTaxMonthly || 0);
      setInsuranceMonthly(draft.insuranceMonthly || 0);
      setHoaFees(draft.hoaFees || 0);
      setCarPayments(draft.carPayments || 0);
      setStudentLoans(draft.studentLoans || 0);
      setCreditCards(draft.creditCards || 0);
      setPersonalLoans(draft.personalLoans || 0);
      setOtherDebts(draft.otherDebts || 0);
    }
    setShowResumeDialog(false);
  };

  const clearDraft = () => {
    localStorage.removeItem(DRAFT_KEY);
    localStorage.removeItem(DRAFT_TIMESTAMP_KEY);
    setDraftLastSaved(null);
    setShowResumeDialog(false);
  };

  const handleSaveAndExit = () => {
    setShowSaveNotification(true);
    setTimeout(() => {
      navigate('/');
    }, 1500);
  };

  const handleNext = () => {
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  const lookupProperty = async () => {
    if (!propertyAddress) {
      alert('Please enter a property address');
      return;
    }

    setLoading(true);
    setLoadingMessage('Looking up property data... This may take 10-20 seconds if we need to search government websites.');

    try {
      const data = await propertyApi.lookup(propertyAddress);

      // Calculate monthly costs
      let monthlyTax = data.monthly_property_tax;
      if (!monthlyTax && data.tax_rate) {
        monthlyTax = (propertyValue * data.tax_rate) / 12;
      } else if (!monthlyTax) {
        monthlyTax = (propertyValue * 0.012) / 12;
      }

      let monthlyInsurance = data.insurance_estimate;
      if (!monthlyInsurance) {
        monthlyInsurance = ((propertyValue / 100000) * 650) / 12;
      }

      setPropertyData(data);
      setPropertyTaxMonthly(monthlyTax);
      setInsuranceMonthly(monthlyInsurance);
    } catch (error) {
      alert('Error looking up property: ' + (error as Error).message);
      console.error('Property lookup error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = (type: keyof UploadedFiles, files: FileList | null) => {
    if (files) {
      setUploadedFiles((prev) => ({
        ...prev,
        [type]: Array.from(files),
      }));
    }
  };

  const removeFile = (type: keyof UploadedFiles, index: number) => {
    setUploadedFiles((prev) => ({
      ...prev,
      [type]: prev[type].filter((_, i) => i !== index),
    }));
  };

  const calculateQualificationResult = async () => {
    if (uploadedFiles.paystub.length === 0 || uploadedFiles.w2.length === 0) {
      alert('Please upload at least one paystub and one W-2 form');
      return;
    }

    setLoading(true);
    setLoadingMessage('Processing your application and calculating qualification...');

    try {
      // Mock monthly income (in production, this would come from OCR extraction)
      const monthlyIncome = 8000;

      const result = await calculateQualification({
        propertyValue,
        loanAmount,
        interestRate,
        loanTerm,
        propertyTax: propertyTaxMonthly,
        insurance: insuranceMonthly,
        hoaFees,
        monthlyIncome,
        carPayments,
        studentLoans,
        creditCards,
        personalLoans,
        otherDebts,
      });

      setQualificationResults(result);
      setActiveStep(4);
    } catch (error) {
      alert('Error calculating qualification: ' + (error as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitApplication = async () => {
    if (!qualificationResults) {
      alert('Please calculate qualification first');
      return;
    }

    try {
      setLoading(true);
      setLoadingMessage('Submitting your application...');

      // TODO: Replace with actual API call when backend is ready
      // const response = await fetch('http://localhost:8004/api/loan-estimates/', {
      //   method: 'POST',
      //   headers: {
      //     'Content-Type': 'application/json',
      //     'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      //   },
      //   body: JSON.stringify({
      //     property_address: propertyAddress,
      //     property_value: propertyValue,
      //     loan_amount: loanAmount,
      //     status: 'submitted',
      //     calculation_results: qualificationResults
      //   })
      // });

      // Mock successful submission
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Clear draft from localStorage
      localStorage.removeItem('mortgage_application_draft');
      localStorage.removeItem('mortgage_application_draft_timestamp');

      // Show success message
      setSnackbarMessage('Application submitted successfully!');
      setSnackbarOpen(true);

      // Navigate to My Applications after a short delay
      setTimeout(() => {
        navigate('/my-applications');
      }, 1500);
    } catch (error) {
      alert('Error submitting application: ' + (error as Error).message);
      setLoading(false);
    }
  };

  const getTransferTaxScenario = () => {
    if (propertyType === 'new_construction') {
      if (firstTimeBuyer) {
        return {
          title: 'Scenario 4: New Construction (First-Time Buyer)',
          description: [
            'Buyer pays 100% of transfer taxes and recording fees',
            'First-time buyer exemption does NOT apply to new construction',
            'Includes: State transfer tax + County transfer tax + Recording fees + Recordation tax',
          ],
        };
      } else {
        return {
          title: 'Scenario 1: New Construction',
          description: [
            'Buyer pays 100% of transfer taxes and recording fees',
            'Includes: State transfer tax + County transfer tax + Recording fees + Recordation tax',
          ],
        };
      }
    } else {
      if (firstTimeBuyer) {
        return {
          title: 'Scenario 3: Resale (First-Time Buyer)',
          description: [
            '50/50 split on transfer taxes between buyer and seller',
            'State transfer tax EXEMPT (up to $500k home value)',
            'Buyer pays recording fees and recordation tax',
            '💰 You save on state transfer tax!',
          ],
          savings: true,
        };
      } else {
        return {
          title: 'Scenario 2: Resale (Standard)',
          description: [
            '50/50 split on transfer taxes between buyer and seller',
            'Buyer pays recording fees and recordation tax',
            'More affordable than new construction',
          ],
        };
      }
    }
  };

  const renderStepContent = () => {
    switch (activeStep) {
      case 0:
        return (
          <Box>
            <Typography variant="h5" gutterBottom>
              Step 1: Enter Property Address
            </Typography>
            <Typography color="text.secondary" sx={{ mb: 4 }}>
              We'll automatically look up property taxes and fees
            </Typography>

            <TextField
              fullWidth
              label="Property Address"
              value={propertyAddress}
              onChange={(e) => setPropertyAddress(e.target.value)}
              placeholder="123 Main Street, Rockville, MD 20850"
              sx={{ mb: 3 }}
            />

            <Alert
              severity="info"
              sx={{
                mb: 3,
                '& ul': {
                  marginTop: 1,
                  marginBottom: 0,
                  paddingLeft: { xs: 2, sm: 3 },
                },
                '& li': {
                  fontSize: { xs: '0.875rem', sm: '1rem' },
                },
              }}
            >
              <strong>💡 Smart Lookup:</strong> Enter the property address and we'll automatically retrieve:
              <ul>
                <li>Property tax rates</li>
                <li>Transfer tax rates</li>
                <li>Recording fees</li>
                <li>Insurance estimates</li>
                <li>County jurisdiction</li>
              </ul>
            </Alert>

            <Button
              variant="contained"
              size="large"
              onClick={lookupProperty}
              disabled={!propertyAddress.trim()}
              fullWidth={true}
              sx={{
                mb: 3,
                py: { xs: 1.5, sm: 2 },
                fontSize: { xs: '1rem', sm: '1.125rem' },
              }}
            >
              🔍 Look Up Property
            </Button>

            {propertyData && (
              <Card sx={{ mt: 3, bgcolor: '#f8fdf9' }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom color="primary" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <span>📍</span>
                    <span>Property Information</span>
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6} md={4}>
                      <Box sx={{ bgcolor: 'white', p: 2, borderRadius: 1, height: '100%' }}>
                        <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                          Address
                        </Typography>
                        <Typography variant="body2" fontWeight={600}>
                          {propertyData.address.formatted_address}
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={4}>
                      <Box sx={{ bgcolor: 'white', p: 2, borderRadius: 1, height: '100%' }}>
                        <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                          County
                        </Typography>
                        <Typography variant="body2" fontWeight={600}>
                          {propertyData.address.county} County, {propertyData.address.state}
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={4}>
                      <Box sx={{ bgcolor: 'white', p: 2, borderRadius: 1, height: '100%' }}>
                        <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                          Property Tax Rate
                        </Typography>
                        <Typography variant="h6" color="primary" fontWeight={700}>
                          {(propertyData.tax_rate * 100).toFixed(3)}%
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={4}>
                      <Box sx={{ bgcolor: 'white', p: 2, borderRadius: 1, height: '100%' }}>
                        <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                          Monthly Property Tax
                        </Typography>
                        <Typography variant="h6" color="success.main" fontWeight={700}>
                          ${propertyTaxMonthly.toFixed(2)}
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={4}>
                      <Box sx={{ bgcolor: 'white', p: 2, borderRadius: 1, height: '100%' }}>
                        <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                          Monthly Insurance
                        </Typography>
                        <Typography variant="h6" color="success.main" fontWeight={700}>
                          ${insuranceMonthly.toFixed(2)}
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12} sm={6} md={4}>
                      <Box sx={{ bgcolor: 'white', p: 2, borderRadius: 1, height: '100%' }}>
                        <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                          Data Confidence
                        </Typography>
                        <Typography variant="h6" color="primary" fontWeight={700}>
                          {propertyData.confidence_score}% ✓
                        </Typography>
                      </Box>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            )}

            {propertyData && (
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 3 }}>
                <Button
                  variant="contained"
                  size="large"
                  onClick={handleNext}
                  fullWidth={true}
                  sx={{
                    py: { xs: 1.5, sm: 2 },
                    fontSize: { xs: '1rem', sm: '1.125rem' },
                  }}
                >
                  Next: Loan Details →
                </Button>
              </Box>
            )}
          </Box>
        );

      case 1:
        const scenario = getTransferTaxScenario();
        return (
          <Box>
            <Typography variant="h5" gutterBottom>
              Step 2: Loan Details
            </Typography>
            <Typography color="text.secondary" sx={{ mb: 4 }}>
              Property costs are auto-filled from our database
            </Typography>

            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Property Value / Purchase Price"
                  type="number"
                  value={propertyValue}
                  onChange={(e) => setPropertyValue(Number(e.target.value))}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Loan Amount"
                  type="number"
                  value={loanAmount}
                  onChange={(e) => setLoanAmount(Number(e.target.value))}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Interest Rate (%)"
                  type="number"
                  inputProps={{ step: 0.01 }}
                  value={interestRate}
                  onChange={(e) => setInterestRate(Number(e.target.value))}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Loan Term</InputLabel>
                  <Select value={loanTerm} label="Loan Term" onChange={(e) => setLoanTerm(Number(e.target.value))}>
                    <MenuItem value={15}>15 Years</MenuItem>
                    <MenuItem value={20}>20 Years</MenuItem>
                    <MenuItem value={30}>30 Years</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Loan Type</InputLabel>
                  <Select value={loanType} label="Loan Type" onChange={(e) => setLoanType(e.target.value)}>
                    <MenuItem value="fannie_mae">Fannie Mae (Conventional)</MenuItem>
                    <MenuItem value="fha">FHA (Government)</MenuItem>
                    <MenuItem value="va">VA (Veterans)</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Credit Score"
                  type="number"
                  value={creditScore}
                  onChange={(e) => setCreditScore(Number(e.target.value))}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Property Type</InputLabel>
                  <Select value={propertyType} label="Property Type" onChange={(e) => setPropertyType(e.target.value)}>
                    <MenuItem value="resale">Resale / Existing Home</MenuItem>
                    <MenuItem value="new_construction">New Construction</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Checkbox checked={firstTimeBuyer} onChange={(e) => setFirstTimeBuyer(e.target.checked)} />
                  }
                  label="First-Time Home Buyer"
                />
                <Typography variant="caption" display="block" color="text.secondary">
                  ✓ May qualify for state transfer tax exemption (resale only)
                </Typography>
              </Grid>
            </Grid>

            {(propertyType || firstTimeBuyer) && (
              <Alert severity={scenario.savings ? 'success' : 'info'} sx={{ mt: 3 }}>
                <strong>💰 Transfer Tax Scenario:</strong>
                <Typography variant="body2" sx={{ mt: 1 }}>
                  <strong>{scenario.title}</strong>
                </Typography>
                <ul style={{ marginTop: 8, marginLeft: 20 }}>
                  {scenario.description.map((item, index) => (
                    <li key={index}>{item}</li>
                  ))}
                </ul>
              </Alert>
            )}

            <Typography variant="h6" sx={{ mt: 4, mb: 2 }}>
              Monthly Property Costs
            </Typography>

            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Monthly Property Tax ✓ Auto-filled"
                  type="number"
                  value={propertyTaxMonthly}
                  InputProps={{ readOnly: true }}
                  sx={{ bgcolor: '#ecfdf5' }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Monthly Insurance ✓ Auto-filled"
                  type="number"
                  value={insuranceMonthly}
                  InputProps={{ readOnly: true }}
                  sx={{ bgcolor: '#ecfdf5' }}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Monthly HOA Fees (if applicable)"
                  type="number"
                  value={hoaFees}
                  onChange={(e) => setHoaFees(Number(e.target.value))}
                />
              </Grid>
            </Grid>

            {propertyData && (
              <Alert severity="success" sx={{ mt: 3 }}>
                <strong>✓ Property costs auto-filled</strong> from our database based on the property address.
                These values are calculated using current tax rates for {propertyData.address.county} County.
              </Alert>
            )}

            <Box
              sx={{
                display: 'flex',
                flexDirection: { xs: 'column', sm: 'row' },
                justifyContent: 'space-between',
                gap: 2,
                mt: 4,
              }}
            >
              <Button
                onClick={handleBack}
                sx={{
                  order: { xs: 2, sm: 1 },
                  py: { xs: 1.5, sm: 1 },
                }}
              >
                ← Back
              </Button>
              <Button
                variant="contained"
                size="large"
                onClick={handleNext}
                sx={{
                  order: { xs: 1, sm: 2 },
                  py: { xs: 1.5, sm: 2 },
                  fontSize: { xs: '1rem', sm: '1.125rem' },
                }}
              >
                Next: Upload Documents →
              </Button>
            </Box>
          </Box>
        );

      case 2:
        return (
          <Box>
            <Typography variant="h5" gutterBottom>
              Step 3: Upload Income Documents
            </Typography>
            <Typography color="text.secondary" sx={{ mb: 4 }}>
              Upload documents to verify your income
            </Typography>

            {['paystub', 'w2', 'tax'].map((type) => (
              <Box key={type} sx={{ mb: 4 }}>
                <Typography variant="subtitle1" gutterBottom>
                  {type === 'paystub' && 'Pay Stubs (Recent 2 months) *Required'}
                  {type === 'w2' && 'W-2 Forms (Recent 2 years) *Required'}
                  {type === 'tax' && 'Tax Returns (Optional - for self-employed)'}
                </Typography>
                <Paper
                  sx={{
                    p: 4,
                    textAlign: 'center',
                    border: '3px dashed #667eea',
                    cursor: 'pointer',
                    '&:hover': {
                      bgcolor: '#f8f9ff',
                      borderColor: '#764ba2',
                    },
                  }}
                  onClick={() => document.getElementById(`${type}-input`)?.click()}
                >
                  <Typography variant="h3">📄</Typography>
                  <Typography>Click to upload or drag and drop documents</Typography>
                  <Typography variant="caption" color="text.secondary">
                    PDF, JPG, PNG (Max 10MB each)
                  </Typography>
                </Paper>
                <input
                  id={`${type}-input`}
                  type="file"
                  multiple
                  accept="image/*,application/pdf"
                  style={{ display: 'none' }}
                  onChange={(e) => handleFileUpload(type as keyof UploadedFiles, e.target.files)}
                />
                {uploadedFiles[type as keyof UploadedFiles].map((file, index) => (
                  <Paper key={index} sx={{ p: 1, mt: 1, display: 'flex', justifyContent: 'space-between' }}>
                    <Typography>{file.name}</Typography>
                    <Button size="small" color="error" onClick={() => removeFile(type as keyof UploadedFiles, index)}>
                      ✕
                    </Button>
                  </Paper>
                ))}
              </Box>
            ))}

            <Alert severity="info">
              <strong>Note:</strong> Documents will be processed using AI OCR to extract income information
              automatically. All data is encrypted and secure.
            </Alert>

            <Box
              sx={{
                display: 'flex',
                flexDirection: { xs: 'column', sm: 'row' },
                justifyContent: 'space-between',
                gap: 2,
                mt: 4,
              }}
            >
              <Button
                onClick={handleBack}
                sx={{
                  order: { xs: 2, sm: 1 },
                  py: { xs: 1.5, sm: 1 },
                }}
              >
                ← Back
              </Button>
              <Button
                variant="contained"
                size="large"
                onClick={handleNext}
                sx={{
                  order: { xs: 1, sm: 2 },
                  py: { xs: 1.5, sm: 2 },
                  fontSize: { xs: '1rem', sm: '1.125rem' },
                }}
              >
                Next: Other Debts →
              </Button>
            </Box>
          </Box>
        );

      case 3:
        return (
          <Box>
            <Typography variant="h5" gutterBottom sx={{ fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2rem' } }}>
              Step 4: Other Monthly Debts
            </Typography>
            <Typography color="text.secondary" sx={{ mb: 4, fontSize: { xs: '0.875rem', sm: '1rem' } }}>
              Enter your monthly debt obligations
            </Typography>

            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Car Payments"
                  type="number"
                  value={carPayments}
                  onChange={(e) => setCarPayments(Number(e.target.value))}
                  inputProps={{ min: 0, step: 1 }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Student Loans"
                  type="number"
                  value={studentLoans}
                  onChange={(e) => setStudentLoans(Number(e.target.value))}
                  inputProps={{ min: 0, step: 1 }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Credit Card Minimum Payments"
                  type="number"
                  value={creditCards}
                  onChange={(e) => setCreditCards(Number(e.target.value))}
                  inputProps={{ min: 0, step: 1 }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Personal Loans"
                  type="number"
                  value={personalLoans}
                  onChange={(e) => setPersonalLoans(Number(e.target.value))}
                  inputProps={{ min: 0, step: 1 }}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Other Monthly Debts"
                  type="number"
                  value={otherDebts}
                  onChange={(e) => setOtherDebts(Number(e.target.value))}
                  inputProps={{ min: 0, step: 1 }}
                />
              </Grid>
            </Grid>

            <Alert severity="info" sx={{ mt: 3, fontSize: { xs: '0.875rem', sm: '1rem' } }}>
              <strong>Important:</strong> Include all recurring monthly payments. These are used to calculate your
              debt-to-income ratio.
            </Alert>

            <Box
              sx={{
                display: 'flex',
                flexDirection: { xs: 'column', sm: 'row' },
                justifyContent: 'space-between',
                gap: 2,
                mt: 4,
              }}
            >
              <Button
                onClick={handleBack}
                sx={{
                  order: { xs: 2, sm: 1 },
                  py: { xs: 1.5, sm: 1 },
                }}
              >
                ← Back
              </Button>
              <Button
                variant="contained"
                size="large"
                onClick={calculateQualificationResult}
                sx={{
                  order: { xs: 1, sm: 2 },
                  py: { xs: 1.5, sm: 2 },
                  fontSize: { xs: '1rem', sm: '1.125rem' },
                }}
              >
                Submit Application 🚀
              </Button>
            </Box>
          </Box>
        );

      case 4:
        return (
          <Box>
            {qualificationResults && (
              <>
                <Alert severity={qualificationResults.qualified ? 'success' : 'error'} sx={{ mb: 3 }}>
                  <Typography variant="h5">
                    {qualificationResults.qualified ? '✅ Congratulations! You Qualify' : '❌ Not Qualified'}
                  </Typography>
                  <Typography>
                    {qualificationResults.qualified
                      ? `You qualify for ${qualificationResults.qualified_loan_types.length} loan type(s)`
                      : 'Your DTI ratio exceeds maximum limits'}
                  </Typography>
                </Alert>

                <Card>
                  <CardContent>
                    <Typography variant="h6" color="primary" gutterBottom>
                      📊 Qualification Summary
                    </Typography>
                    <Grid container spacing={2}>
                      <Grid item xs={6}>
                        <Typography variant="body2" color="text.secondary">Monthly Income:</Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="body2">${qualificationResults.monthly_income.toFixed(0)}</Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="body2" color="text.secondary">Housing Payment:</Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="body2">${qualificationResults.housing_payment.toFixed(0)}</Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="body2" color="text.secondary">Front-End DTI:</Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="body2">{qualificationResults.front_end_dti.toFixed(2)}%</Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="body2" color="text.secondary">Back-End DTI:</Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="body2">{qualificationResults.back_end_dti.toFixed(2)}%</Typography>
                      </Grid>
                      <Grid item xs={12}>
                        <Typography variant="body2" color="text.secondary">Qualified Loan Types:</Typography>
                        <Typography variant="body2">{qualificationResults.qualified_loan_types.join(', ')}</Typography>
                      </Grid>
                    </Grid>

                    {qualificationResults.warnings.length > 0 && (
                      <Alert severity="warning" sx={{ mt: 2 }}>
                        {qualificationResults.warnings.map((warning: string, index: number) => (
                          <Typography key={index} variant="body2">• {warning}</Typography>
                        ))}
                      </Alert>
                    )}
                  </CardContent>
                </Card>

                <Box
                  sx={{
                    display: 'flex',
                    flexDirection: { xs: 'column', sm: 'row' },
                    gap: 2,
                    justifyContent: 'center',
                    mt: 4,
                  }}
                >
                  <Button
                    variant="contained"
                    color="success"
                    size="large"
                    onClick={handleSubmitApplication}
                    disabled={loading}
                    fullWidth={false}
                    sx={{
                      py: { xs: 1.5, sm: 1.5 },
                      minWidth: { sm: 240 },
                      fontSize: { xs: '1rem', sm: '1.125rem' },
                      fontWeight: 600,
                    }}
                  >
                    Submit Application ✓
                  </Button>
                  <Button
                    variant="contained"
                    onClick={() => window.print()}
                    fullWidth={false}
                    sx={{
                      py: { xs: 1.5, sm: 1 },
                      minWidth: { sm: 200 },
                    }}
                  >
                    Print Results 🖨️
                  </Button>
                  <Button
                    variant="outlined"
                    onClick={() => window.location.reload()}
                    fullWidth={false}
                    sx={{
                      py: { xs: 1.5, sm: 1 },
                      minWidth: { sm: 200 },
                    }}
                  >
                    New Application
                  </Button>
                </Box>
              </>
            )}
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <>
      {/* Navigation Bar */}
      <Navbar title="Mortgage Application" />

      <Box
        sx={{
          minHeight: 'calc(100vh - 64px)', // Subtract navbar height
          width: '100%',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          py: { xs: 2, sm: 3, md: 4 },
          px: { xs: 1, sm: 2, md: 3 },
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
          <Box textAlign="center" mb={{ xs: 2, sm: 3, md: 4 }}>
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
              🏠 Mortgage Application
            </Typography>
          <Typography
            variant="h6"
            sx={{
              color: 'white',
              opacity: 0.9,
              fontSize: { xs: '0.875rem', sm: '1rem', md: '1.25rem' },
            }}
          >
            Smart qualification system with automatic property lookup
          </Typography>

          {/* Trust Badges */}
          <Box
            sx={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: 2,
              justifyContent: 'center',
              alignItems: 'center',
              mt: 3,
            }}
          >
            <Chip
              icon={<VerifiedUserIcon />}
              label="Secure & Confidential"
              sx={{
                bgcolor: 'rgba(255,255,255,0.2)',
                color: 'white',
                backdropFilter: 'blur(10px)',
                fontWeight: 600,
              }}
            />
            <Chip
              icon={<HomeIcon />}
              label="All 50 States"
              sx={{
                bgcolor: 'rgba(255,255,255,0.2)',
                color: 'white',
                backdropFilter: 'blur(10px)',
                fontWeight: 600,
              }}
            />
            <Chip
              icon={<TrendingUpIcon />}
              label="Real-Time Data"
              sx={{
                bgcolor: 'rgba(255,255,255,0.2)',
                color: 'white',
                backdropFilter: 'blur(10px)',
                fontWeight: 600,
              }}
            />

            {/* Save & Exit Button */}
            {propertyAddress && activeStep < steps.length - 1 && (
              <Tooltip title="Save your progress and exit">
                <Button
                  onClick={handleSaveAndExit}
                  startIcon={<SaveIcon />}
                  size="small"
                  sx={{
                    bgcolor: 'rgba(255,255,255,0.25)',
                    color: 'white',
                    backdropFilter: 'blur(10px)',
                    fontWeight: 600,
                    '&:hover': {
                      bgcolor: 'rgba(255,255,255,0.35)',
                    },
                  }}
                >
                  Save & Exit
                </Button>
              </Tooltip>
            )}
          </Box>
        </Box>

        {/* Progress Indicator with Percentage */}
        <Box
          sx={{
            bgcolor: 'rgba(255,255,255,0.15)',
            backdropFilter: 'blur(10px)',
            borderRadius: 2,
            p: 2,
            mb: 3,
          }}
        >
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="body2" sx={{ color: 'white', fontWeight: 600 }}>
              Application Progress
            </Typography>
            <Typography variant="body2" sx={{ color: 'white', fontWeight: 600 }}>
              {Math.round(((activeStep + 1) / steps.length) * 100)}% Complete
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={((activeStep + 1) / steps.length) * 100}
            sx={{
              height: 8,
              borderRadius: 4,
              bgcolor: 'rgba(255,255,255,0.3)',
              '& .MuiLinearProgress-bar': {
                bgcolor: 'white',
                borderRadius: 4,
              },
            }}
          />
        </Box>

        <Stepper
          activeStep={activeStep}
          sx={{
            mb: { xs: 2, sm: 3, md: 4 },
            bgcolor: 'white',
            borderRadius: 2,
            p: { xs: 1.5, sm: 2, md: 3 },
            display: { xs: 'none', sm: 'flex' },
          }}
        >
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {/* Mobile Step Indicator */}
        <Box
          sx={{
            display: { xs: 'block', sm: 'none' },
            mb: 2,
            bgcolor: 'white',
            borderRadius: 2,
            p: 2,
            textAlign: 'center',
          }}
        >
          <Typography variant="body2" color="text.secondary">
            Step {activeStep + 1} of {steps.length}
          </Typography>
          <Typography variant="h6" color="primary">
            {steps[activeStep]}
          </Typography>
        </Box>

        <Paper
          sx={{
            p: { xs: 2, sm: 3, md: 4 },
            minHeight: { xs: '400px', sm: '500px', md: '600px' },
            width: '100%',
          }}
        >
          {renderStepContent()}
        </Paper>
      </Container>

      <Dialog
        open={loading}
        PaperProps={{
          sx: {
            p: { xs: 2, sm: 4 },
            textAlign: 'center',
            minWidth: { xs: '90%', sm: 400 },
            maxWidth: { xs: '95%', sm: 500 },
          },
        }}
      >
        <DialogContent>
          <CircularProgress size={60} sx={{ mb: 3, color: '#667eea' }} />
          <Typography
            variant="h6"
            gutterBottom
            color="primary"
            sx={{ fontSize: { xs: '1.125rem', sm: '1.25rem' } }}
          >
            Processing...
          </Typography>
          <Typography
            color="text.secondary"
            sx={{
              mb: 2,
              fontSize: { xs: '0.875rem', sm: '1rem' },
              px: { xs: 1, sm: 0 },
            }}
          >
            {loadingMessage}
          </Typography>
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{
              display: 'block',
              mt: 2,
              fontSize: { xs: '0.75rem', sm: '0.875rem' },
            }}
          >
            🤖 Using AI to search government databases...
          </Typography>
        </DialogContent>
      </Dialog>

      {/* Resume Draft Dialog */}
      <Dialog
        open={showResumeDialog}
        onClose={() => setShowResumeDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <RestoreIcon color="primary" />
            <Typography variant="h6">Resume Application?</Typography>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Typography variant="body1" gutterBottom>
            We found a saved application from{' '}
            <strong>
              {draftLastSaved?.toLocaleDateString()} at {draftLastSaved?.toLocaleTimeString()}
            </strong>
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            Would you like to continue where you left off or start fresh?
          </Typography>
        </DialogContent>
        <DialogActions sx={{ p: 2, gap: 1 }}>
          <Button
            onClick={clearDraft}
            startIcon={<DeleteIcon />}
            variant="outlined"
            color="error"
          >
            Start Fresh
          </Button>
          <Button
            onClick={loadDraft}
            startIcon={<RestoreIcon />}
            variant="contained"
            sx={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              '&:hover': {
                background: 'linear-gradient(135deg, #5568d3 0%, #63408b 100%)',
              },
            }}
          >
            Resume Application
          </Button>
        </DialogActions>
      </Dialog>

      {/* Save Notification */}
      <Snackbar
        open={showSaveNotification}
        autoHideDuration={1500}
        onClose={() => setShowSaveNotification(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity="success" sx={{ width: '100%' }}>
          Progress saved! Redirecting to home...
        </Alert>
      </Snackbar>
      </Box>
    </>
  );
};

export default MortgageApplication;
