import { useState } from 'react';
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
  Card,
  CardContent,
} from '@mui/material';
import { propertyApi, calculateQualification } from '../services/api';
import type { PropertyLookupResponse } from '../services/api';

interface UploadedFiles {
  paystub: File[];
  w2: File[];
  tax: File[];
}

const steps = ['Property Address', 'Loan Details', 'Upload Documents', 'Other Debts', 'Results'];

const MortgageApplication = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('');

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
    setLoadingMessage('Looking up property...');

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

      setLoading(false);
    } catch (error) {
      setLoading(false);
      alert('Error looking up property: ' + (error as Error).message);
      console.error('Property lookup error:', error);
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
    setLoadingMessage('Processing your application...');

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
      setLoading(false);
    } catch (error) {
      setLoading(false);
      alert('Error calculating qualification: ' + (error as Error).message);
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

            <Alert severity="info" sx={{ mb: 3 }}>
              <strong>💡 Smart Lookup:</strong> Enter the property address and we'll automatically retrieve:
              <ul style={{ marginTop: 10, marginLeft: 20 }}>
                <li>Property tax rates</li>
                <li>Transfer tax rates</li>
                <li>Recording fees</li>
                <li>Insurance estimates</li>
                <li>County jurisdiction</li>
              </ul>
            </Alert>

            <Button variant="contained" size="large" onClick={lookupProperty} sx={{ mb: 3 }}>
              🔍 Look Up Property
            </Button>

            {propertyData && (
              <Card sx={{ mt: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom color="primary">
                    📍 Property Information
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Address:</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2">{propertyData.address.formatted_address}</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">County:</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2">{propertyData.address.county} County, {propertyData.address.state}</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Property Tax Rate:</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2">{(propertyData.tax_rate * 100).toFixed(3)}%</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Est. Monthly Property Tax:</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2">${propertyTaxMonthly.toFixed(2)}</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Est. Monthly Insurance:</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2">${insuranceMonthly.toFixed(2)}</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Data Confidence:</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2">{propertyData.confidence_score}% ✓</Typography>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            )}

            {propertyData && (
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 3 }}>
                <Button variant="contained" size="large" onClick={handleNext}>
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

            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
              <Button onClick={handleBack}>← Back</Button>
              <Button variant="contained" size="large" onClick={handleNext}>
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

            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
              <Button onClick={handleBack}>← Back</Button>
              <Button variant="contained" size="large" onClick={handleNext}>
                Next: Other Debts →
              </Button>
            </Box>
          </Box>
        );

      case 3:
        return (
          <Box>
            <Typography variant="h5" gutterBottom>
              Step 4: Other Monthly Debts
            </Typography>
            <Typography color="text.secondary" sx={{ mb: 4 }}>
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
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Student Loans"
                  type="number"
                  value={studentLoans}
                  onChange={(e) => setStudentLoans(Number(e.target.value))}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Credit Card Minimum Payments"
                  type="number"
                  value={creditCards}
                  onChange={(e) => setCreditCards(Number(e.target.value))}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Personal Loans"
                  type="number"
                  value={personalLoans}
                  onChange={(e) => setPersonalLoans(Number(e.target.value))}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Other Monthly Debts"
                  type="number"
                  value={otherDebts}
                  onChange={(e) => setOtherDebts(Number(e.target.value))}
                />
              </Grid>
            </Grid>

            <Alert severity="info" sx={{ mt: 3 }}>
              <strong>Important:</strong> Include all recurring monthly payments. These are used to calculate your
              debt-to-income ratio.
            </Alert>

            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
              <Button onClick={handleBack}>← Back</Button>
              <Button variant="contained" size="large" onClick={calculateQualificationResult}>
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

                <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', mt: 4 }}>
                  <Button variant="contained" onClick={() => window.print()}>
                    Print Results 🖨️
                  </Button>
                  <Button variant="outlined" onClick={() => window.location.reload()}>
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
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        py: 4,
      }}
    >
      <Container maxWidth="lg">
        <Box textAlign="center" mb={4}>
          <Typography variant="h3" component="h1" gutterBottom sx={{ color: 'white', fontWeight: 700 }}>
            🏠 Mortgage Application
          </Typography>
          <Typography variant="h6" sx={{ color: 'white', opacity: 0.9 }}>
            Smart qualification system with automatic property lookup
          </Typography>
        </Box>

        <Stepper activeStep={activeStep} sx={{ mb: 4, bgcolor: 'white', borderRadius: 2, p: 3 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        <Paper sx={{ p: 4, minHeight: '600px' }}>{renderStepContent()}</Paper>
      </Container>

      <Dialog open={loading} PaperProps={{ sx: { p: 4, textAlign: 'center' } }}>
        <DialogContent>
          <CircularProgress size={60} sx={{ mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            Processing...
          </Typography>
          <Typography color="text.secondary">{loadingMessage}</Typography>
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default MortgageApplication;
