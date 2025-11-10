import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Container,
  Box,
  Typography,
  Button,
  Paper,
  Card,
  CardContent,
  Grid,
  Chip,
  Alert,
  AlertTitle,
  LinearProgress,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  Tooltip,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import DescriptionIcon from '@mui/icons-material/Description';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import RefreshIcon from '@mui/icons-material/Refresh';
import VisibilityIcon from '@mui/icons-material/Visibility';
import DeleteIcon from '@mui/icons-material/Delete';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import WarningIcon from '@mui/icons-material/Warning';
import { useDropzone } from 'react-dropzone';
import Navbar from '../components/Navbar';
import { creditApi, ocrApi } from '../services/api';
import type { DocTask } from '../types/credit';

interface UploadedFile {
  id: string;
  file: File;
  taskId: number;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  progress: number;
  url?: string;
  error?: string;
}

interface TaskSection {
  type: string;
  title: string;
  description: string;
  tasks: DocTask[];
}

const DocumentsPortal = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const loanEstimateId = searchParams.get('loan_estimate_id');

  const [tasks, setTasks] = useState<DocTask[]>([]);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [previewFile, setPreviewFile] = useState<UploadedFile | null>(null);
  const [retryingTaskId, setRetryingTaskId] = useState<number | null>(null);

  // Fetch tasks on mount
  useEffect(() => {
    fetchTasks();
  }, [loanEstimateId]);

  const fetchTasks = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await creditApi.getDocTasks(
        loanEstimateId ? parseInt(loanEstimateId) : undefined
      );
      setTasks(data);
    } catch (err) {
      setError('Failed to load document tasks. Please try again.');
      console.error('Error fetching tasks:', err);
    } finally {
      setLoading(false);
    }
  };

  // Group tasks by type
  const groupedTasks: TaskSection[] = [
    {
      type: 'verify_income',
      title: 'Income Verification',
      description: 'Upload pay stubs, W-2s, or tax returns to verify your income',
      tasks: tasks.filter((t) => t.task_type === 'verify_income'),
    },
    {
      type: 'verify_assets',
      title: 'Asset Verification',
      description: 'Upload bank statements or investment account statements',
      tasks: tasks.filter((t) => t.task_type === 'verify_assets'),
    },
    {
      type: 'upload_document',
      title: 'General Documents',
      description: 'Upload any additional requested documents',
      tasks: tasks.filter((t) => t.task_type === 'upload_document'),
    },
    {
      type: 'dispute_tradeline',
      title: 'Credit Disputes',
      description: 'Provide supporting documentation for disputed items',
      tasks: tasks.filter((t) => t.task_type === 'dispute_tradeline'),
    },
    {
      type: 'provide_explanation',
      title: 'Explanations Required',
      description: 'Provide written explanations with supporting documents',
      tasks: tasks.filter((t) => t.task_type === 'provide_explanation'),
    },
  ].filter((section) => section.tasks.length > 0);

  // Handle file upload for a specific task
  const handleFileUpload = async (file: File, taskId: number) => {
    const uploadId = `${Date.now()}-${file.name}`;
    const newUpload: UploadedFile = {
      id: uploadId,
      file,
      taskId,
      status: 'uploading',
      progress: 0,
    };

    setUploadedFiles((prev) => [...prev, newUpload]);

    try {
      // Simulate upload progress
      for (let i = 0; i <= 100; i += 10) {
        await new Promise((resolve) => setTimeout(resolve, 100));
        setUploadedFiles((prev) =>
          prev.map((f) => (f.id === uploadId ? { ...f, progress: i } : f))
        );
      }

      // Update status to processing
      setUploadedFiles((prev) =>
        prev.map((f) => (f.id === uploadId ? { ...f, status: 'processing' as const } : f))
      );

      // Call OCR API if it's a document
      if (file.type === 'application/pdf' || file.type.startsWith('image/')) {
        await ocrApi.extractDocument(file);
      }

      // Create URL for preview
      const url = URL.createObjectURL(file);

      // Update with results
      setUploadedFiles((prev) =>
        prev.map((f) =>
          f.id === uploadId
            ? {
                ...f,
                status: 'completed' as const,
                progress: 100,
                url,
              }
            : f
        )
      );

      // Update task status to in_progress
      const task = tasks.find((t) => t.id === taskId);
      if (task && task.status === 'pending') {
        await creditApi.updateDocTask(taskId, {
          status: 'in_progress',
        });
        await fetchTasks();
      }
    } catch (err) {
      setUploadedFiles((prev) =>
        prev.map((f) =>
          f.id === uploadId
            ? {
                ...f,
                status: 'error' as const,
                error: (err as Error).message || 'Upload failed',
              }
            : f
        )
      );
    }
  };

  // Retry failed upload
  const handleRetry = (uploadedFile: UploadedFile) => {
    setUploadedFiles((prev) => prev.filter((f) => f.id !== uploadedFile.id));
    handleFileUpload(uploadedFile.file, uploadedFile.taskId);
  };

  // Mark task as completed
  const handleCompleteTask = async (taskId: number) => {
    try {
      setRetryingTaskId(taskId);
      await creditApi.updateDocTask(taskId, { status: 'completed' });
      await fetchTasks();
    } catch (err) {
      setError('Failed to complete task. Please try again.');
    } finally {
      setRetryingTaskId(null);
    }
  };

  // Remove file
  const handleRemoveFile = (fileId: string) => {
    const file = uploadedFiles.find((f) => f.id === fileId);
    if (file?.url) {
      URL.revokeObjectURL(file.url);
    }
    setUploadedFiles((prev) => prev.filter((f) => f.id !== fileId));
  };

  // Get status color
  const getStatusColor = (status: string): 'default' | 'primary' | 'success' | 'error' | 'warning' => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'in_progress':
        return 'primary';
      case 'pending':
        return 'warning';
      case 'cancelled':
        return 'default';
      default:
        return 'default';
    }
  };

  // Get status icon
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon />;
      case 'error':
        return <ErrorIcon />;
      case 'pending':
        return <AccessTimeIcon />;
      default:
        return <DescriptionIcon />;
    }
  };

  // Dropzone component for a task
  const TaskDropzone = ({ task }: { task: DocTask }) => {
    const { getRootProps, getInputProps, isDragActive } = useDropzone({
      accept: {
        'image/*': ['.png', '.jpg', '.jpeg'],
        'application/pdf': ['.pdf'],
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      },
      maxSize: 10485760, // 10MB
      onDrop: (acceptedFiles) => {
        acceptedFiles.forEach((file) => handleFileUpload(file, task.id));
      },
    });

    const taskFiles = uploadedFiles.filter((f) => f.taskId === task.id);

    return (
      <Box>
        <Box
          {...getRootProps()}
          sx={{
            border: '2px dashed',
            borderColor: isDragActive ? 'primary.main' : 'divider',
            borderRadius: 2,
            p: 3,
            textAlign: 'center',
            cursor: 'pointer',
            bgcolor: isDragActive ? 'action.hover' : 'transparent',
            transition: 'all 0.2s ease',
            '&:hover': {
              bgcolor: 'action.hover',
              borderColor: 'primary.main',
            },
            mb: 2,
          }}
        >
          <input {...getInputProps()} />
          <CloudUploadIcon sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
          <Typography variant="body2" color="text.secondary">
            {isDragActive ? 'Drop files here...' : 'Drag & drop files or click to select'}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            PDF, Images, DOCX (Max 10MB)
          </Typography>
        </Box>

        {taskFiles.length > 0 && (
          <List dense>
            {taskFiles.map((file) => (
              <ListItem
                key={file.id}
                sx={{
                  border: 1,
                  borderColor: 'divider',
                  borderRadius: 1,
                  mb: 1,
                }}
              >
                <ListItemIcon>{getStatusIcon(file.status)}</ListItemIcon>
                <ListItemText
                  primary={file.file.name}
                  secondary={
                    <Box>
                      <Chip
                        label={file.status}
                        color={getStatusColor(file.status)}
                        size="small"
                        sx={{ mt: 0.5 }}
                      />
                      {(file.status === 'uploading' || file.status === 'processing') && (
                        <LinearProgress
                          variant={file.status === 'uploading' ? 'determinate' : 'indeterminate'}
                          value={file.progress}
                          sx={{ mt: 1 }}
                        />
                      )}
                      {file.error && (
                        <Typography variant="caption" color="error" display="block">
                          {file.error}
                        </Typography>
                      )}
                    </Box>
                  }
                />
                <ListItemSecondaryAction>
                  {file.status === 'error' && (
                    <IconButton
                      edge="end"
                      onClick={() => handleRetry(file)}
                      color="primary"
                      size="small"
                      sx={{ mr: 1 }}
                    >
                      <RefreshIcon />
                    </IconButton>
                  )}
                  {file.status === 'completed' && file.url && (
                    <IconButton
                      edge="end"
                      onClick={() => setPreviewFile(file)}
                      color="primary"
                      size="small"
                      sx={{ mr: 1 }}
                    >
                      <VisibilityIcon />
                    </IconButton>
                  )}
                  <IconButton edge="end" onClick={() => handleRemoveFile(file.id)} color="error" size="small">
                    <DeleteIcon />
                  </IconButton>
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>
        )}

        {task.status !== 'completed' && taskFiles.some((f) => f.status === 'completed') && (
          <Button
            variant="contained"
            color="success"
            fullWidth
            onClick={() => handleCompleteTask(task.id)}
            disabled={retryingTaskId === task.id}
            startIcon={retryingTaskId === task.id ? <RefreshIcon /> : <CheckCircleIcon />}
          >
            {retryingTaskId === task.id ? 'Submitting...' : 'Mark Task as Complete'}
          </Button>
        )}
      </Box>
    );
  };

  // Preview dialog
  const PreviewDialog = () => {
    if (!previewFile) return null;

    const isImage = previewFile.file.type.startsWith('image/');
    const isPdf = previewFile.file.type === 'application/pdf';

    return (
      <Dialog open={!!previewFile} onClose={() => setPreviewFile(null)} maxWidth="md" fullWidth>
        <DialogTitle>{previewFile.file.name}</DialogTitle>
        <DialogContent>
          {isImage && previewFile.url && (
            <Box
              component="img"
              src={previewFile.url}
              alt={previewFile.file.name}
              sx={{ width: '100%', height: 'auto', borderRadius: 1 }}
            />
          )}
          {isPdf && previewFile.url && (
            <Box
              component="iframe"
              src={previewFile.url}
              sx={{ width: '100%', height: '70vh', border: 'none', borderRadius: 1 }}
            />
          )}
          {!isImage && !isPdf && (
            <Alert severity="info">
              <AlertTitle>Preview Not Available</AlertTitle>
              Preview is only available for images and PDFs. The file has been uploaded successfully.
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPreviewFile(null)}>Close</Button>
        </DialogActions>
      </Dialog>
    );
  };

  if (loading) {
    return (
      <>
        <Navbar title="Documents Portal" />
        <Box
          sx={{
            minHeight: 'calc(100vh - 64px)',
            width: '100%',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Paper sx={{ p: 4, textAlign: 'center' }}>
            <LinearProgress sx={{ mb: 2 }} />
            <Typography>Loading document tasks...</Typography>
          </Paper>
        </Box>
      </>
    );
  }

  return (
    <>
      <Navbar title="Documents Portal" />
      <Box
        sx={{
          minHeight: 'calc(100vh - 64px)',
          width: '100%',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          py: { xs: 2, sm: 3, md: 4 },
          px: { xs: 1, sm: 2, md: 3 },
        }}
      >
        <Container maxWidth="lg">
          {/* Header */}
          <Box textAlign="center" mb={{ xs: 3, sm: 4 }}>
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
              Documents Portal
            </Typography>
            <Typography
              variant="h6"
              sx={{
                color: 'white',
                opacity: 0.9,
                fontSize: { xs: '1rem', sm: '1.125rem', md: '1.25rem' },
                px: { xs: 2, sm: 0 },
              }}
            >
              Upload required documents organized by category
            </Typography>
          </Box>

          {/* Error Banner */}
          {error && (
            <Alert
              severity="error"
              sx={{ mb: 3 }}
              action={
                <IconButton color="inherit" size="small" onClick={fetchTasks}>
                  <RefreshIcon />
                </IconButton>
              }
            >
              <AlertTitle>Error</AlertTitle>
              {error}
            </Alert>
          )}

          {/* Overall Progress */}
          <Paper sx={{ p: { xs: 2, sm: 3 }, mb: 3 }}>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} sm={8}>
                <Typography variant="h6" gutterBottom>
                  Overall Progress
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Box sx={{ flex: 1 }}>
                    <LinearProgress
                      variant="determinate"
                      value={
                        tasks.length > 0
                          ? (tasks.filter((t) => t.status === 'completed').length / tasks.length) * 100
                          : 0
                      }
                      sx={{ height: 10, borderRadius: 5 }}
                    />
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ minWidth: 60 }}>
                    {tasks.filter((t) => t.status === 'completed').length} / {tasks.length} complete
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={4}>
                <Grid container spacing={1}>
                  <Grid item xs={6}>
                    <Chip
                      icon={<AccessTimeIcon />}
                      label={`${tasks.filter((t) => t.status === 'pending').length} Pending`}
                      color="warning"
                      size="small"
                      sx={{ width: '100%' }}
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <Chip
                      icon={<CheckCircleIcon />}
                      label={`${tasks.filter((t) => t.status === 'completed').length} Done`}
                      color="success"
                      size="small"
                      sx={{ width: '100%' }}
                    />
                  </Grid>
                </Grid>
              </Grid>
            </Grid>
          </Paper>

          {/* No Tasks */}
          {groupedTasks.length === 0 && (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <AttachFileIcon sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h5" gutterBottom>
                No Document Tasks
              </Typography>
              <Typography color="text.secondary" sx={{ mb: 3 }}>
                You don't have any pending document tasks at this time.
              </Typography>
              <Button variant="contained" href="/">
                Back to Home
              </Button>
            </Paper>
          )}

          {/* Task Sections */}
          {groupedTasks.map((section) => (
            <Accordion
              key={section.type}
              defaultExpanded
              sx={{
                mb: 2,
                '&:before': { display: 'none' },
                boxShadow: 2,
              }}
            >
              <AccordionSummary
                expandIcon={<ExpandMoreIcon />}
                sx={{
                  bgcolor: 'primary.main',
                  color: 'white',
                  borderRadius: '4px 4px 0 0',
                  '&:hover': { bgcolor: 'primary.dark' },
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                  <Typography variant="h6" sx={{ flex: 1 }}>
                    {section.title}
                  </Typography>
                  <Chip
                    label={`${section.tasks.filter((t) => t.status === 'completed').length}/${section.tasks.length}`}
                    size="small"
                    sx={{ bgcolor: 'white', color: 'primary.main' }}
                  />
                </Box>
              </AccordionSummary>
              <AccordionDetails sx={{ p: { xs: 2, sm: 3 } }}>
                <Typography color="text.secondary" sx={{ mb: 3 }}>
                  {section.description}
                </Typography>

                <Grid container spacing={3}>
                  {section.tasks.map((task) => (
                    <Grid item xs={12} key={task.id}>
                      <Card
                        variant="outlined"
                        sx={{
                          borderColor: task.is_overdue ? 'error.main' : 'divider',
                          borderWidth: task.is_overdue ? 2 : 1,
                        }}
                      >
                        <CardContent>
                          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2, mb: 2 }}>
                            <Box sx={{ flex: 1 }}>
                              <Typography variant="h6" gutterBottom>
                                {task.title}
                              </Typography>
                              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                                {task.description}
                              </Typography>
                              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', alignItems: 'center' }}>
                                <Chip
                                  label={task.status_display}
                                  color={getStatusColor(task.status)}
                                  size="small"
                                />
                                {task.due_date && (
                                  <Chip
                                    icon={task.is_overdue ? <WarningIcon /> : <AccessTimeIcon />}
                                    label={`Due: ${new Date(task.due_date).toLocaleDateString()}`}
                                    color={task.is_overdue ? 'error' : 'default'}
                                    size="small"
                                    variant="outlined"
                                  />
                                )}
                                {task.tradeline_details && (
                                  <Tooltip title={`${task.tradeline_details.creditor_name} - $${task.tradeline_details.current_balance}`}>
                                    <Chip
                                      label={task.tradeline_details.account_type}
                                      size="small"
                                      variant="outlined"
                                    />
                                  </Tooltip>
                                )}
                              </Box>
                            </Box>
                          </Box>

                          {task.is_overdue && (
                            <Alert severity="warning" sx={{ mb: 2 }}>
                              <AlertTitle>Overdue</AlertTitle>
                              This task is past its due date. Please complete it as soon as possible.
                            </Alert>
                          )}

                          <Divider sx={{ my: 2 }} />

                          {task.status !== 'completed' ? (
                            <TaskDropzone task={task} />
                          ) : (
                            <Alert severity="success" icon={<CheckCircleIcon />}>
                              <AlertTitle>Task Completed</AlertTitle>
                              This task has been marked as complete.
                              {task.completed_at && (
                                <Typography variant="caption" display="block" sx={{ mt: 0.5 }}>
                                  Completed on {new Date(task.completed_at).toLocaleString()}
                                </Typography>
                              )}
                            </Alert>
                          )}
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </AccordionDetails>
            </Accordion>
          ))}

          {/* Back Button */}
          <Box textAlign="center" mt={{ xs: 3, sm: 4 }}>
            <Button
              variant="contained"
              size="large"
              onClick={() => navigate(-1)}
              sx={{
                bgcolor: 'white',
                color: 'primary.main',
                '&:hover': { bgcolor: 'rgba(255,255,255,0.9)' },
                width: { xs: '100%', sm: 'auto' },
                maxWidth: { xs: '100%', sm: 240 },
              }}
            >
              Back
            </Button>
          </Box>
        </Container>
      </Box>

      {/* Preview Dialog */}
      <PreviewDialog />
    </>
  );
};

export default DocumentsPortal;
