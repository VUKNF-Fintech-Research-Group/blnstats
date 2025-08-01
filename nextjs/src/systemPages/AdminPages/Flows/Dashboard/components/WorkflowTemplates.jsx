import React from 'react';
import { Box, Typography, Grid } from '@mui/material';
import WorkflowTemplateCard from './WorkflowTemplateCard';

export default function WorkflowTemplates({ workflowTemplates, triggerWorkflow }) {
  return (
    <Box>
      <Typography variant="h6" className="mb-4">Workflow Templates</Typography>
      <Grid container spacing={3}>
        {workflowTemplates.map((template) => (
          <Grid item xs={12} md={6} lg={4} key={template.id}>
            <WorkflowTemplateCard 
              template={template} 
              triggerWorkflow={triggerWorkflow}
            />
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}