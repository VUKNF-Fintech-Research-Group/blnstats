import React from 'react';
import { Box } from '@mui/material';
import WorkflowRunCard from './WorkflowRunCard';

export default function ActiveWorkflows({ workflowRuns }) {
  return (
    <Box className="space-y-4">
      {workflowRuns.length === 0 ? (
        <Box className="text-center py-8 text-gray-500">
          No active workflows
        </Box>
      ) : (
        workflowRuns.map((run) => (
          <WorkflowRunCard
            key={run.id}
            run={run}
          />
        ))
      )}
    </Box>
  );
}