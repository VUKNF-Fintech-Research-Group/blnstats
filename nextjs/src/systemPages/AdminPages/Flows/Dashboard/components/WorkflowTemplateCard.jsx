import React from 'react';
import { 
  Box, 
  Typography, 
  Button, 
  Card, 
  CardContent 
} from '@mui/material';

export default function WorkflowTemplateCard({ template, triggerWorkflow }) {
  return (
    <Card className="h-full">
      <CardContent className="flex flex-col h-full">
        <Typography variant="h6" className="mb-2">
          📊 {template.name}
        </Typography>
        <Typography variant="body2" color="textSecondary" className="mb-3 flex-1">
          {template.description}
        </Typography>
        <Box className="mb-3">
          <Typography variant="caption" color="textSecondary">
            ⏱️ Duration: {template.estimatedDuration}
          </Typography>
          <br />
          <Typography variant="caption" color="textSecondary">
            🕒 Last Run: {template.lastRun}
          </Typography>
        </Box>
        <Box className="flex gap-2">
          <Button
            variant="contained"
            size="small"
            onClick={() => triggerWorkflow(template.id)}
            className="flex-1"
          >
            ▶️ Run Now
          </Button>
          <Button
            variant="outlined"
            size="small"
          >
            📅 Schedule
          </Button>
          <Button
            variant="outlined"
            size="small"
          >
            ⚙️
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
}