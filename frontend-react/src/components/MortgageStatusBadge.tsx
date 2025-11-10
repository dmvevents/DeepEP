import { Chip, Tooltip, type ChipProps } from '@mui/material';
import WarningIcon from '@mui/icons-material/Warning';
import InfoIcon from '@mui/icons-material/Info';
import ErrorIcon from '@mui/icons-material/Error';
import HelpIcon from '@mui/icons-material/Help';

export type MortgageStatusType =
  | 'forbearance'
  | 'modification'
  | 'transfer'
  | 'foreclosure'
  | null;

export interface MortgageStatus {
  type: MortgageStatusType;
  description?: string;
  startDate?: string;
  endDate?: string;
  notes?: string;
}

interface MortgageStatusBadgeProps {
  status: MortgageStatus;
  size?: ChipProps['size'];
  onClick?: () => void;
}

const STATUS_CONFIG: Record<Exclude<MortgageStatusType, null>, {
  label: string;
  color: ChipProps['color'];
  icon: React.ReactElement;
  tooltip: string;
}> = {
  forbearance: {
    label: 'Forbearance',
    color: 'warning',
    icon: <WarningIcon fontSize="small" />,
    tooltip: 'Temporary pause or reduction in mortgage payments due to financial hardship',
  },
  modification: {
    label: 'Modification',
    color: 'info',
    icon: <InfoIcon fontSize="small" />,
    tooltip: 'Permanent change to loan terms to make payments more affordable',
  },
  transfer: {
    label: 'Transfer',
    color: 'default',
    icon: <HelpIcon fontSize="small" />,
    tooltip: 'Mortgage ownership or servicing has been transferred to another entity',
  },
  foreclosure: {
    label: 'Foreclosure',
    color: 'error',
    icon: <ErrorIcon fontSize="small" />,
    tooltip: 'Legal process where lender attempts to recover loan balance due to non-payment',
  },
};

/**
 * MortgageStatusBadge component displays a status badge with tooltip
 * for mortgage-related alerts (forbearance, modification, transfer, foreclosure)
 *
 * Acceptance Criteria:
 * - Renders badge with appropriate color and icon
 * - Shows tooltip with status description on hover
 * - Supports click interaction for detailed dialog
 * - Accessible with aria-label and keyboard navigation
 */
export default function MortgageStatusBadge({
  status,
  size = 'small',
  onClick,
}: MortgageStatusBadgeProps) {
  if (!status.type) {
    return null;
  }

  const config = STATUS_CONFIG[status.type];
  if (!config) {
    return null;
  }

  const tooltipText = status.description || config.tooltip;

  return (
    <Tooltip
      title={tooltipText}
      arrow
      enterDelay={300}
      leaveDelay={200}
    >
      <Chip
        icon={config.icon}
        label={config.label}
        color={config.color}
        size={size}
        onClick={onClick}
        aria-label={`${config.label}: ${tooltipText}`}
        sx={{
          fontWeight: 600,
          cursor: onClick ? 'pointer' : 'default',
          '&:hover': onClick ? {
            opacity: 0.8,
          } : undefined,
        }}
      />
    </Tooltip>
  );
}
