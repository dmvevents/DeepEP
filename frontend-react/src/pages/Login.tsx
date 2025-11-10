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
  Divider,
} from '@mui/material';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';

const Login = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8004/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        throw new Error('Invalid username or password');
      }

      const data = await response.json();

      // Store token in localStorage
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.user));

      // Redirect based on user role
      if (data.user.is_admin) {
        navigate('/admin');
      } else {
        navigate('/mortgage-application');
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

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
      <Container maxWidth="sm" disableGutters sx={{ width: '100%', px: { xs: 1, sm: 0 } }}>
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
                margin: '0 auto 16px',
              }}
            >
              <LockOutlinedIcon fontSize="large" />
            </Box>
            <Typography
              variant="h4"
              component="h1"
              gutterBottom
              fontWeight={700}
              sx={{ fontSize: { xs: '1.75rem', sm: '2.125rem' } }}
            >
              Welcome Back
            </Typography>
            <Typography
              variant="body1"
              color="text.secondary"
              sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}
            >
              Sign in to continue to Mortgage Calculator
            </Typography>
          </Box>

          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          <Box component="form" onSubmit={handleLogin} aria-label="Login form">
            <TextField
              fullWidth
              label="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              margin="normal"
              required
              autoFocus
              autoComplete="username"
              disabled={loading}
              aria-label="Username input"
              inputProps={{ 'aria-required': 'true' }}
            />
            <TextField
              fullWidth
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              margin="normal"
              required
              autoComplete="current-password"
              disabled={loading}
              aria-label="Password input"
              inputProps={{ 'aria-required': 'true' }}
            />

            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              disabled={loading}
              sx={{ mt: 3, mb: 2, py: 1.5 }}
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </Button>

            <Box textAlign="center" mt={2}>
              <Link
                href="#"
                underline="hover"
                onClick={(e) => {
                  e.preventDefault();
                  navigate('/');
                }}
                sx={{ color: 'text.secondary' }}
              >
                ← Back to Home
              </Link>
            </Box>
          </Box>

          <Divider sx={{ my: 3 }}>
            <Typography variant="body2" color="text.secondary">
              Demo Accounts
            </Typography>
          </Divider>

          <Box sx={{ bgcolor: '#f5f5f5', p: 2, borderRadius: 2 }}>
            <Typography variant="body2" gutterBottom>
              <strong>Admin Account:</strong>
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', mb: 2 }}>
              Username: admin | Password: admin
            </Typography>

            <Typography variant="body2" gutterBottom>
              <strong>Demo Account:</strong>
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
              Username: demo | Password: demo123
            </Typography>
          </Box>

          <Divider sx={{ my: 3 }} />

          <Box textAlign="center">
            <Typography variant="body2">
              Don't have an account?{' '}
              <Link
                component="button"
                variant="body2"
                onClick={() => navigate('/register')}
                sx={{ textDecoration: 'none', fontWeight: 600 }}
              >
                Sign Up
              </Link>
            </Typography>
          </Box>

          <Box mt={3} textAlign="center">
            <Button
              variant="outlined"
              onClick={() => {
                setUsername('demo');
                setPassword('demo123');
              }}
            >
              Quick Fill Demo Account
            </Button>
          </Box>
        </Paper>

        <Box textAlign="center" mt={3}>
          <Typography variant="body2" sx={{ color: 'white', opacity: 0.9 }}>
            © 2025 Real Estate Mortgage Calculator
          </Typography>
          <Typography variant="caption" sx={{ color: 'white', opacity: 0.7 }}>
            Created by Anton Alexander
          </Typography>
        </Box>
      </Container>
    </Box>
  );
};

export default Login;
