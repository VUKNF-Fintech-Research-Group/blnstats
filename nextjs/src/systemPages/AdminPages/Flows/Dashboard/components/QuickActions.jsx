import React from 'react';
import { 
  Box, 
  Typography, 
  Button, 
  Card, 
  CardContent, 
  Grid 
} from '@mui/material';

import PlayCircleFilledIcon from '@mui/icons-material/PlayCircleFilled';
import SyncIcon from '@mui/icons-material/Sync';
import AssessmentIcon from '@mui/icons-material/Assessment';

export default function QuickActions({ triggerWorkflow }) {
  return (
    <Card className="mb-6">
      <CardContent>
        <Typography variant="h6" className="mb-3">
          Quick Actions
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={4}>
            <Button
              variant="contained"
              color="primary"
              fullWidth
              onClick={() => triggerWorkflow('ln-analytics')}
              className="h-12"
            >
              <PlayCircleFilledIcon className="mr-2" /> Run Full Pipeline
            </Button>
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <Button
              variant="outlined"
              color="primary"
              fullWidth
              onClick={() => triggerWorkflow('blockchain-sync')}
              className="h-12"
            >
              <SyncIcon className="mr-2" /> Sync Blockchain
            </Button>
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <Button
              variant="outlined"
              color="primary"
              fullWidth
              onClick={() => triggerWorkflow('generate-stats')}
              className="h-12"
            >
              <AssessmentIcon className="mr-2" /> Generate Stats
            </Button>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
} 