import React, { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Grid,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Button,
  Chip,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableRow,
  Paper,
  Stack,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import CompareArrowsIcon from '@mui/icons-material/CompareArrows';
import Navbar from '../components/Navbar';

interface ScenarioData {
  id: number;
  name: string;
  rate: number;
  points: number;
  credit: number;
  loanAmount: number;
  propertyValue: number;
  downPayment: number;
  monthlyPI: number;
  pitia: number;
  dti: number;
  ltv: number;
  cashToClose: number;
  closingCosts: {
    sectionA: {
      loanAmount: number;
      interestRate: number;
      monthlyPI: number;
      loanTerm: number;
    };
    sectionB: {
      principalAndInterest: number;
      mortgageInsurance: number;
      estimatedEscrow: number;
      estimatedTotal: number;
    };
    sectionC: {
      downPayment: number;
      closingCosts: number;
      cashToClose: number;
    };
    sectionE: {
      recordingFees: number;
      transferTaxes: number;
      recordationTaxes: number;
      total: number;
    };
    sectionH: {
      titleServices: number;
      titleInsurance: number;
      surveyFee: number;
      total: number;
    };
  };
}

const ScenarioDesk: React.FC = () => {
  const [scenarios] = useState<ScenarioData[]>([
    {
      id: 1,
      name: 'Best Rate',
      rate: 6.5,
      points: 1.0,
      credit: 0,
      loanAmount: 400000,
      propertyValue: 500000,
      downPayment: 100000,
      monthlyPI: 2528,
      pitia: 3450,
      dti: 28.5,
      ltv: 80,
      cashToClose: 112500,
      closingCosts: {
        sectionA: {
          loanAmount: 400000,
          interestRate: 6.5,
          monthlyPI: 2528,
          loanTerm: 360,
        },
        sectionB: {
          principalAndInterest: 2528,
          mortgageInsurance: 0,
          estimatedEscrow: 922,
          estimatedTotal: 3450,
        },
        sectionC: {
          downPayment: 100000,
          closingCosts: 12500,
          cashToClose: 112500,
        },
        sectionE: {
          recordingFees: 255,
          transferTaxes: 7500,
          recordationTaxes: 3580,
          total: 11335,
        },
        sectionH: {
          titleServices: 750,
          titleInsurance: 2450,
          surveyFee: 500,
          total: 3700,
        },
      },
    },
    {
      id: 2,
      name: 'Zero Cost',
      rate: 6.875,
      points: 0,
      credit: 4000,
      loanAmount: 400000,
      propertyValue: 500000,
      downPayment: 100000,
      monthlyPI: 2632,
      pitia: 3554,
      dti: 29.3,
      ltv: 80,
      cashToClose: 108500,
      closingCosts: {
        sectionA: {
          loanAmount: 400000,
          interestRate: 6.875,
          monthlyPI: 2632,
          loanTerm: 360,
        },
        sectionB: {
          principalAndInterest: 2632,
          mortgageInsurance: 0,
          estimatedEscrow: 922,
          estimatedTotal: 3554,
        },
        sectionC: {
          downPayment: 100000,
          closingCosts: 8500,
          cashToClose: 108500,
        },
        sectionE: {
          recordingFees: 255,
          transferTaxes: 7500,
          recordationTaxes: 3580,
          total: 11335,
        },
        sectionH: {
          titleServices: 750,
          titleInsurance: 2450,
          surveyFee: 500,
          total: 3700,
        },
      },
    },
    {
      id: 3,
      name: 'Max Credit',
      rate: 7.125,
      points: 0,
      credit: 8000,
      loanAmount: 400000,
      propertyValue: 500000,
      downPayment: 100000,
      monthlyPI: 2695,
      pitia: 3617,
      dti: 29.8,
      ltv: 80,
      cashToClose: 104500,
      closingCosts: {
        sectionA: {
          loanAmount: 400000,
          interestRate: 7.125,
          monthlyPI: 2695,
          loanTerm: 360,
        },
        sectionB: {
          principalAndInterest: 2695,
          mortgageInsurance: 0,
          estimatedEscrow: 922,
          estimatedTotal: 3617,
        },
        sectionC: {
          downPayment: 100000,
          closingCosts: 4500,
          cashToClose: 104500,
        },
        sectionE: {
          recordingFees: 255,
          transferTaxes: 7500,
          recordationTaxes: 3580,
          total: 11335,
        },
        sectionH: {
          titleServices: 750,
          titleInsurance: 2450,
          surveyFee: 500,
          total: 3700,
        },
      },
    },
  ]);

  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercent = (value: number, decimals: number = 2): string => {
    return `${value.toFixed(decimals)}%`;
  };

  const handleExportPDF = async () => {
    try {
      // Generate PDF with watermark
      const html2pdf = (await import('html2pdf.js')).default;
      const element = document.getElementById('scenario-comparison');

      if (!element) return;

      const opt = {
        margin: 0.5,
        filename: `scenario-comparison-${new Date().toISOString().split('T')[0]}.pdf`,
        image: { type: 'jpeg' as const, quality: 0.98 },
        html2canvas: { scale: 2 },
        jsPDF: { unit: 'in', format: 'letter', orientation: 'landscape' as const },
      };

      // Add watermark
      const watermark = document.createElement('div');
      watermark.style.position = 'fixed';
      watermark.style.top = '50%';
      watermark.style.left = '50%';
      watermark.style.transform = 'translate(-50%, -50%) rotate(-45deg)';
      watermark.style.fontSize = '120px';
      watermark.style.opacity = '0.1';
      watermark.style.color = '#667eea';
      watermark.style.fontWeight = 'bold';
      watermark.style.pointerEvents = 'none';
      watermark.style.zIndex = '9999';
      watermark.textContent = 'DRAFT';
      document.body.appendChild(watermark);

      await html2pdf().set(opt).from(element).save();

      document.body.removeChild(watermark);
    } catch (error) {
      console.error('Error generating PDF:', error);
    }
  };

  return (
    <>
      <Navbar />
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box>
              <Typography variant="h4" gutterBottom sx={{ fontWeight: 600 }}>
                Scenario Desk
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Compare pricing scenarios with detailed cost breakdowns
              </Typography>
            </Box>
            <Button
              variant="contained"
              startIcon={<PictureAsPdfIcon />}
              onClick={handleExportPDF}
              sx={{ minWidth: 160 }}
            >
              Export PDF
            </Button>
          </Box>
        </Box>

        <Box id="scenario-comparison">
          {/* Scenario Cards */}
          <Grid container spacing={3} sx={{ mb: 4 }}>
            {scenarios.map((scenario) => (
              <Grid item xs={12} md={4} key={scenario.id}>
                <Card
                  sx={{
                    height: '100%',
                    border: '2px solid',
                    borderColor: 'primary.main',
                    borderRadius: 2,
                    transition: 'all 0.3s',
                    '&:hover': {
                      boxShadow: 6,
                      transform: 'translateY(-4px)',
                    },
                  }}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                      <Typography variant="h5" sx={{ fontWeight: 600 }}>
                        {scenario.name}
                      </Typography>
                      <Chip
                        icon={<CompareArrowsIcon />}
                        label="Scenario"
                        color="primary"
                        size="small"
                      />
                    </Box>

                    <Divider sx={{ my: 2 }} />

                    {/* Key Metrics */}
                    <Stack spacing={2}>
                      <Box>
                        <Typography variant="h3" sx={{ fontWeight: 700, color: 'primary.main' }}>
                          {formatPercent(scenario.rate, 3)}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Interest Rate
                        </Typography>
                      </Box>

                      <Grid container spacing={2}>
                        <Grid item xs={6}>
                          <Typography variant="h6" sx={{ fontWeight: 600 }}>
                            {formatCurrency(scenario.pitia)}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            PITIA Payment
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="h6" sx={{ fontWeight: 600 }}>
                            {formatPercent(scenario.dti, 1)}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Back-End DTI
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="h6" sx={{ fontWeight: 600 }}>
                            {formatPercent(scenario.ltv, 0)}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            LTV Ratio
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="h6" sx={{ fontWeight: 600 }}>
                            {formatCurrency(scenario.cashToClose)}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Cash to Close
                          </Typography>
                        </Grid>
                      </Grid>

                      <Divider />

                      {/* Points and Credit */}
                      <Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2" color="text.secondary">
                            Origination Points
                          </Typography>
                          <Typography variant="body2" sx={{ fontWeight: 600 }}>
                            {formatPercent(scenario.points, 2)}
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="body2" color="text.secondary">
                            Lender Credit
                          </Typography>
                          <Typography
                            variant="body2"
                            sx={{ fontWeight: 600, color: scenario.credit > 0 ? 'success.main' : 'inherit' }}
                          >
                            {scenario.credit > 0 ? '-' : ''}{formatCurrency(scenario.credit)}
                          </Typography>
                        </Box>
                      </Box>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>

          {/* Expandable Cost Breakdown */}
          <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>
            Detailed Cost Breakdown
          </Typography>

          {scenarios.map((scenario) => (
            <Box key={scenario.id} sx={{ mb: 2 }}>
              <Typography variant="h6" sx={{ mb: 2, color: 'primary.main', fontWeight: 600 }}>
                {scenario.name}
              </Typography>

              {/* Section A: Loan Terms */}
              <Accordion>
                <AccordionSummary
                  expandIcon={<ExpandMoreIcon />}
                  aria-controls={`section-a-${scenario.id}-content`}
                  id={`section-a-${scenario.id}-header`}
                >
                  <Typography sx={{ fontWeight: 600 }}>Section A: Loan Terms</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableBody>
                        <TableRow>
                          <TableCell>Loan Amount</TableCell>
                          <TableCell align="right" sx={{ fontWeight: 600 }}>
                            {formatCurrency(scenario.closingCosts.sectionA.loanAmount)}
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Interest Rate</TableCell>
                          <TableCell align="right" sx={{ fontWeight: 600 }}>
                            {formatPercent(scenario.closingCosts.sectionA.interestRate, 3)}
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Loan Term</TableCell>
                          <TableCell align="right" sx={{ fontWeight: 600 }}>
                            {scenario.closingCosts.sectionA.loanTerm / 12} years
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell sx={{ fontWeight: 600 }}>Principal & Interest</TableCell>
                          <TableCell align="right" sx={{ fontWeight: 700, color: 'primary.main' }}>
                            {formatCurrency(scenario.closingCosts.sectionA.monthlyPI)}
                          </TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>
                </AccordionDetails>
              </Accordion>

              {/* Section B: Projected Payments */}
              <Accordion>
                <AccordionSummary
                  expandIcon={<ExpandMoreIcon />}
                  aria-controls={`section-b-${scenario.id}-content`}
                  id={`section-b-${scenario.id}-header`}
                >
                  <Typography sx={{ fontWeight: 600 }}>Section B: Projected Payments</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableBody>
                        <TableRow>
                          <TableCell>Principal & Interest</TableCell>
                          <TableCell align="right" sx={{ fontWeight: 600 }}>
                            {formatCurrency(scenario.closingCosts.sectionB.principalAndInterest)}
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Mortgage Insurance</TableCell>
                          <TableCell align="right" sx={{ fontWeight: 600 }}>
                            {formatCurrency(scenario.closingCosts.sectionB.mortgageInsurance)}
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Estimated Escrow</TableCell>
                          <TableCell align="right" sx={{ fontWeight: 600 }}>
                            {formatCurrency(scenario.closingCosts.sectionB.estimatedEscrow)}
                          </TableCell>
                        </TableRow>
                        <TableRow sx={{ bgcolor: 'action.hover' }}>
                          <TableCell sx={{ fontWeight: 700 }}>Estimated Total Monthly Payment</TableCell>
                          <TableCell align="right" sx={{ fontWeight: 700, color: 'primary.main' }}>
                            {formatCurrency(scenario.closingCosts.sectionB.estimatedTotal)}
                          </TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>
                </AccordionDetails>
              </Accordion>

              {/* Section C: Costs at Closing */}
              <Accordion>
                <AccordionSummary
                  expandIcon={<ExpandMoreIcon />}
                  aria-controls={`section-c-${scenario.id}-content`}
                  id={`section-c-${scenario.id}-header`}
                >
                  <Typography sx={{ fontWeight: 600 }}>Section C: Costs at Closing</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableBody>
                        <TableRow>
                          <TableCell>Down Payment</TableCell>
                          <TableCell align="right" sx={{ fontWeight: 600 }}>
                            {formatCurrency(scenario.closingCosts.sectionC.downPayment)}
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Closing Costs</TableCell>
                          <TableCell align="right" sx={{ fontWeight: 600 }}>
                            {formatCurrency(scenario.closingCosts.sectionC.closingCosts)}
                          </TableCell>
                        </TableRow>
                        <TableRow sx={{ bgcolor: 'action.hover' }}>
                          <TableCell sx={{ fontWeight: 700 }}>Cash to Close</TableCell>
                          <TableCell align="right" sx={{ fontWeight: 700, color: 'primary.main' }}>
                            {formatCurrency(scenario.closingCosts.sectionC.cashToClose)}
                          </TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>
                </AccordionDetails>
              </Accordion>

              {/* Section E: Taxes and Government Fees */}
              <Accordion>
                <AccordionSummary
                  expandIcon={<ExpandMoreIcon />}
                  aria-controls={`section-e-${scenario.id}-content`}
                  id={`section-e-${scenario.id}-header`}
                >
                  <Typography sx={{ fontWeight: 600 }}>Section E: Taxes and Government Fees</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableBody>
                        <TableRow>
                          <TableCell>Recording Fees</TableCell>
                          <TableCell align="right" sx={{ fontWeight: 600 }}>
                            {formatCurrency(scenario.closingCosts.sectionE.recordingFees)}
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Transfer Taxes</TableCell>
                          <TableCell align="right" sx={{ fontWeight: 600 }}>
                            {formatCurrency(scenario.closingCosts.sectionE.transferTaxes)}
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Recordation Taxes</TableCell>
                          <TableCell align="right" sx={{ fontWeight: 600 }}>
                            {formatCurrency(scenario.closingCosts.sectionE.recordationTaxes)}
                          </TableCell>
                        </TableRow>
                        <TableRow sx={{ bgcolor: 'action.hover' }}>
                          <TableCell sx={{ fontWeight: 700 }}>Total Taxes and Fees</TableCell>
                          <TableCell align="right" sx={{ fontWeight: 700, color: 'primary.main' }}>
                            {formatCurrency(scenario.closingCosts.sectionE.total)}
                          </TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>
                </AccordionDetails>
              </Accordion>

              {/* Section H: Other Costs */}
              <Accordion>
                <AccordionSummary
                  expandIcon={<ExpandMoreIcon />}
                  aria-controls={`section-h-${scenario.id}-content`}
                  id={`section-h-${scenario.id}-header`}
                >
                  <Typography sx={{ fontWeight: 600 }}>Section H: Other Costs</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableBody>
                        <TableRow>
                          <TableCell>Title Services</TableCell>
                          <TableCell align="right" sx={{ fontWeight: 600 }}>
                            {formatCurrency(scenario.closingCosts.sectionH.titleServices)}
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Title Insurance</TableCell>
                          <TableCell align="right" sx={{ fontWeight: 600 }}>
                            {formatCurrency(scenario.closingCosts.sectionH.titleInsurance)}
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Survey Fee</TableCell>
                          <TableCell align="right" sx={{ fontWeight: 600 }}>
                            {formatCurrency(scenario.closingCosts.sectionH.surveyFee)}
                          </TableCell>
                        </TableRow>
                        <TableRow sx={{ bgcolor: 'action.hover' }}>
                          <TableCell sx={{ fontWeight: 700 }}>Total Other Costs</TableCell>
                          <TableCell align="right" sx={{ fontWeight: 700, color: 'primary.main' }}>
                            {formatCurrency(scenario.closingCosts.sectionH.total)}
                          </TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>
                </AccordionDetails>
              </Accordion>

              <Divider sx={{ my: 3 }} />
            </Box>
          ))}
        </Box>
      </Container>
    </>
  );
};

export default ScenarioDesk;
