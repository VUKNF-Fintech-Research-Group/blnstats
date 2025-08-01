import React from 'react';
import { Box, Grid } from '@mui/material';
import WorkflowRunCard from './WorkflowRunCard';

export default function ActiveWorkflows({ workflowRuns, stopWorkflow, getStatusColor, getStatusEmoji }) {
  return (
    <Box>
      {workflowRuns.length === 0 ? (
        <Box className="text-center py-8 text-gray-500">
          No active workflows
        </Box>
      ) : (
        <Grid container spacing={3}>
          {workflowRuns.map((run) => (
            <Box key={run.id} className="w-full border-2 border-gray-200 rounded-md">
              <WorkflowRunCard
                run={run}
                stopWorkflow={stopWorkflow}
                getStatusColor={getStatusColor}
                getStatusEmoji={getStatusEmoji}
              />
            </Box>
          ))}
        </Grid>
      )}
    </Box>
  );
}