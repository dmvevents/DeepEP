import { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Checkbox,
  FormControlLabel,
  Box,
  Alert,
  Divider,
  Link,
} from '@mui/material';
import InfoIcon from '@mui/icons-material/Info';
import VerifiedUserIcon from '@mui/icons-material/VerifiedUser';

interface CreditConsentModalProps {
  open: boolean;
  onAccept: () => void;
  borrowerName: string;
  ssn?: string;
  isLoading?: boolean;
}

/**
 * CFPB-compliant credit consent modal
 * References the 45-day rate-shopping window per CFPB guidance
 * Blocks progression until accepted
 */
const CreditConsentModal = ({
  open,
  onAccept,
  borrowerName,
  ssn,
  isLoading = false,
}: CreditConsentModalProps) => {
  const [consentChecked, setConsentChecked] = useState(false);
  const [acknowledgementChecked, setAcknowledgementChecked] = useState(false);

  const handleAccept = () => {
    if (!consentChecked || !acknowledgementChecked) {
      return;
    }
    onAccept();
  };

  const canAccept = consentChecked && acknowledgementChecked && !isLoading;

  return (
    <Dialog
      open={open}
      maxWidth="md"
      fullWidth
      disableEscapeKeyDown
      aria-labelledby="credit-consent-dialog-title"
      aria-describedby="credit-consent-dialog-description"
    >
      <DialogTitle
        id="credit-consent-dialog-title"
        sx={{
          bgcolor: 'primary.main',
          color: 'white',
          display: 'flex',
          alignItems: 'center',
          gap: 1,
        }}
      >
        <VerifiedUserIcon />
        <Typography variant="h6" component="span">
          Credit Report Authorization
        </Typography>
      </DialogTitle>

      <DialogContent sx={{ mt: 2 }}>
        <Alert severity="info" icon={<InfoIcon />} sx={{ mb: 3 }}>
          <Typography variant="body2" fontWeight={600}>
            This authorization is required before we can pull your credit report.
          </Typography>
        </Alert>

        <Box id="credit-consent-dialog-description">
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mt: 2 }}>
            Authorization to Obtain Credit Report
          </Typography>

          <Typography variant="body1" paragraph>
            I/We, <strong>{borrowerName || '[Borrower Name]'}</strong>
            {ssn && ` (SSN ending in ${ssn.slice(-4)})`}, hereby authorize{' '}
            <strong>Real Estate Mortgage Calculator</strong> and its designated consumer
            reporting agencies to obtain my/our consumer credit report(s) for the purpose
            of evaluating my/our mortgage loan application.
          </Typography>

          <Divider sx={{ my: 2 }} />

          <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mt: 2 }}>
            CFPB 45-Day Rate Shopping Window
          </Typography>

          <Typography variant="body1" paragraph>
            Under federal law and Consumer Financial Protection Bureau (CFPB) guidance,
            multiple credit inquiries for a mortgage within a <strong>45-day period</strong>{' '}
            are treated as a single inquiry for credit scoring purposes. This allows you to
            shop for the best mortgage rate without negatively impacting your credit score.
          </Typography>

          <Alert severity="success" sx={{ mb: 2 }}>
            <Typography variant="body2">
              <strong>Rate Shopping Protection:</strong> You may apply with multiple lenders
              within 45 days, and all inquiries will count as one inquiry on your credit report.
            </Typography>
          </Alert>

          <Typography variant="body2" color="text.secondary" paragraph>
            <strong>Important:</strong> This protection applies specifically to mortgage-related
            inquiries. The 45-day window begins from the date of your first mortgage inquiry.
          </Typography>

          <Divider sx={{ my: 2 }} />

          <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mt: 2 }}>
            Your Rights
          </Typography>

          <Box component="ul" sx={{ pl: 2, mt: 1 }}>
            <Typography component="li" variant="body2" paragraph>
              You have the right to request a copy of your credit report
            </Typography>
            <Typography component="li" variant="body2" paragraph>
              You may dispute any inaccurate information on your credit report
            </Typography>
            <Typography component="li" variant="body2" paragraph>
              Credit reports will be used solely for mortgage loan evaluation
            </Typography>
            <Typography component="li" variant="body2" paragraph>
              Your information will be protected according to the{' '}
              <Link
                href="https://www.ftc.gov/legal-library/browse/rules/gramm-leach-bliley-act"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="Learn more about Gramm-Leach-Bliley Act (opens in new tab)"
              >
                Gramm-Leach-Bliley Act
              </Link>
            </Typography>
          </Box>

          <Divider sx={{ my: 2 }} />

          <Box sx={{ mt: 3, bgcolor: '#f5f5f5', p: 2, borderRadius: 1 }}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={consentChecked}
                  onChange={(e) => setConsentChecked(e.target.checked)}
                  color="primary"
                  inputProps={{
                    'aria-label': 'I authorize the credit report pull',
                  }}
                />
              }
              label={
                <Typography variant="body2">
                  <strong>I authorize</strong> the obtaining of my consumer credit report(s)
                  for mortgage loan evaluation purposes
                </Typography>
              }
            />

            <FormControlLabel
              control={
                <Checkbox
                  checked={acknowledgementChecked}
                  onChange={(e) => setAcknowledgementChecked(e.target.checked)}
                  color="primary"
                  inputProps={{
                    'aria-label': 'I understand the 45-day rate shopping window',
                  }}
                />
              }
              label={
                <Typography variant="body2">
                  <strong>I understand</strong> that I have a 45-day rate shopping window
                  during which multiple mortgage credit inquiries will be treated as a single
                  inquiry
                </Typography>
              }
            />
          </Box>

          <Alert severity="warning" sx={{ mt: 2 }}>
            <Typography variant="body2">
              <strong>Required:</strong> Both checkboxes must be selected to proceed with your
              mortgage application.
            </Typography>
          </Alert>
        </Box>
      </DialogContent>

      <DialogActions sx={{ p: 2, bgcolor: '#f9fafb' }}>
        <Button
          variant="contained"
          color="primary"
          size="large"
          onClick={handleAccept}
          disabled={!canAccept}
          fullWidth
          sx={{
            py: 1.5,
            fontSize: '1rem',
            fontWeight: 600,
          }}
          aria-label="Accept credit authorization and continue"
        >
          {isLoading ? 'Processing...' : 'Accept & Continue'}
        </Button>
      </DialogActions>

      <Box sx={{ px: 2, pb: 2, textAlign: 'center' }}>
        <Typography variant="caption" color="text.secondary">
          By clicking "Accept & Continue", you electronically sign this authorization
        </Typography>
      </Box>
    </Dialog>
  );
};

export default CreditConsentModal;
