import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import MortgageApplication from './pages/MortgageApplication';
import AdminDashboard from './pages/AdminDashboard';
import SuperAdminDashboard from './pages/SuperAdminDashboard';
import DocumentUpload from './pages/DocumentUpload';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import MyApplications from './pages/MyApplications';
import Profile from './pages/Profile';
import AdminProfile from './pages/AdminProfile';
import CreditReview from './pages/CreditReview';
import MortgageStatusDemo from './pages/MortgageStatusDemo';

const theme = createTheme({
  palette: {
    primary: {
      main: '#667eea',
      dark: '#764ba2',
    },
    secondary: {
      main: '#10b981',
    },
    error: {
      main: '#ef4444',
    },
  },
  typography: {
    fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: '10px',
          padding: '12px 24px',
          fontSize: '1rem',
          fontWeight: 600,
        },
      },
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/mortgage-application" element={<MortgageApplication />} />
          <Route path="/my-applications" element={<MyApplications />} />
          <Route path="/mortgage-status" element={<MortgageStatusDemo />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/admin-profile" element={<AdminProfile />} />
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/super-admin" element={<SuperAdminDashboard />} />
          <Route path="/documents" element={<DocumentUpload />} />
          <Route path="/credit-review" element={<CreditReview />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;
