import { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  Container,
  Box,
  Typography,
  Button,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  LinearProgress,
  Alert,
  Card,
  CardContent,
  Grid,
  Chip,
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import DescriptionIcon from '@mui/icons-material/Description';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import { ocrApi } from '../services/api';

interface UploadedDocument {
  id: string;
  file: File;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  progress: number;
  extractedData?: any;
  confidence?: number;
  error?: string;
}

const DocumentUpload = () => {
  const [documents, setDocuments] = useState<UploadedDocument[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<UploadedDocument | null>(null);

  const processDocument = async (file: File) => {
    const docId = `${Date.now()}-${file.name}`;
    const newDoc: UploadedDocument = {
      id: docId,
      file,
      status: 'uploading',
      progress: 0,
    };

    setDocuments((prev) => [...prev, newDoc]);

    try {
      // Simulate upload progress
      for (let i = 0; i <= 100; i += 20) {
        await new Promise((resolve) => setTimeout(resolve, 200));
        setDocuments((prev) =>
          prev.map((doc) => (doc.id === docId ? { ...doc, progress: i } : doc))
        );
      }

      // Update status to processing
      setDocuments((prev) =>
        prev.map((doc) => (doc.id === docId ? { ...doc, status: 'processing' as const } : doc))
      );

      // Call OCR API
      const result = await ocrApi.extractDocument(file);

      // Update with results
      setDocuments((prev) =>
        prev.map((doc) =>
          doc.id === docId
            ? {
                ...doc,
                status: 'completed' as const,
                progress: 100,
                extractedData: result.extracted_data,
                confidence: result.confidence_score,
              }
            : doc
        )
      );
    } catch (error) {
      setDocuments((prev) =>
        prev.map((doc) =>
          doc.id === docId
            ? {
                ...doc,
                status: 'error' as const,
                error: (error as Error).message,
              }
            : doc
        )
      );
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'image/*': ['.png', '.jpg', '.jpeg'],
      'application/pdf': ['.pdf'],
    },
    maxSize: 10485760, // 10MB
    onDrop: (acceptedFiles) => {
      acceptedFiles.forEach((file) => processDocument(file));
    },
  });

  const handleRemove = (id: string) => {
    setDocuments((prev) => prev.filter((doc) => doc.id !== id));
    if (selectedDoc?.id === id) {
      setSelectedDoc(null);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon color="success" />;
      case 'error':
        return <ErrorIcon color="error" />;
      default:
        return <DescriptionIcon color="primary" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'error':
        return 'error';
      case 'processing':
        return 'info';
      default:
        return 'default';
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        width: '100%',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        py: { xs: 2, sm: 3, md: 4 },
        px: { xs: 1, sm: 2, md: 3 },
      }}
    >
      <Container maxWidth="xl" disableGutters sx={{ width: '100%', px: { xs: 1, sm: 2, md: 3 } }}>
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
            📄 Document Upload & OCR
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
            Upload income documents for AI-powered data extraction
          </Typography>
        </Box>

        <Grid container spacing={{ xs: 2, sm: 3 }}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
              <Typography variant="h5" gutterBottom sx={{ fontSize: { xs: '1.25rem', sm: '1.5rem' } }}>
                Upload Documents
              </Typography>

              <Box
                {...getRootProps()}
                sx={{
                  border: '3px dashed',
                  borderColor: isDragActive ? 'primary.main' : '#667eea',
                  borderRadius: 2,
                  p: { xs: 3, sm: 4, md: 6 },
                  textAlign: 'center',
                  cursor: 'pointer',
                  bgcolor: isDragActive ? 'action.hover' : 'transparent',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    bgcolor: 'action.hover',
                    borderColor: 'primary.dark',
                  },
                  mb: 3,
                }}
              >
                <input {...getInputProps()} />
                <CloudUploadIcon sx={{ fontSize: { xs: 48, sm: 60 }, color: '#667eea', mb: 2 }} />
                <Typography variant="h6" gutterBottom sx={{ fontSize: { xs: '1rem', sm: '1.125rem', md: '1.25rem' } }}>
                  {isDragActive ? 'Drop files here...' : 'Drag & drop documents here'}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}>
                  or click to select files
                </Typography>
                <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 2 }}>
                  Supported: PDF, JPG, PNG (Max 10MB)
                </Typography>
              </Box>

              <Alert severity="info" sx={{ mb: 3 }}>
                <strong>Supported Documents:</strong>
                <ul style={{ marginTop: 8, marginLeft: 20, marginBottom: 0 }}>
                  <li>Pay Stubs</li>
                  <li>W-2 Forms</li>
                  <li>Tax Returns (1040)</li>
                  <li>Bank Statements</li>
                  <li>Employment Letters</li>
                </ul>
              </Alert>

              <Typography variant="h6" gutterBottom>
                Uploaded Documents ({documents.length})
              </Typography>

              {documents.length === 0 ? (
                <Alert severity="info">No documents uploaded yet. Upload documents to get started.</Alert>
              ) : (
                <List>
                  {documents.map((doc) => (
                    <ListItem
                      key={doc.id}
                      button
                      selected={selectedDoc?.id === doc.id}
                      onClick={() => setSelectedDoc(doc)}
                      sx={{
                        border: 1,
                        borderColor: 'divider',
                        borderRadius: 1,
                        mb: 1,
                        '&:hover': {
                          bgcolor: 'action.hover',
                        },
                      }}
                    >
                      <Box sx={{ mr: 2 }}>{getStatusIcon(doc.status)}</Box>
                      <ListItemText
                        primary={doc.file.name}
                        secondary={
                          <Box>
                            <Chip
                              label={doc.status}
                              color={getStatusColor(doc.status)}
                              size="small"
                              sx={{ mt: 0.5 }}
                            />
                            {doc.status === 'uploading' || doc.status === 'processing' ? (
                              <LinearProgress
                                variant={doc.status === 'uploading' ? 'determinate' : 'indeterminate'}
                                value={doc.progress}
                                sx={{ mt: 1 }}
                              />
                            ) : null}
                            {doc.confidence !== undefined && (
                              <Typography variant="caption" display="block" sx={{ mt: 0.5 }}>
                                Confidence: {doc.confidence.toFixed(0)}%
                              </Typography>
                            )}
                          </Box>
                        }
                      />
                      <ListItemSecondaryAction>
                        <IconButton edge="end" onClick={() => handleRemove(doc.id)} color="error">
                          <DeleteIcon />
                        </IconButton>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              )}
            </Paper>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper sx={{ p: { xs: 2, sm: 3, md: 4 }, height: '100%' }}>
              <Typography variant="h5" gutterBottom sx={{ fontSize: { xs: '1.25rem', sm: '1.5rem' } }}>
                Extracted Data
              </Typography>

              {!selectedDoc ? (
                <Alert severity="info">Select a document from the left to view extracted data</Alert>
              ) : selectedDoc.status === 'uploading' || selectedDoc.status === 'processing' ? (
                <Box textAlign="center" py={8}>
                  <LinearProgress sx={{ mb: 2 }} />
                  <Typography color="text.secondary">
                    {selectedDoc.status === 'uploading' ? 'Uploading...' : 'Processing document with AI OCR...'}
                  </Typography>
                </Box>
              ) : selectedDoc.status === 'error' ? (
                <Alert severity="error">
                  <Typography variant="body1">
                    <strong>Extraction Failed</strong>
                  </Typography>
                  <Typography variant="body2">{selectedDoc.error}</Typography>
                </Alert>
              ) : (
                <Box>
                  <Alert severity="success" sx={{ mb: 3 }}>
                    <Typography variant="body1">
                      <strong>✓ Extraction Complete</strong>
                    </Typography>
                    <Typography variant="body2">Confidence Score: {selectedDoc.confidence?.toFixed(0)}%</Typography>
                  </Alert>

                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" gutterBottom color="primary">
                        Document Information
                      </Typography>
                      <Grid container spacing={2}>
                        <Grid item xs={6}>
                          <Typography variant="body2" color="text.secondary">
                            File Name:
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2">{selectedDoc.file.name}</Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2" color="text.secondary">
                            File Size:
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2">
                            {(selectedDoc.file.size / 1024 / 1024).toFixed(2)} MB
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2" color="text.secondary">
                            File Type:
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2">{selectedDoc.file.type}</Typography>
                        </Grid>
                      </Grid>
                    </CardContent>
                  </Card>

                  {selectedDoc.extractedData && (
                    <Card variant="outlined" sx={{ mt: 2 }}>
                      <CardContent>
                        <Typography variant="h6" gutterBottom color="primary">
                          Extracted Fields
                        </Typography>
                        <Paper variant="outlined" sx={{ p: 2, bgcolor: '#f5f5f5' }}>
                          <pre style={{ margin: 0, fontSize: '0.875rem', overflow: 'auto' }}>
                            {JSON.stringify(selectedDoc.extractedData, null, 2)}
                          </pre>
                        </Paper>
                      </CardContent>
                    </Card>
                  )}
                </Box>
              )}
            </Paper>
          </Grid>
        </Grid>

        <Box textAlign="center" mt={{ xs: 3, sm: 4 }}>
          <Button
            variant="contained"
            size="large"
            href="/"
            sx={{
              bgcolor: 'white',
              color: '#667eea',
              '&:hover': { bgcolor: 'rgba(255,255,255,0.9)' },
              width: { xs: '100%', sm: 'auto' },
              maxWidth: { xs: '100%', sm: 240 },
              py: { xs: 1.5, sm: 1 },
            }}
          >
            Back to Home
          </Button>
        </Box>
      </Container>
    </Box>
  );
};

export default DocumentUpload;
