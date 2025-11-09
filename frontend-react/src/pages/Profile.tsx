import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Box,
  Typography,
  Paper,
  Grid,
  TextField,
  Button,
  Avatar,
  IconButton,
  Dialog,
  DialogContent,
  DialogTitle,
  DialogActions,
  Alert,
  Divider,
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import CameraAltIcon from '@mui/icons-material/CameraAlt';
import SaveIcon from '@mui/icons-material/Save';
import CancelIcon from '@mui/icons-material/Cancel';
import Navbar from '../components/Navbar';
import ReactCrop, { Crop, PixelCrop } from 'react-image-crop';
import 'react-image-crop/dist/ReactCrop.css';
import { getInitials, formatPhoneNumber, isValidEmail, isValidPhone } from '../utils/formatters';

const Profile = () => {
  const navigate = useNavigate();
  const imgRef = useRef<HTMLImageElement>(null);
  const [user, setUser] = useState<any>(null);
  const [editing, setEditing] = useState(false);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [imageSrc, setImageSrc] = useState<string>('');
  const [crop, setCrop] = useState<Crop>({
    unit: '%',
    width: 90,
    height: 90,
    x: 5,
    y: 5,
  });
  const [completedCrop, setCompletedCrop] = useState<PixelCrop | null>(null);
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const [formData, setFormData] = useState({
    username: '',
    email: '',
    phone: '',
    first_name: '',
    last_name: '',
  });

  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });

  useEffect(() => {
    // Load user from localStorage
    const userStr = localStorage.getItem('user');
    if (!userStr) {
      navigate('/login');
      return;
    }

    const userData = JSON.parse(userStr);
    setUser(userData);
    setFormData({
      username: userData.username || '',
      email: userData.email || '',
      phone: userData.phone || '',
      first_name: userData.first_name || '',
      last_name: userData.last_name || '',
    });
  }, [navigate]);

  const handleEditToggle = () => {
    if (editing) {
      // Cancel - reset form
      setFormData({
        username: user.username || '',
        email: user.email || '',
        phone: user.phone || '',
        first_name: user.first_name || '',
        last_name: user.last_name || '',
      });
    }
    setEditing(!editing);
  };

  const handleSaveProfile = async () => {
    // Validate email
    if (!isValidEmail(formData.email)) {
      setErrorMessage('Please enter a valid email address');
      return;
    }

    // Validate phone
    if (formData.phone && !isValidPhone(formData.phone)) {
      setErrorMessage('Please enter a valid 10-digit phone number');
      return;
    }

    try {
      // TODO: Replace with actual API call
      // await fetch('/api/profile/update/', {
      //   method: 'PATCH',
      //   headers: {
      //     'Content-Type': 'application/json',
      //     'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      //   },
      //   body: JSON.stringify(formData)
      // });

      // Update user in localStorage
      const updatedUser = { ...user, ...formData };
      localStorage.setItem('user', JSON.stringify(updatedUser));
      setUser(updatedUser);
      setEditing(false);
      setSuccessMessage('Profile updated successfully!');
      setErrorMessage('');
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (error) {
      setErrorMessage('Failed to update profile. Please try again.');
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const reader = new FileReader();
      reader.addEventListener('load', () => {
        setImageSrc(reader.result as string);
        setUploadDialogOpen(true);
      });
      reader.readAsDataURL(e.target.files[0]);
    }
  };

  const getCroppedImg = async (): Promise<string> => {
    if (!imgRef.current || !completedCrop) {
      return '';
    }

    const image = imgRef.current;
    const canvas = document.createElement('canvas');
    const scaleX = image.naturalWidth / image.width;
    const scaleY = image.naturalHeight / image.height;

    const size = 200; // Target size for avatar
    canvas.width = size;
    canvas.height = size;

    const ctx = canvas.getContext('2d');
    if (!ctx) return '';

    ctx.drawImage(
      image,
      completedCrop.x * scaleX,
      completedCrop.y * scaleY,
      completedCrop.width * scaleX,
      completedCrop.height * scaleY,
      0,
      0,
      size,
      size
    );

    return canvas.toDataURL('image/jpeg');
  };

  const handleSaveAvatar = async () => {
    try {
      const croppedImageUrl = await getCroppedImg();
      if (croppedImageUrl) {
        // TODO: Replace with actual API call to upload image
        // const formData = new FormData();
        // const blob = await fetch(croppedImageUrl).then(r => r.blob());
        // formData.append('profile_picture', blob, 'avatar.jpg');
        // await fetch('/api/profile/upload-picture/', {
        //   method: 'POST',
        //   headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` },
        //   body: formData
        // });

        // Save to localStorage for now
        const updatedUser = { ...user, profile_picture: croppedImageUrl };
        localStorage.setItem('user', JSON.stringify(updatedUser));
        setUser(updatedUser);
        setUploadDialogOpen(false);
        setSuccessMessage('Profile picture updated successfully!');
        setTimeout(() => setSuccessMessage(''), 3000);
      }
    } catch (error) {
      setErrorMessage('Failed to upload profile picture. Please try again.');
    }
  };

  const handleChangePassword = async () => {
    if (passwordData.new_password !== passwordData.confirm_password) {
      setErrorMessage('New passwords do not match');
      return;
    }

    if (passwordData.new_password.length < 8) {
      setErrorMessage('New password must be at least 8 characters');
      return;
    }

    try {
      // TODO: Replace with actual API call
      // await fetch('/api/profile/change-password/', {
      //   method: 'POST',
      //   headers: {
      //     'Content-Type': 'application/json',
      //     'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      //   },
      //   body: JSON.stringify({
      //     current_password: passwordData.current_password,
      //     new_password: passwordData.new_password
      //   })
      // });

      setPasswordData({ current_password: '', new_password: '', confirm_password: '' });
      setSuccessMessage('Password changed successfully!');
      setErrorMessage('');
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (error) {
      setErrorMessage('Failed to change password. Please check your current password.');
    }
  };

  if (!user) {
    return null;
  }

  return (
    <>
      <Navbar title="My Profile" />

      <Box
        sx={{
          minHeight: 'calc(100vh - 64px)',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          py: 4,
        }}
      >
        <Container maxWidth="md">
          {/* Success/Error Messages */}
          {successMessage && (
            <Alert severity="success" sx={{ mb: 3 }}>
              {successMessage}
            </Alert>
          )}
          {errorMessage && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {errorMessage}
            </Alert>
          )}

          {/* Profile Picture Section */}
          <Paper sx={{ p: 4, mb: 3, textAlign: 'center' }}>
            <Box sx={{ position: 'relative', display: 'inline-block' }}>
              <Avatar
                sx={{
                  width: 150,
                  height: 150,
                  fontSize: '3rem',
                  bgcolor: '#667eea',
                  mx: 'auto',
                }}
                src={user.profile_picture}
              >
                {!user.profile_picture && getInitials(user.username || user.email)}
              </Avatar>
              <IconButton
                sx={{
                  position: 'absolute',
                  bottom: 0,
                  right: 0,
                  bgcolor: 'white',
                  boxShadow: 2,
                  '&:hover': { bgcolor: '#f5f5f5' },
                }}
                onClick={() => document.getElementById('avatar-upload')?.click()}
              >
                <CameraAltIcon />
              </IconButton>
              <input
                id="avatar-upload"
                type="file"
                accept="image/*"
                style={{ display: 'none' }}
                onChange={handleFileSelect}
              />
            </Box>
            <Typography variant="h5" sx={{ mt: 2, fontWeight: 600 }}>
              {user.username || user.email}
            </Typography>
            {user.is_admin && (
              <Typography variant="body2" color="primary" sx={{ fontWeight: 600 }}>
                {user.is_super_admin ? 'Super Admin' : 'Admin'} Account
              </Typography>
            )}
          </Paper>

          {/* Profile Information */}
          <Paper sx={{ p: 4, mb: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Profile Information
              </Typography>
              <Button
                variant={editing ? 'outlined' : 'contained'}
                startIcon={editing ? <CancelIcon /> : <EditIcon />}
                onClick={handleEditToggle}
              >
                {editing ? 'Cancel' : 'Edit'}
              </Button>
            </Box>

            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Username"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  disabled={!editing}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  disabled={!editing}
                  error={editing && formData.email && !isValidEmail(formData.email)}
                  helperText={editing && formData.email && !isValidEmail(formData.email) ? 'Invalid email' : ''}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="First Name"
                  value={formData.first_name}
                  onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                  disabled={!editing}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Last Name"
                  value={formData.last_name}
                  onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                  disabled={!editing}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Phone"
                  value={editing ? formData.phone : formatPhoneNumber(formData.phone)}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  disabled={!editing}
                  error={editing && formData.phone && !isValidPhone(formData.phone)}
                  helperText={editing && formData.phone && !isValidPhone(formData.phone) ? 'Enter 10-digit phone' : ''}
                />
              </Grid>
            </Grid>

            {editing && (
              <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  variant="contained"
                  startIcon={<SaveIcon />}
                  onClick={handleSaveProfile}
                  sx={{ fontWeight: 600 }}
                >
                  Save Changes
                </Button>
              </Box>
            )}
          </Paper>

          {/* Change Password */}
          <Paper sx={{ p: 4 }}>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
              Change Password
            </Typography>

            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Current Password"
                  type="password"
                  value={passwordData.current_password}
                  onChange={(e) => setPasswordData({ ...passwordData, current_password: e.target.value })}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="New Password"
                  type="password"
                  value={passwordData.new_password}
                  onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                  error={passwordData.new_password.length > 0 && passwordData.new_password.length < 8}
                  helperText={passwordData.new_password.length > 0 && passwordData.new_password.length < 8 ? 'Minimum 8 characters' : ''}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Confirm New Password"
                  type="password"
                  value={passwordData.confirm_password}
                  onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                  error={passwordData.confirm_password.length > 0 && passwordData.new_password !== passwordData.confirm_password}
                  helperText={passwordData.confirm_password.length > 0 && passwordData.new_password !== passwordData.confirm_password ? 'Passwords do not match' : ''}
                />
              </Grid>
            </Grid>

            <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                variant="contained"
                color="secondary"
                onClick={handleChangePassword}
                disabled={!passwordData.current_password || !passwordData.new_password || passwordData.new_password !== passwordData.confirm_password}
              >
                Change Password
              </Button>
            </Box>
          </Paper>
        </Container>
      </Box>

      {/* Image Crop Dialog */}
      <Dialog open={uploadDialogOpen} onClose={() => setUploadDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Crop Profile Picture</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
            {imageSrc && (
              <ReactCrop
                crop={crop}
                onChange={(c) => setCrop(c)}
                onComplete={(c) => setCompletedCrop(c)}
                aspect={1}
                circularCrop
              >
                <img ref={imgRef} src={imageSrc} alt="Crop preview" style={{ maxWidth: '100%' }} />
              </ReactCrop>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSaveAvatar} variant="contained">
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default Profile;
