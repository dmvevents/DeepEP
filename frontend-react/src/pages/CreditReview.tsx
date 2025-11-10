import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Container,
  Box,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Stepper,
  Step,
  StepLabel,
  Paper,
} from '@mui/material';
import { CheckCircle, ArrowBack, ArrowForward } from '@mui/icons-material';
import CreditSnapshot from '../components/CreditSnapshot';
import TradelineConfirmationCard from '../components/TradelineConfirmationCard';
import { creditApi } from '../services/api';
import type { CreditSnapshot as CreditSnapshotType, Tradeline } from '../types/credit';

const CreditReview: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const loanEstimateId = searchParams.get('loan_estimate_id');

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [snapshot, setSnapshot] = useState<CreditSnapshotType | null>(null);
  const [activeStep, setActiveStep] = useState(0);

  const steps = ['Review Credit Report', 'Confirm Tradelines', 'Complete'];

  useEffect(() => {
    if (!loanEstimateId) {
      setError('No loan estimate ID provided');
      setLoading(false);
      return;
    }

    loadCreditSnapshot();
  }, [loanEstimateId]);

  const loadCreditSnapshot = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await creditApi.getCreditSnapshot(Number(loanEstimateId));
      setSnapshot(data);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load credit snapshot');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmTradeline = async (tradelineId: number) => {
    try {
      await creditApi.updateTradelineConfirmation({
        tradeline_id: tradelineId,
        confirmation_status: 'confirmed',
      });
      // Reload snapshot to get updated data
      await loadCreditSnapshot();
    } catch (err: any) {
      throw new Error(err.response?.data?.message || 'Failed to confirm tradeline');
    }
  };

  const handleDisputeTradeline = async (tradelineId: number, reason: string) => {
    try {
      await creditApi.updateTradelineConfirmation({
        tradeline_id: tradelineId,
        confirmation_status: 'disputed',
        dispute_reason: reason,
      });

      // Create a DocTask for the dispute
      await creditApi.createDocTask({
        tradeline_id: tradelineId,
        loan_estimate_id: Number(loanEstimateId),
        task_type: 'dispute_tradeline',
        title: `Dispute: ${snapshot?.tradelines.find((t) => t.id === tradelineId)?.creditor_name}`,
        description: `Please provide supporting documentation for your dispute: ${reason}`,
      });

      // Reload snapshot to get updated data
      await loadCreditSnapshot();
    } catch (err: any) {
      throw new Error(err.response?.data?.message || 'Failed to dispute tradeline');
    }
  };

  const handleUploadDocument = async (tradelineId: number) => {
    try {
      const tradeline = snapshot?.tradelines.find((t) => t.id === tradelineId);
      await creditApi.createDocTask({
        tradeline_id: tradelineId,
        loan_estimate_id: Number(loanEstimateId),
        task_type: 'upload_document',
        title: `Upload Document: ${tradeline?.creditor_name}`,
        description: 'Please upload supporting documentation for this tradeline.',
      });

      // Navigate to documents page or show success
      alert('Document task created. You can upload documents from the Documents page.');
    } catch (err: any) {
      alert(err.response?.data?.message || 'Failed to create document task');
    }
  };

  const handleNext = () => {
    if (activeStep === 0) {
      // Move to tradeline confirmation
      setActiveStep(1);
    } else if (activeStep === 1) {
      // Check if all tradelines are confirmed or disputed
      const pendingTradelines = snapshot?.tradelines.filter((t) => t.confirmation_status === 'pending') || [];
      if (pendingTradelines.length > 0) {
        setError(`Please confirm or dispute all ${pendingTradelines.length} pending tradeline(s)`);
        return;
      }
      setActiveStep(2);
    } else {
      // Navigate back to application or next step
      navigate('/mortgage-application');
    }
  };

  const handleBack = () => {
    if (activeStep > 0) {
      setActiveStep(activeStep - 1);
    } else {
      navigate(-1);
    }
  };

  const getStepContent = (step: number) => {
    if (loading) {
      return (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      );
    }

    if (error) {
      return (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      );
    }

    if (!snapshot) {
      return (
        <Alert severity="warning" sx={{ mb: 3 }}>
          No credit snapshot available
        </Alert>
      );
    }

    switch (step) {
      case 0:
        return <CreditSnapshot snapshot={snapshot} loading={loading} />;

      case 1:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Review and Confirm Tradelines
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Please review each tradeline and confirm the information is accurate. If you find any errors, you can
              dispute them and provide supporting documentation.
            </Typography>
            {snapshot.tradelines.map((tradeline: Tradeline) => (
              <TradelineConfirmationCard
                key={tradeline.id}
                tradeline={tradeline}
                onConfirm={handleConfirmTradeline}
                onDispute={handleDisputeTradeline}
                onUpload={handleUploadDocument}
              />
            ))}
            {snapshot.tradelines.length === 0 && (
              <Alert severity="info">No tradelines found on your credit report.</Alert>
            )}
          </Box>
        );

      case 2:
        const confirmedCount = snapshot.tradelines.filter((t) => t.confirmation_status === 'confirmed').length;
        const disputedCount = snapshot.tradelines.filter((t) => t.confirmation_status === 'disputed').length;

        return (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <CheckCircle sx={{ fontSize: 80, color: 'success.main', mb: 2 }} />
            <Typography variant="h4" gutterBottom>
              Credit Review Complete
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
              You have successfully reviewed your credit report.
            </Typography>
            <Paper sx={{ p: 3, maxWidth: 400, mx: 'auto', mb: 3 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Summary:
              </Typography>
              <Typography variant="body1">
                <strong>{confirmedCount}</strong> tradeline{confirmedCount !== 1 ? 's' : ''} confirmed
              </Typography>
              {disputedCount > 0 && (
                <Typography variant="body1" color="warning.main">
                  <strong>{disputedCount}</strong> tradeline{disputedCount !== 1 ? 's' : ''} disputed
                </Typography>
              )}
            </Paper>
            <Typography variant="body2" color="text.secondary">
              Click Continue to proceed with your mortgage application.
            </Typography>
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Credit Review
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Review your credit report and confirm the accuracy of all tradelines.
        </Typography>
      </Box>

      <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      {getStepContent(activeStep)}

      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4, pt: 3, borderTop: 1, borderColor: 'divider' }}>
        <Button startIcon={<ArrowBack />} onClick={handleBack} disabled={loading}>
          Back
        </Button>
        <Button variant="contained" endIcon={<ArrowForward />} onClick={handleNext} disabled={loading}>
          {activeStep === steps.length - 1 ? 'Continue to Application' : 'Next'}
        </Button>
      </Box>
    </Container>
  );
};

export default CreditReview;
