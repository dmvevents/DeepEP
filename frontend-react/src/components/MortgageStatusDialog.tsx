import { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  TextField,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Stack,
} from '@mui/material';
import WarningIcon from '@mui/icons-material/Warning';
import InfoIcon from '@mui/icons-material/Info';
import type { MortgageStatus, MortgageStatusType } from './MortgageStatusBadge';

interface MortgageStatusDialogProps {
  open: boolean;
  onClose: () => void;
  onSave: (status: MortgageStatus) => Promise<void> | void;
  currentStatus?: MortgageStatus;
  mortgageId?: number;
}

const STATUS_OPTIONS: { value: MortgageStatusType; label: string; description: string }[] = [
  {
    value: null,
    label: 'None',
    description: 'No special status',
  },
  {
    value: 'forbearance',
    label: 'Forbearance',
    description: 'Temporary pause or reduction in payments due to financial hardship',
  },
  {
    value: 'modification',
    label: 'Modification',
    description: 'Permanent change to loan terms to make payments more affordable',
  },
  {
    value: 'transfer',
    label: 'Transfer',
    description: 'Mortgage ownership or servicing transferred to another entity',
  },
  {
    value: 'foreclosure',
    label: 'Foreclosure',
    description: 'Legal process to recover loan balance due to non-payment',
  },
];

/**
 * MortgageStatusDialog component for updating mortgage status
 *
 * Acceptance Criteria:
 * - Prompts user when status rules trigger (e.g., delinquency detected)
 * - Allows selection of status type with descriptions
 * - Captures start/end dates and additional notes
 * - Saves status to borrower profile via API
 * - Accessible with proper form labels and keyboard navigation
 * - Shows loading state during save operation
 */
export default function MortgageStatusDialog({
  open,
  onClose,
  onSave,
  currentStatus,
}: MortgageStatusDialogProps) {
  const [statusType, setStatusType] = useState<MortgageStatusType>(
    currentStatus?.type || null
  );
  const [description, setDescription] = useState(currentStatus?.description || '');
  const [startDate, setStartDate] = useState(currentStatus?.startDate || '');
  const [endDate, setEndDate] = useState(currentStatus?.endDate || '');
  const [notes, setNotes] = useState(currentStatus?.notes || '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');

  const handleSave = async () => {
    try {
      setLoading(true);
      setError('');

      const newStatus: MortgageStatus = {
        type: statusType,
        description: description.trim() || undefined,
        startDate: startDate || undefined,
        endDate: endDate || undefined,
        notes: notes.trim() || undefined,
      };

      await onSave(newStatus);
      handleClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save status');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setError('');
      onClose();
    }
  };

  const selectedOption = STATUS_OPTIONS.find((opt) => opt.value === statusType);

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
      aria-labelledby="mortgage-status-dialog-title"
    >
      <DialogTitle id="mortgage-status-dialog-title">
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <WarningIcon color="warning" />
          <Typography variant="h6" component="span">
            Update Mortgage Status
          </Typography>
        </Box>
      </DialogTitle>

      <DialogContent>
        <Stack spacing={3} sx={{ mt: 1 }}>
          {/* Info Alert */}
          <Alert severity="info" icon={<InfoIcon />}>
            Update the mortgage status to track special circumstances like forbearance,
            modifications, or other loan events. This information is saved to your borrower
            profile.
          </Alert>

          {/* Error Alert */}
          {error && (
            <Alert severity="error" onClose={() => setError('')}>
              {error}
            </Alert>
          )}

          {/* Status Type Selection */}
          <FormControl fullWidth required>
            <InputLabel id="status-type-label">Status Type</InputLabel>
            <Select
              labelId="status-type-label"
              id="status-type-select"
              value={statusType || ''}
              label="Status Type"
              onChange={(e) => setStatusType((e.target.value || null) as MortgageStatusType)}
              aria-describedby="status-type-helper"
            >
              {STATUS_OPTIONS.map((option) => (
                <MenuItem key={option.value || 'none'} value={option.value || ''}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* Status Description */}
          {selectedOption && selectedOption.value && (
            <Alert severity="info" sx={{ py: 1 }}>
              <Typography variant="body2">{selectedOption.description}</Typography>
            </Alert>
          )}

          {/* Custom Description */}
          {statusType && (
            <>
              <TextField
                fullWidth
                label="Additional Description"
                multiline
                rows={2}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Add any additional details about this status"
                inputProps={{
                  maxLength: 500,
                  'aria-label': 'Additional description',
                }}
                helperText={`${description.length}/500 characters`}
              />

              {/* Date Fields */}
              <Box sx={{ display: 'flex', gap: 2 }}>
                <TextField
                  fullWidth
                  label="Start Date"
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  InputLabelProps={{ shrink: true }}
                  inputProps={{
                    'aria-label': 'Status start date',
                  }}
                />
                <TextField
                  fullWidth
                  label="End Date (Optional)"
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  InputLabelProps={{ shrink: true }}
                  inputProps={{
                    'aria-label': 'Status end date',
                    min: startDate || undefined,
                  }}
                  disabled={!startDate}
                />
              </Box>

              {/* Notes */}
              <TextField
                fullWidth
                label="Internal Notes"
                multiline
                rows={3}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Add any internal notes or reminders"
                inputProps={{
                  maxLength: 1000,
                  'aria-label': 'Internal notes',
                }}
                helperText={`${notes.length}/1000 characters`}
              />
            </>
          )}
        </Stack>
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 2, gap: 1 }}>
        <Button
          onClick={handleClose}
          disabled={loading}
          aria-label="Cancel and close dialog"
        >
          Cancel
        </Button>
        <Button
          onClick={handleSave}
          variant="contained"
          disabled={loading}
          aria-label="Save mortgage status"
        >
          {loading ? 'Saving...' : 'Save Status'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
