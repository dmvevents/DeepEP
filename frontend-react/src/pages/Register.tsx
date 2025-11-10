import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  Alert,
  Link,
  Grid,
  Stepper,
  Step,
  StepLabel,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import AddressAutocomplete from '../components/AddressAutocomplete';
import {
  formatName,
  formatPhoneNumber,
  isValidName,
  isValidEmail,
  isValidPhone,
} from '../utils/formatters';

const steps = ['Account Info', 'Personal Details', 'Contact & Address'];

const Register = () => {
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState(0);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Step 1: Account Info
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // Step 2: Personal Details
  const [firstName, setFirstName] = useState('');
  const [middleName, setMiddleName] = useState('');
  const [lastName, setLastName] = useState('');
  const [dateOfBirth, setDateOfBirth] = useState('');

  // Step 3: Contact & Address
  const [phone, setPhone] = useState('');
  const [address, setAddress] = useState('');
  const [city, setCity] = useState('');
  const [state, setState] = useState('');
  const [zipCode, setZipCode] = useState('');

  const handleNext = () => {
    setError('');

    // Validate current step
    if (activeStep === 0) {
      if (!username || username.length < 3) {
        setError('Username must be at least 3 characters');
        return;
      }
      if (!isValidEmail(email)) {
        setError('Please enter a valid email address');
        return;
      }
      if (password.length < 8) {
        setError('Password must be at least 8 characters');
        return;
      }
      if (password !== confirmPassword) {
        setError('Passwords do not match');
        return;
      }
    }

    if (activeStep === 1) {
      if (!firstName || !isValidName(firstName)) {
        setError('Please enter a valid first name');
        return;
      }
      if (!lastName || !isValidName(lastName)) {
        setError('Please enter a valid last name');
        return;
      }
      if (middleName && !isValidName(middleName)) {
        setError('Please enter a valid middle name');
        return;
      }
      if (!dateOfBirth) {
        setError('Please enter your date of birth');
        return;
      }
      // Check age (must be 18+)
      const age = new Date().getFullYear() - new Date(dateOfBirth).getFullYear();
      if (age < 18) {
        setError('You must be at least 18 years old to register');
        return;
      }
    }

    if (activeStep === 2) {
      if (!phone || !isValidPhone(phone)) {
        setError('Please enter a valid 10-digit phone number');
        return;
      }
      if (!address) {
        setError('Please enter your street address');
        return;
      }
      if (!city) {
        setError('Please enter your city');
        return;
      }
      if (!state) {
        setError('Please select your state');
        return;
      }
      if (!zipCode || zipCode.length !== 5) {
        setError('Please enter a valid 5-digit ZIP code');
        return;
      }
    }

    setActiveStep((prev) => prev + 1);
  };

  const handleBack = () => {
    setError('');
    setActiveStep((prev) => prev - 1);
  };

  const handleRegister = async () => {
    setError('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8004/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username,
          email,
          password,
          first_name: firstName,
          middle_name: middleName,
          last_name: lastName,
          date_of_birth: dateOfBirth,
          phone,
          address,
          city,
          state,
          zip_code: zipCode,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.message || 'Registration failed');
      }

      const data = await response.json();

      // Store token and user info
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));

      // Redirect to mortgage application
      navigate('/mortgage-application');
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  // US States
  const usStates = [
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC'
  ];

  return (
    <Box
      sx={{
        minHeight: '100vh',
        width: '100%',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        py: { xs: 2, sm: 4 },
        px: { xs: 2, sm: 3 },
      }}
    >
      <Container maxWidth="md" disableGutters sx={{ width: '100%', px: { xs: 1, sm: 0 } }}>
        <Paper elevation={10} sx={{ p: { xs: 3, sm: 4 }, borderRadius: 3 }}>
          <Box textAlign="center" mb={3}>
            <Box
              sx={{
                bgcolor: 'primary.main',
                color: 'white',
                width: 56,
                height: 56,
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto',
                mb: 2,
              }}
            >
              <PersonAddIcon fontSize="large" />
            </Box>
            <Typography variant="h4" fontWeight="bold" gutterBottom>
              Create Account
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Join us to get started with your mortgage application
            </Typography>
          </Box>

          <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>

          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          <Box component="form" onSubmit={(e) => e.preventDefault()}>
            {/* Step 1: Account Info */}
            {activeStep === 0 && (
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value.toLowerCase())}
                    required
                    helperText="Must be at least 3 characters"
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    error={!!email && !isValidEmail(email)}
                    helperText={email && !isValidEmail(email) ? 'Invalid email' : undefined}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    helperText="Must be at least 8 characters"
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Confirm Password"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                    error={!!confirmPassword && password !== confirmPassword}
                    helperText={
                      confirmPassword && password !== confirmPassword
                        ? 'Passwords do not match'
                        : undefined
                    }
                  />
                </Grid>
              </Grid>
            )}

            {/* Step 2: Personal Details */}
            {activeStep === 1 && (
              <Grid container spacing={3}>
                <Grid item xs={12} sm={4}>
                  <TextField
                    fullWidth
                    label="First Name"
                    value={firstName}
                    onChange={(e) => setFirstName(formatName(e.target.value))}
                    required
                    error={!!firstName && !isValidName(firstName)}
                    helperText={
                      firstName && !isValidName(firstName) ? 'Letters only, 2-50 chars' : undefined
                    }
                  />
                </Grid>
                <Grid item xs={12} sm={4}>
                  <TextField
                    fullWidth
                    label="Middle Name"
                    value={middleName}
                    onChange={(e) => setMiddleName(formatName(e.target.value))}
                    error={!!middleName && !isValidName(middleName)}
                    helperText={
                      middleName && !isValidName(middleName) ? 'Letters only' : 'Optional'
                    }
                  />
                </Grid>
                <Grid item xs={12} sm={4}>
                  <TextField
                    fullWidth
                    label="Last Name"
                    value={lastName}
                    onChange={(e) => setLastName(formatName(e.target.value))}
                    required
                    error={!!lastName && !isValidName(lastName)}
                    helperText={
                      lastName && !isValidName(lastName) ? 'Letters only, 2-50 chars' : undefined
                    }
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Date of Birth"
                    type="date"
                    value={dateOfBirth}
                    onChange={(e) => setDateOfBirth(e.target.value)}
                    required
                    InputLabelProps={{ shrink: true }}
                    helperText="You must be at least 18 years old"
                  />
                </Grid>
              </Grid>
            )}

            {/* Step 3: Contact & Address */}
            {activeStep === 2 && (
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Phone Number"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value.replace(/\D/g, ''))}
                    required
                    inputProps={{ maxLength: 10 }}
                    error={!!phone && !isValidPhone(phone)}
                    helperText={
                      phone && !isValidPhone(phone)
                        ? 'Enter 10-digit phone'
                        : phone
                        ? formatPhoneNumber(phone)
                        : 'Numbers only'
                    }
                  />
                </Grid>
                <Grid item xs={12}>
                  <AddressAutocomplete
                    value={address}
                    onChange={(newAddress) => {
                      setAddress(newAddress);
                      // Try to parse city, state, zip from the address
                      const parts = newAddress.split(',').map((p) => p.trim());
                      if (parts.length >= 3) {
                        setCity(parts[parts.length - 3] || '');
                        const stateZip = parts[parts.length - 2] || '';
                        const stateMatch = stateZip.match(/^([A-Z]{2})/);
                        const zipMatch = stateZip.match(/(\d{5})$/);
                        if (stateMatch) setState(stateMatch[1]);
                        if (zipMatch) setZipCode(zipMatch[1]);
                      }
                    }}
                    textFieldProps={{
                      label: 'Street Address',
                      placeholder: '123 Main Street',
                      helperText: 'Start typing and select from suggestions',
                      required: true,
                    }}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="City"
                    value={city}
                    onChange={(e) => setCity(e.target.value)}
                    required
                  />
                </Grid>
                <Grid item xs={12} sm={3}>
                  <FormControl fullWidth required>
                    <InputLabel>State</InputLabel>
                    <Select value={state} label="State" onChange={(e) => setState(e.target.value)}>
                      {usStates.map((st) => (
                        <MenuItem key={st} value={st}>
                          {st}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={3}>
                  <TextField
                    fullWidth
                    label="ZIP Code"
                    value={zipCode}
                    onChange={(e) => setZipCode(e.target.value.replace(/\D/g, ''))}
                    required
                    inputProps={{ maxLength: 5 }}
                  />
                </Grid>
              </Grid>
            )}

            {/* Navigation Buttons */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
              <Button
                variant="outlined"
                onClick={handleBack}
                disabled={activeStep === 0}
                sx={{ minWidth: 100 }}
              >
                Back
              </Button>
              {activeStep < steps.length - 1 ? (
                <Button variant="contained" onClick={handleNext} sx={{ minWidth: 100 }}>
                  Next
                </Button>
              ) : (
                <Button
                  variant="contained"
                  onClick={handleRegister}
                  disabled={loading}
                  sx={{ minWidth: 100 }}
                >
                  {loading ? 'Creating Account...' : 'Register'}
                </Button>
              )}
            </Box>
          </Box>

          <Box textAlign="center" mt={3}>
            <Typography variant="body2">
              Already have an account?{' '}
              <Link
                component="button"
                variant="body2"
                onClick={() => navigate('/login')}
                sx={{ textDecoration: 'none', fontWeight: 600 }}
              >
                Sign In
              </Link>
            </Typography>
          </Box>
        </Paper>
      </Container>
    </Box>
  );
};

export default Register;
