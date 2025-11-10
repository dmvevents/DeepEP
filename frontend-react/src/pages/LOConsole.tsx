import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Container,
  Box,
  Typography,
  Paper,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Switch,
  Tooltip,
  Alert,
  AlertTitle,
  CircularProgress,
  Card,
  CardContent,
  Grid,
  IconButton,
  Divider,
  FormControlLabel,
} from '@mui/material';
import {
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  Visibility as VisibilityIcon,
} from '@mui/icons-material';
import Navbar from '../components/Navbar';
import { creditApi } from '../services/api';
import type { CreditSnapshot, DocTask, Tradeline } from '../types/credit';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`lo-console-tabpanel-${index}`}
      aria-labelledby={`lo-console-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

interface TradelineIncludeState {
  [key: number]: boolean;
}

interface TaskIncludeState {
  [key: number]: boolean;
}

interface DTIPreview {
  totalMonthlyIncome: number;
  totalMonthlyDebts: number;
  housingPayment: number;
  dtiRatio: number;
  frontEndDti: number;
  includeRule: string;
}

const LOConsole = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const loanEstimateId = searchParams.get('loan_estimate_id');

  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [snapshot, setSnapshot] = useState<CreditSnapshot | null>(null);
  const [docTasks, setDocTasks] = useState<DocTask[]>([]);
  const [tradelineIncludes, setTradelineIncludes] = useState<TradelineIncludeState>({});
  const [taskIncludes, setTaskIncludes] = useState<TaskIncludeState>({});
  const [dtiPreview, setDtiPreview] = useState<DTIPreview | null>(null);

  // Check RBAC - only loan officers should access this page
  useEffect(() => {
    const user = localStorage.getItem('user');
    if (user) {
      const userData = JSON.parse(user);
      if (!userData.is_admin && !userData.is_loan_officer) {
        setError('Access denied. This page is only available to loan officers.');
        setLoading(false);
        return;
      }
    }
  }, []);

  // Load data on mount
  useEffect(() => {
    if (!loanEstimateId) {
      setError('No loan estimate ID provided');
      setLoading(false);
      return;
    }

    loadData();
  }, [loanEstimateId]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load credit snapshot and doc tasks in parallel
      const [snapshotData, tasksData] = await Promise.all([
        creditApi.getCreditSnapshot(Number(loanEstimateId)),
        creditApi.getDocTasks(Number(loanEstimateId)),
      ]);

      setSnapshot(snapshotData);
      setDocTasks(tasksData);

      // Initialize all tradelines as included by default
      const tradelineState: TradelineIncludeState = {};
      snapshotData.tradelines.forEach((tradeline) => {
        tradelineState[tradeline.id] = true;
      });
      setTradelineIncludes(tradelineState);

      // Initialize all tasks as included by default
      const taskState: TaskIncludeState = {};
      tasksData.forEach((task) => {
        taskState[task.id] = true;
      });
      setTaskIncludes(taskState);

      // Calculate initial DTI
      calculateDTI(snapshotData.tradelines, tradelineState);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const calculateDTI = (tradelines: Tradeline[], includeState: TradelineIncludeState) => {
    // Calculate total monthly debts from included tradelines
    const totalDebts = tradelines
      .filter((t) => includeState[t.id])
      .reduce((sum, t) => sum + parseFloat(t.monthly_payment || '0'), 0);

    // Mock housing payment and income (in production, fetch from loan estimate)
    const mockHousingPayment = 2500;
    const mockMonthlyIncome = 8000;

    const frontEndDti = (mockHousingPayment / mockMonthlyIncome) * 100;
    const backEndDti = ((mockHousingPayment + totalDebts) / mockMonthlyIncome) * 100;

    // Determine which rule to apply based on DTI
    let rule = 'Fannie Mae Standard (DTI ≤ 36%)';
    if (backEndDti > 43) {
      rule = 'FHA Manual UW (DTI ≤ 50%)';
    } else if (backEndDti > 36) {
      rule = 'Fannie Mae Expanded (DTI ≤ 43%)';
    }

    setDtiPreview({
      totalMonthlyIncome: mockMonthlyIncome,
      totalMonthlyDebts: totalDebts,
      housingPayment: mockHousingPayment,
      dtiRatio: backEndDti,
      frontEndDti,
      includeRule: rule,
    });
  };

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleTradelineToggle = (tradelineId: number) => {
    const newState = {
      ...tradelineIncludes,
      [tradelineId]: !tradelineIncludes[tradelineId],
    };
    setTradelineIncludes(newState);

    // Recalculate DTI
    if (snapshot) {
      calculateDTI(snapshot.tradelines, newState);
    }
  };

  const handleTaskToggle = (taskId: number) => {
    setTaskIncludes({
      ...taskIncludes,
      [taskId]: !taskIncludes[taskId],
    });
  };

  const getAccountTypeColor = (accountType: string) => {
    switch (accountType) {
      case 'mortgage':
        return 'primary';
      case 'auto':
        return 'secondary';
      case 'credit_card':
        return 'warning';
      case 'student':
        return 'info';
      case 'collection':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'in_progress':
        return 'primary';
      case 'pending':
        return 'warning';
      case 'cancelled':
        return 'error';
      default:
        return 'default';
    }
  };

  const getDTIColor = (dti: number) => {
    if (dti <= 36) return 'success';
    if (dti <= 43) return 'warning';
    return 'error';
  };

  if (loading) {
    return (
      <>
        <Navbar title="LO Console" />
        <Box
          sx={{
            minHeight: 'calc(100vh - 64px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <CircularProgress />
        </Box>
      </>
    );
  }

  if (error) {
    return (
      <>
        <Navbar title="LO Console" />
        <Container maxWidth="lg" sx={{ py: 4 }}>
          <Alert severity="error">
            <AlertTitle>Error</AlertTitle>
            {error}
          </Alert>
        </Container>
      </>
    );
  }

  return (
    <>
      <Navbar title="LO Console" />
      <Box
        sx={{
          minHeight: 'calc(100vh - 64px)',
          width: '100%',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          py: { xs: 2, sm: 3, md: 4 },
          px: { xs: 1, sm: 2, md: 3 },
        }}
      >
        <Container maxWidth="xl">
          {/* Header */}
          <Box textAlign="center" mb={4}>
            <Typography
              variant="h3"
              component="h1"
              gutterBottom
              sx={{
                color: 'white',
                fontWeight: 700,
                fontSize: { xs: '1.75rem', sm: '2.5rem', md: '3rem' },
              }}
            >
              Loan Officer Console
            </Typography>
            <Typography
              variant="h6"
              sx={{
                color: 'white',
                opacity: 0.9,
                fontSize: { xs: '1rem', sm: '1.125rem', md: '1.25rem' },
              }}
            >
              Manage credit tradelines and document tasks for Loan #{loanEstimateId}
            </Typography>
          </Box>

          {/* DTI Preview Card */}
          {dtiPreview && (
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Grid container spacing={3} alignItems="center">
                  <Grid item xs={12} md={8}>
                    <Typography variant="h6" gutterBottom>
                      DTI Preview
                    </Typography>
                    <Grid container spacing={2}>
                      <Grid item xs={6} sm={3}>
                        <Typography variant="body2" color="text.secondary">
                          Monthly Income
                        </Typography>
                        <Typography variant="h6">
                          ${dtiPreview.totalMonthlyIncome.toLocaleString()}
                        </Typography>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Typography variant="body2" color="text.secondary">
                          Housing Payment
                        </Typography>
                        <Typography variant="h6">
                          ${dtiPreview.housingPayment.toLocaleString()}
                        </Typography>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Typography variant="body2" color="text.secondary">
                          Total Debts
                        </Typography>
                        <Typography variant="h6">
                          ${dtiPreview.totalMonthlyDebts.toFixed(2)}
                        </Typography>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Typography variant="body2" color="text.secondary">
                          Back-End DTI
                        </Typography>
                        <Chip
                          label={`${dtiPreview.dtiRatio.toFixed(1)}%`}
                          color={getDTIColor(dtiPreview.dtiRatio)}
                          sx={{ fontWeight: 600, fontSize: '1rem' }}
                        />
                      </Grid>
                    </Grid>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Alert severity={getDTIColor(dtiPreview.dtiRatio)} icon={<InfoIcon />}>
                      <Typography variant="body2" fontWeight={600}>
                        Recommended Guideline
                      </Typography>
                      <Typography variant="body2">{dtiPreview.includeRule}</Typography>
                    </Alert>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          )}

          {/* Tabs */}
          <Paper>
            <Tabs
              value={tabValue}
              onChange={handleTabChange}
              variant="fullWidth"
              sx={{ borderBottom: 1, borderColor: 'divider' }}
              aria-label="LO Console tabs"
            >
              <Tab
                label="Credit Tradelines"
                id="lo-console-tab-0"
                aria-controls="lo-console-tabpanel-0"
                icon={<CheckCircleIcon />}
                iconPosition="start"
              />
              <Tab
                label="Document Tasks"
                id="lo-console-tab-1"
                aria-controls="lo-console-tabpanel-1"
                icon={<WarningIcon />}
                iconPosition="start"
              />
            </Tabs>

            {/* Tab 1: Credit Tradelines */}
            <TabPanel value={tabValue} index={0}>
              <Box sx={{ p: { xs: 2, sm: 3 } }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                  <Typography variant="h5">Credit Tradelines</Typography>
                  <IconButton onClick={loadData} color="primary" aria-label="Refresh data">
                    <RefreshIcon />
                  </IconButton>
                </Box>

                <Alert severity="info" sx={{ mb: 3 }}>
                  <AlertTitle>Include/Exclude Tradelines</AlertTitle>
                  Toggle tradelines to include or exclude them from DTI calculations. Changes are reflected in
                  real-time in the DTI Preview above.
                </Alert>

                {snapshot && snapshot.tradelines.length > 0 ? (
                  <TableContainer sx={{ overflowX: 'auto' }}>
                    <Table sx={{ minWidth: 650 }} aria-label="credit tradelines table">
                      <TableHead>
                        <TableRow>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              Include
                              <Tooltip
                                title="Toggle to include or exclude this tradeline from DTI calculations"
                                arrow
                              >
                                <InfoIcon fontSize="small" sx={{ color: 'text.secondary' }} />
                              </Tooltip>
                            </Box>
                          </TableCell>
                          <TableCell>Creditor</TableCell>
                          <TableCell>Account Type</TableCell>
                          <TableCell>Current Balance</TableCell>
                          <TableCell>Monthly Payment</TableCell>
                          <TableCell>Status</TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              Rule
                              <Tooltip
                                title="Underwriting rule that determines if this tradeline should be included in DTI"
                                arrow
                              >
                                <InfoIcon fontSize="small" sx={{ color: 'text.secondary' }} />
                              </Tooltip>
                            </Box>
                          </TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {snapshot.tradelines.map((tradeline) => {
                          const isIncluded = tradelineIncludes[tradeline.id];
                          const hasHighBalance = parseFloat(tradeline.current_balance) > 10000;
                          const ruleText = hasHighBalance
                            ? 'Include: Balance > $10K'
                            : 'Exclude: Balance ≤ $10K';

                          return (
                            <TableRow key={tradeline.id} hover>
                              <TableCell>
                                <FormControlLabel
                                  control={
                                    <Switch
                                      checked={isIncluded}
                                      onChange={() => handleTradelineToggle(tradeline.id)}
                                      color="primary"
                                      inputProps={{
                                        'aria-label': `Include ${tradeline.creditor_name} in DTI calculation`,
                                      }}
                                    />
                                  }
                                  label=""
                                />
                              </TableCell>
                              <TableCell>{tradeline.creditor_name}</TableCell>
                              <TableCell>
                                <Chip
                                  label={tradeline.account_type}
                                  color={getAccountTypeColor(tradeline.account_type)}
                                  size="small"
                                />
                              </TableCell>
                              <TableCell>${parseFloat(tradeline.current_balance).toLocaleString()}</TableCell>
                              <TableCell>${parseFloat(tradeline.monthly_payment).toFixed(2)}</TableCell>
                              <TableCell>
                                <Chip label={tradeline.status} size="small" />
                              </TableCell>
                              <TableCell>
                                <Tooltip title={ruleText} arrow placement="top">
                                  <Chip
                                    icon={<InfoIcon />}
                                    label={hasHighBalance ? 'Include' : 'Exclude'}
                                    color={hasHighBalance ? 'success' : 'default'}
                                    size="small"
                                    variant="outlined"
                                  />
                                </Tooltip>
                              </TableCell>
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                  </TableContainer>
                ) : (
                  <Alert severity="info">No credit tradelines found for this loan estimate.</Alert>
                )}
              </Box>
            </TabPanel>

            {/* Tab 2: Document Tasks */}
            <TabPanel value={tabValue} index={1}>
              <Box sx={{ p: { xs: 2, sm: 3 } }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                  <Typography variant="h5">Document Tasks</Typography>
                  <IconButton onClick={loadData} color="primary" aria-label="Refresh data">
                    <RefreshIcon />
                  </IconButton>
                </Box>

                <Alert severity="info" sx={{ mb: 3 }}>
                  <AlertTitle>Manage Document Requirements</AlertTitle>
                  Toggle tasks to mark them as required or optional. Completed tasks are automatically included in
                  underwriting review.
                </Alert>

                {docTasks.length > 0 ? (
                  <TableContainer sx={{ overflowX: 'auto' }}>
                    <Table sx={{ minWidth: 650 }} aria-label="document tasks table">
                      <TableHead>
                        <TableRow>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              Required
                              <Tooltip title="Toggle to mark this task as required or optional" arrow>
                                <InfoIcon fontSize="small" sx={{ color: 'text.secondary' }} />
                              </Tooltip>
                            </Box>
                          </TableCell>
                          <TableCell>Title</TableCell>
                          <TableCell>Task Type</TableCell>
                          <TableCell>Status</TableCell>
                          <TableCell>Due Date</TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              Compliance Rule
                              <Tooltip
                                title="Compliance requirement that determines if this task is mandatory"
                                arrow
                              >
                                <InfoIcon fontSize="small" sx={{ color: 'text.secondary' }} />
                              </Tooltip>
                            </Box>
                          </TableCell>
                          <TableCell>Actions</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {docTasks.map((task) => {
                          const isRequired = taskIncludes[task.id];
                          const isCritical = task.task_type === 'verify_income' || task.task_type === 'verify_assets';
                          const ruleText = isCritical
                            ? 'Required: CFPB ATR verification'
                            : 'Optional: Supplemental documentation';

                          return (
                            <TableRow key={task.id} hover>
                              <TableCell>
                                <FormControlLabel
                                  control={
                                    <Switch
                                      checked={isRequired}
                                      onChange={() => handleTaskToggle(task.id)}
                                      color="primary"
                                      inputProps={{
                                        'aria-label': `Mark ${task.title} as required`,
                                      }}
                                    />
                                  }
                                  label=""
                                />
                              </TableCell>
                              <TableCell>
                                <Typography variant="body2" fontWeight={600}>
                                  {task.title}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  {task.description}
                                </Typography>
                              </TableCell>
                              <TableCell>
                                <Chip label={task.task_type_display} size="small" />
                              </TableCell>
                              <TableCell>
                                <Chip
                                  label={task.status_display}
                                  color={getStatusColor(task.status)}
                                  size="small"
                                />
                              </TableCell>
                              <TableCell>
                                {task.due_date ? (
                                  <Box>
                                    <Typography variant="body2">
                                      {new Date(task.due_date).toLocaleDateString()}
                                    </Typography>
                                    {task.is_overdue && (
                                      <Chip
                                        icon={<WarningIcon />}
                                        label="Overdue"
                                        color="error"
                                        size="small"
                                        sx={{ mt: 0.5 }}
                                      />
                                    )}
                                  </Box>
                                ) : (
                                  <Typography variant="body2" color="text.secondary">
                                    No due date
                                  </Typography>
                                )}
                              </TableCell>
                              <TableCell>
                                <Tooltip title={ruleText} arrow placement="top">
                                  <Chip
                                    icon={isCritical ? <ErrorIcon /> : <InfoIcon />}
                                    label={isCritical ? 'Required' : 'Optional'}
                                    color={isCritical ? 'error' : 'default'}
                                    size="small"
                                    variant="outlined"
                                  />
                                </Tooltip>
                              </TableCell>
                              <TableCell>
                                <Tooltip title="View task details" arrow>
                                  <IconButton
                                    size="small"
                                    color="primary"
                                    onClick={() => navigate(`/documents-portal?loan_estimate_id=${loanEstimateId}`)}
                                    aria-label={`View details for ${task.title}`}
                                  >
                                    <VisibilityIcon />
                                  </IconButton>
                                </Tooltip>
                              </TableCell>
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                  </TableContainer>
                ) : (
                  <Alert severity="info">No document tasks found for this loan estimate.</Alert>
                )}
              </Box>
            </TabPanel>
          </Paper>

          {/* Footer Actions */}
          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Divider sx={{ mb: 2 }} />
            <Typography variant="body2" color="white" sx={{ opacity: 0.8 }}>
              Loan Officer Console • RBAC Protected • Real-time DTI Updates
            </Typography>
          </Box>
        </Container>
      </Box>
    </>
  );
};

export default LOConsole;
