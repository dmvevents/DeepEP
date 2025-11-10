import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Grid,
  Button,
  Chip,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Stack,
  IconButton,
  Collapse,
} from '@mui/material';
import {
  CheckCircle,
  Error as ErrorIcon,
  ExpandMore,
  CreditCard,
  Home,
  DirectionsCar,
  School,
  AccountBalance,
  Warning,
  UploadFile,
  Gavel,
} from '@mui/icons-material';
import type { Tradeline, ConfirmationStatus } from '../types/credit';
import { formatCurrency } from '../utils/formatters';

interface TradelineConfirmationCardProps {
  tradeline: Tradeline;
  onConfirm: (tradelineId: number) => Promise<void>;
  onDispute: (tradelineId: number, reason: string) => Promise<void>;
  onUpload: (tradelineId: number) => void;
}

const TradelineConfirmationCard: React.FC<TradelineConfirmationCardProps> = ({
  tradeline,
  onConfirm,
  onDispute,
  onUpload,
}) => {
  const [expanded, setExpanded] = useState(false);
  const [disputeDialogOpen, setDisputeDialogOpen] = useState(false);
  const [disputeReason, setDisputeReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getAccountIcon = () => {
    switch (tradeline.account_type) {
      case 'mortgage':
        return <Home />;
      case 'auto':
        return <DirectionsCar />;
      case 'student':
        return <School />;
      case 'credit_card':
        return <CreditCard />;
      case 'personal':
      case 'installment':
        return <AccountBalance />;
      case 'collection':
        return <Warning color="error" />;
      default:
        return <CreditCard />;
    }
  };

  const getStatusChip = (status: ConfirmationStatus) => {
    switch (status) {
      case 'confirmed':
        return <Chip icon={<CheckCircle />} label="Confirmed" color="success" size="small" />;
      case 'disputed':
        return <Chip icon={<ErrorIcon />} label="Disputed" color="error" size="small" />;
      case 'pending':
        return <Chip label="Pending Review" color="warning" size="small" />;
    }
  };

  const getAccountStatusChip = () => {
    const colorMap: Record<string, 'success' | 'default' | 'warning' | 'error'> = {
      open: 'success',
      closed: 'default',
      paid: 'success',
      charge_off: 'error',
      collection: 'error',
    };

    return (
      <Chip
        label={tradeline.status.replace('_', ' ').toUpperCase()}
        color={colorMap[tradeline.status] || 'default'}
        size="small"
      />
    );
  };

  const handleConfirm = async () => {
    setLoading(true);
    setError(null);
    try {
      await onConfirm(tradeline.id);
    } catch (err) {
      setError('Failed to confirm tradeline. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDisputeOpen = () => {
    setDisputeDialogOpen(true);
    setDisputeReason(tradeline.dispute_reason || '');
  };

  const handleDisputeSubmit = async () => {
    if (!disputeReason.trim()) {
      setError('Please provide a reason for the dispute');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await onDispute(tradeline.id, disputeReason);
      setDisputeDialogOpen(false);
    } catch (err) {
      setError('Failed to submit dispute. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const isPastDue = tradeline.days_past_due > 0;
  const isDerogatory = ['charge_off', 'collection'].includes(tradeline.status);

  return (
    <>
      <Card
        sx={{
          mb: 2,
          border: isDerogatory ? 2 : 1,
          borderColor: isDerogatory ? 'error.main' : 'divider',
        }}
      >
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flex: 1 }}>
              <Box
                sx={{
                  p: 1,
                  bgcolor: 'primary.light',
                  borderRadius: 1,
                  display: 'flex',
                  alignItems: 'center',
                  color: 'primary.main',
                }}
              >
                {getAccountIcon()}
              </Box>
              <Box flex={1}>
                <Typography variant="h6" gutterBottom>
                  {tradeline.creditor_name}
                </Typography>
                <Stack direction="row" spacing={1} alignItems="center">
                  <Typography variant="body2" color="text.secondary">
                    {tradeline.account_type.replace('_', ' ').toUpperCase()}
                  </Typography>
                  {tradeline.account_number && (
                    <>
                      <Typography variant="body2" color="text.secondary">
                        •
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        ...{tradeline.account_number}
                      </Typography>
                    </>
                  )}
                </Stack>
              </Box>
            </Box>
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
              {getStatusChip(tradeline.confirmation_status)}
              <IconButton
                onClick={() => setExpanded(!expanded)}
                sx={{
                  transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
                  transition: 'transform 0.3s',
                }}
                aria-label="expand"
                aria-expanded={expanded}
              >
                <ExpandMore />
              </IconButton>
            </Box>
          </Box>

          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={6} sm={3}>
              <Typography variant="caption" color="text.secondary">
                Current Balance
              </Typography>
              <Typography variant="body1" fontWeight="bold">
                {formatCurrency(parseFloat(tradeline.current_balance))}
              </Typography>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Typography variant="caption" color="text.secondary">
                Monthly Payment
              </Typography>
              <Typography variant="body1" fontWeight="bold">
                {formatCurrency(parseFloat(tradeline.monthly_payment))}
              </Typography>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Typography variant="caption" color="text.secondary">
                Account Status
              </Typography>
              <Box sx={{ mt: 0.5 }}>{getAccountStatusChip()}</Box>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Typography variant="caption" color="text.secondary">
                {tradeline.credit_limit ? 'Credit Limit' : 'Opened Date'}
              </Typography>
              <Typography variant="body1" fontWeight="bold">
                {tradeline.credit_limit
                  ? formatCurrency(parseFloat(tradeline.credit_limit))
                  : tradeline.opened_date
                    ? new Date(tradeline.opened_date).toLocaleDateString()
                    : 'N/A'}
              </Typography>
            </Grid>
          </Grid>

          {isPastDue && (
            <Alert severity="error" sx={{ mb: 2 }}>
              <Typography variant="body2">
                <strong>Past Due:</strong> This account is {tradeline.days_past_due} days past due
              </Typography>
            </Alert>
          )}

          {tradeline.confirmation_status === 'disputed' && tradeline.dispute_reason && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              <Typography variant="body2">
                <strong>Dispute Reason:</strong> {tradeline.dispute_reason}
              </Typography>
            </Alert>
          )}

          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          <Collapse in={expanded}>
            <Box sx={{ mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
              <Grid container spacing={2}>
                {tradeline.opened_date && (
                  <Grid item xs={6} sm={4}>
                    <Typography variant="caption" color="text.secondary">
                      Opened Date
                    </Typography>
                    <Typography variant="body2">
                      {new Date(tradeline.opened_date).toLocaleDateString()}
                    </Typography>
                  </Grid>
                )}
                {tradeline.last_payment_date && (
                  <Grid item xs={6} sm={4}>
                    <Typography variant="caption" color="text.secondary">
                      Last Payment
                    </Typography>
                    <Typography variant="body2">
                      {new Date(tradeline.last_payment_date).toLocaleDateString()}
                    </Typography>
                  </Grid>
                )}
                <Grid item xs={6} sm={4}>
                  <Typography variant="caption" color="text.secondary">
                    Days Past Due
                  </Typography>
                  <Typography variant="body2" color={isPastDue ? 'error' : 'text.primary'}>
                    {tradeline.days_past_due}
                  </Typography>
                </Grid>
              </Grid>
            </Box>
          </Collapse>

          {tradeline.confirmation_status === 'pending' && (
            <Box sx={{ display: 'flex', gap: 2, mt: 2, pt: 2, borderTop: 1, borderColor: 'divider' }}>
              <Button
                variant="contained"
                color="success"
                startIcon={<CheckCircle />}
                onClick={handleConfirm}
                disabled={loading}
                fullWidth
              >
                Confirm Accurate
              </Button>
              <Button
                variant="outlined"
                color="error"
                startIcon={<Gavel />}
                onClick={handleDisputeOpen}
                disabled={loading}
                fullWidth
              >
                Dispute
              </Button>
              <Button
                variant="outlined"
                startIcon={<UploadFile />}
                onClick={() => onUpload(tradeline.id)}
                disabled={loading}
                fullWidth
              >
                Upload Doc
              </Button>
            </Box>
          )}

          {tradeline.confirmation_status === 'confirmed' && (
            <Alert severity="success" sx={{ mt: 2 }}>
              <Typography variant="body2">
                Confirmed on {tradeline.confirmed_at ? new Date(tradeline.confirmed_at).toLocaleDateString() : 'N/A'}
              </Typography>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Dispute Dialog */}
      <Dialog
        open={disputeDialogOpen}
        onClose={() => !loading && setDisputeDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Dispute Tradeline</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Please provide a detailed reason for disputing this tradeline. This information will be reviewed by your
            loan officer.
          </Typography>
          <TextField
            autoFocus
            margin="dense"
            label="Dispute Reason"
            type="text"
            fullWidth
            multiline
            rows={4}
            value={disputeReason}
            onChange={(e) => setDisputeReason(e.target.value)}
            placeholder="e.g., This account was paid off in 2023 but still shows a balance..."
            required
            disabled={loading}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDisputeDialogOpen(false)} disabled={loading}>
            Cancel
          </Button>
          <Button onClick={handleDisputeSubmit} variant="contained" color="error" disabled={loading}>
            Submit Dispute
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default TradelineConfirmationCard;
