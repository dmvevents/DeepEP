import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Box,
  Button,
  Divider,
  Stack,
} from '@mui/material';
import HomeIcon from '@mui/icons-material/Home';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import { formatCurrency } from '../utils/formatters';
import MortgageStatusBadge, { type MortgageStatus } from './MortgageStatusBadge';

export interface MortgageCardData {
  id: number;
  propertyAddress: string;
  loanAmount: number;
  monthlyPayment: number;
  interestRate: number;
  closingDate?: string;
  status?: MortgageStatus;
}

interface MortgageCardProps {
  mortgage: MortgageCardData;
  onViewDetails?: (id: number) => void;
  onStatusClick?: (mortgage: MortgageCardData) => void;
}

/**
 * MortgageCard component displays mortgage information with status badge
 *
 * Acceptance Criteria:
 * - Displays key mortgage details (address, amount, payment)
 * - Shows MortgageStatusBadge when status is present
 * - Provides action buttons for viewing details
 * - Responsive layout with proper spacing
 * - Accessible with semantic HTML and aria labels
 */
export default function MortgageCard({
  mortgage,
  onViewDetails,
  onStatusClick,
}: MortgageCardProps) {
  const handleStatusClick = () => {
    if (onStatusClick && mortgage.status?.type) {
      onStatusClick(mortgage);
    }
  };

  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        transition: 'box-shadow 0.3s ease-in-out',
        '&:hover': {
          boxShadow: (theme) => theme.shadows[8],
        },
      }}
      role="article"
      aria-label={`Mortgage for ${mortgage.propertyAddress}`}
    >
      <CardContent sx={{ flexGrow: 1 }}>
        {/* Header with Status Badge */}
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            mb: 2,
            gap: 1,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 0 }}>
            <HomeIcon color="primary" />
            <Typography
              variant="h6"
              component="h3"
              sx={{
                fontWeight: 600,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              Property Loan
            </Typography>
          </Box>
          {mortgage.status?.type && (
            <MortgageStatusBadge
              status={mortgage.status}
              onClick={onStatusClick ? handleStatusClick : undefined}
            />
          )}
        </Box>

        {/* Property Address */}
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{
            mb: 2,
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
          }}
          title={mortgage.propertyAddress}
        >
          {mortgage.propertyAddress}
        </Typography>

        <Divider sx={{ my: 2 }} />

        {/* Financial Details */}
        <Stack spacing={1.5}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <AttachMoneyIcon fontSize="small" color="action" />
              <Typography variant="body2" color="text.secondary">
                Loan Amount
              </Typography>
            </Box>
            <Typography variant="body1" fontWeight={600}>
              {formatCurrency(mortgage.loanAmount)}
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="body2" color="text.secondary" sx={{ ml: 4 }}>
              Monthly Payment
            </Typography>
            <Typography variant="body1" fontWeight={600} color="primary">
              {formatCurrency(mortgage.monthlyPayment)}/mo
            </Typography>
          </Box>

          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="body2" color="text.secondary" sx={{ ml: 4 }}>
              Interest Rate
            </Typography>
            <Typography variant="body1" fontWeight={600}>
              {mortgage.interestRate.toFixed(3)}%
            </Typography>
          </Box>

          {mortgage.closingDate && (
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CalendarTodayIcon fontSize="small" color="action" />
                <Typography variant="body2" color="text.secondary">
                  Closing Date
                </Typography>
              </Box>
              <Typography variant="body2" fontWeight={500}>
                {new Date(mortgage.closingDate).toLocaleDateString()}
              </Typography>
            </Box>
          )}
        </Stack>
      </CardContent>

      {onViewDetails && (
        <CardActions sx={{ px: 2, pb: 2 }}>
          <Button
            size="small"
            variant="outlined"
            fullWidth
            onClick={() => onViewDetails(mortgage.id)}
            aria-label={`View details for ${mortgage.propertyAddress}`}
          >
            View Details
          </Button>
        </CardActions>
      )}
    </Card>
  );
}
