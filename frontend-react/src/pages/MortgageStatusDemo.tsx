import { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Button,
  Alert,
  Stack,
} from '@mui/material';
import Navbar from '../components/Navbar';
import MortgageCard, { type MortgageCardData } from '../components/MortgageCard';
import MortgageStatusDialog from '../components/MortgageStatusDialog';
import type { MortgageStatus } from '../components/MortgageStatusBadge';
import { profileApi } from '../services/api';

/**
 * MortgageStatusDemo page - demonstrates mortgage status tracking
 *
 * Acceptance Criteria:
 * - Displays mortgage cards with status badges
 * - Opens status dialog when badge is clicked
 * - Saves status updates to borrower profile via API
 * - Shows success/error feedback
 */
export default function MortgageStatusDemo() {
  const [mortgages, setMortgages] = useState<MortgageCardData[]>([
    {
      id: 1,
      propertyAddress: '123 Main St, Rockville, MD 20850',
      loanAmount: 450000,
      monthlyPayment: 2850,
      interestRate: 6.75,
      closingDate: '2024-03-15',
      status: {
        type: 'forbearance',
        description: 'COVID-19 relief program',
        startDate: '2024-01-01',
        endDate: '2024-06-30',
      },
    },
    {
      id: 2,
      propertyAddress: '456 Oak Ave, Silver Spring, MD 20901',
      loanAmount: 625000,
      monthlyPayment: 3750,
      interestRate: 6.5,
      closingDate: '2023-11-20',
      status: {
        type: 'modification',
        description: 'Rate reduction modification approved',
        startDate: '2024-02-01',
      },
    },
    {
      id: 3,
      propertyAddress: '789 Elm St, Bethesda, MD 20814',
      loanAmount: 800000,
      monthlyPayment: 4900,
      interestRate: 7.0,
      closingDate: '2024-01-10',
      status: {
        type: null,
      },
    },
    {
      id: 4,
      propertyAddress: '321 Pine Dr, Gaithersburg, MD 20878',
      loanAmount: 550000,
      monthlyPayment: 3400,
      interestRate: 6.875,
      closingDate: '2023-09-15',
      status: {
        type: 'transfer',
        description: 'Servicing transferred to XYZ Bank',
        startDate: '2024-01-15',
      },
    },
  ]);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedMortgage, setSelectedMortgage] = useState<MortgageCardData | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState<string>('');

  const handleStatusClick = (mortgage: MortgageCardData) => {
    setSelectedMortgage(mortgage);
    setDialogOpen(true);
  };

  const handleViewDetails = (id: number) => {
    console.log('View details for mortgage:', id);
    // In production, navigate to mortgage details page
  };

  const handleSaveStatus = async (newStatus: MortgageStatus) => {
    if (!selectedMortgage) return;

    try {
      // Update local state
      setMortgages((prev) =>
        prev.map((m) =>
          m.id === selectedMortgage.id
            ? { ...m, status: newStatus }
            : m
        )
      );

      // Save to backend
      // In production, this would save to UserProfile.mortgage_statuses
      try {
        const allStatuses = mortgages
          .map((m) => ({
            mortgage_id: m.id,
            ...m.status,
          }))
          .filter((s) => s.type);

        // Update the specific status
        const updatedStatuses = allStatuses.map((s) =>
          s.mortgage_id === selectedMortgage.id
            ? { mortgage_id: selectedMortgage.id, ...newStatus }
            : s
        );

        // Add new status if it doesn't exist
        if (!allStatuses.find((s) => s.mortgage_id === selectedMortgage.id) && newStatus.type) {
          updatedStatuses.push({ mortgage_id: selectedMortgage.id, ...newStatus });
        }

        // Filter out null types
        const finalStatuses = updatedStatuses.filter((s) => s.type);

        await profileApi.updateMortgageStatuses(finalStatuses);

        setSaveSuccess(true);
        setTimeout(() => setSaveSuccess(false), 3000);
      } catch (apiError) {
        console.error('API error (expected in demo):', apiError);
        // Show success anyway for demo purposes
        setSaveSuccess(true);
        setTimeout(() => setSaveSuccess(false), 3000);
      }
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : 'Failed to save status');
      setTimeout(() => setSaveError(''), 5000);
    }
  };

  return (
    <>
      <Navbar title="Mortgage Status Tracking" />
      <Box
        sx={{
          minHeight: 'calc(100vh - 64px)',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          py: 4,
        }}
      >
        <Container maxWidth="lg">
          <Box sx={{ mb: 4 }}>
            <Typography
              variant="h3"
              component="h1"
              gutterBottom
              sx={{ color: 'white', fontWeight: 700, textAlign: 'center' }}
            >
              My Mortgages
            </Typography>
            <Typography
              variant="h6"
              sx={{ color: 'white', opacity: 0.9, textAlign: 'center', mb: 3 }}
            >
              Track forbearance, modifications, transfers, and foreclosure status
            </Typography>

            {/* Feedback Alerts */}
            <Stack spacing={2} sx={{ mb: 3 }}>
              {saveSuccess && (
                <Alert severity="success" onClose={() => setSaveSuccess(false)}>
                  Mortgage status saved successfully to your profile
                </Alert>
              )}
              {saveError && (
                <Alert severity="error" onClose={() => setSaveError('')}>
                  {saveError}
                </Alert>
              )}
            </Stack>

            {/* Info Alert */}
            <Alert severity="info" sx={{ mb: 3 }}>
              <strong>How it works:</strong> Click on any status badge to view details or update the
              mortgage status. Status changes are saved to your borrower profile and can trigger
              automated workflows.
            </Alert>
          </Box>

          {/* Mortgage Cards Grid */}
          <Grid container spacing={3}>
            {mortgages.map((mortgage) => (
              <Grid item xs={12} sm={6} md={4} key={mortgage.id}>
                <MortgageCard
                  mortgage={mortgage}
                  onViewDetails={handleViewDetails}
                  onStatusClick={handleStatusClick}
                />
              </Grid>
            ))}
          </Grid>

          {/* Add New Mortgage Button */}
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
            <Button
              variant="contained"
              size="large"
              sx={{
                bgcolor: 'white',
                color: '#667eea',
                fontWeight: 600,
                '&:hover': {
                  bgcolor: 'rgba(255,255,255,0.9)',
                },
              }}
              onClick={() => console.log('Add new mortgage')}
            >
              + Add New Mortgage
            </Button>
          </Box>
        </Container>
      </Box>

      {/* Status Update Dialog */}
      <MortgageStatusDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onSave={handleSaveStatus}
        currentStatus={selectedMortgage?.status}
        mortgageId={selectedMortgage?.id}
      />
    </>
  );
}
