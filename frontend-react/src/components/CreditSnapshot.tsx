import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  Divider,
  Alert,
  LinearProgress,
  Stack,
} from '@mui/material';
import {
  CreditScore as CreditScoreIcon,
  TrendingUp,
  TrendingDown,
  Assessment,
} from '@mui/icons-material';
import type { CreditSnapshot as CreditSnapshotType } from '../types/credit';
import { formatCurrency } from '../utils/formatters';

interface CreditSnapshotProps {
  snapshot: CreditSnapshotType;
  loading?: boolean;
}

const CreditSnapshot: React.FC<CreditSnapshotProps> = ({ snapshot, loading = false }) => {
  const { credit_report, tradelines, inquiries, summary } = snapshot;

  const getScoreColor = (score: number | null): string => {
    if (!score) return 'default';
    if (score >= 740) return 'success';
    if (score >= 670) return 'info';
    if (score >= 580) return 'warning';
    return 'error';
  };

  const getScoreLabel = (score: number | null): string => {
    if (!score) return 'Unknown';
    if (score >= 740) return 'Excellent';
    if (score >= 670) return 'Good';
    if (score >= 580) return 'Fair';
    return 'Needs Work';
  };

  if (loading) {
    return (
      <Card>
        <CardContent>
          <Box sx={{ mb: 2 }}>
            <Typography variant="h6" gutterBottom>
              Loading Credit Report...
            </Typography>
            <LinearProgress />
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (credit_report.status === 'error') {
    return (
      <Card>
        <CardContent>
          <Alert severity="error">
            <Typography variant="body2">{credit_report.error_message || 'Error loading credit report'}</Typography>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  const middleScore = credit_report.middle_score;
  const scoreColor = getScoreColor(middleScore);
  const scoreLabel = getScoreLabel(middleScore);

  return (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <CreditScoreIcon color="primary" />
        Credit Snapshot
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom sx={{ mb: 3 }}>
        Report pulled on {new Date(credit_report.report_date).toLocaleDateString()}
      </Typography>

      {/* Credit Scores */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Credit Scores
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} md={3}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="subtitle2" color="text.secondary">
                  Middle Score
                </Typography>
                <Typography variant="h3" color={`${scoreColor}.main`} sx={{ fontWeight: 'bold', my: 1 }}>
                  {middleScore || 'N/A'}
                </Typography>
                <Chip label={scoreLabel} color={scoreColor as any} size="small" />
              </Box>
            </Grid>
            <Grid item xs={12} md={3}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="subtitle2" color="text.secondary">
                  Equifax
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 'bold', my: 1 }}>
                  {credit_report.equifax_score || 'N/A'}
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} md={3}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="subtitle2" color="text.secondary">
                  Experian
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 'bold', my: 1 }}>
                  {credit_report.experian_score || 'N/A'}
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={12} md={3}>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="subtitle2" color="text.secondary">
                  TransUnion
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 'bold', my: 1 }}>
                  {credit_report.transunion_score || 'N/A'}
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Summary Statistics */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Assessment />
            Credit Summary
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={6} sm={4}>
              <Typography variant="subtitle2" color="text.secondary">
                Total Accounts
              </Typography>
              <Typography variant="h6">{summary.total_accounts}</Typography>
            </Grid>
            <Grid item xs={6} sm={4}>
              <Typography variant="subtitle2" color="text.secondary">
                Open Accounts
              </Typography>
              <Typography variant="h6">{summary.open_accounts}</Typography>
            </Grid>
            <Grid item xs={6} sm={4}>
              <Typography variant="subtitle2" color="text.secondary">
                Total Balance
              </Typography>
              <Typography variant="h6">{formatCurrency(parseFloat(summary.total_balance))}</Typography>
            </Grid>
            <Grid item xs={6} sm={4}>
              <Typography variant="subtitle2" color="text.secondary">
                Monthly Payment
              </Typography>
              <Typography variant="h6">{formatCurrency(parseFloat(summary.total_monthly_payment))}</Typography>
            </Grid>
            <Grid item xs={6} sm={4}>
              <Typography variant="subtitle2" color="text.secondary">
                Credit Utilization
              </Typography>
              <Typography variant="h6">
                {summary.credit_utilization ? `${summary.credit_utilization.toFixed(1)}%` : 'N/A'}
              </Typography>
            </Grid>
            <Grid item xs={6} sm={4}>
              <Typography variant="subtitle2" color="text.secondary">
                Derogatory Marks
              </Typography>
              <Typography variant="h6" color={summary.derogatory_marks > 0 ? 'error' : 'success'}>
                {summary.derogatory_marks}
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Recent Inquiries */}
      {inquiries.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Recent Credit Inquiries ({inquiries.length})
            </Typography>
            <Stack spacing={1} divider={<Divider />}>
              {inquiries.slice(0, 5).map((inquiry, index) => (
                <Box key={index} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Box>
                    <Typography variant="body2" fontWeight="medium">
                      {inquiry.creditor_name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {new Date(inquiry.inquiry_date).toLocaleDateString()}
                    </Typography>
                  </Box>
                  <Chip
                    label={inquiry.inquiry_type === 'hard' ? 'Hard Pull' : 'Soft Pull'}
                    size="small"
                    color={inquiry.inquiry_type === 'hard' ? 'warning' : 'default'}
                    icon={inquiry.inquiry_type === 'hard' ? <TrendingDown /> : <TrendingUp />}
                  />
                </Box>
              ))}
            </Stack>
            {inquiries.length > 5 && (
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2 }}>
                Showing 5 of {inquiries.length} inquiries
              </Typography>
            )}
          </CardContent>
        </Card>
      )}

      {/* Tradelines Count */}
      <Alert severity="info" sx={{ mb: 2 }}>
        <Typography variant="body2">
          <strong>{tradelines.length} tradeline{tradelines.length !== 1 ? 's' : ''}</strong> found on your credit
          report. Please review each account below and confirm the information is accurate.
        </Typography>
      </Alert>
    </Box>
  );
};

export default CreditSnapshot;
