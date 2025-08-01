import React from 'react';
import { 
  Box, 
  Typography, 
  Button, 
  Card, 
  CardContent, 
  LinearProgress, 
  Chip, 
  List,
  ListItem,
  ListItemText
} from '@mui/material';

export default function WorkflowRunCard({ run, stopWorkflow, getStatusColor, getStatusEmoji }) {
  return (
    <Box className="w-full border-2 border-gray-200 rounded-md">
      <Card>
        <CardContent>
          <Box className="flex justify-between items-start mb-3">
            <Box>
              <Typography variant="h6" className="flex items-center gap-2">
                {getStatusEmoji(run.status)}
                {run.name}
                <Chip 
                  label={run.status} 
                  color={getStatusColor(run.status)}
                  size="small"
                />
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Started: {run.startTime} {run.estimatedEnd && `• ETA: ${run.estimatedEnd}`}
              </Typography>
            </Box>
            <Box className="flex gap-1">
              <Button size="small" variant="outlined">
                👁️ View
              </Button>
              {run.status === 'running' && (
                <Button 
                  size="small" 
                  color="warning"
                  variant="outlined"
                  onClick={() => stopWorkflow(run.id)}
                >
                  ⏹️ Stop
                </Button>
              )}
              <Button size="small" variant="outlined">
                🔄 Restart
              </Button>
            </Box>
          </Box>

          {run.status === 'running' && (
            <Box className="mb-3">
              <Box className="flex justify-between items-center mb-1">
                <Typography variant="body2">Overall Progress</Typography>
                <Typography variant="body2">{Math.round(run.progress)}%</Typography>
              </Box>
              <LinearProgress variant="determinate" value={run.progress} />
            </Box>
          )}

          {run.tasks && run.tasks.length > 0 && (
            <Box>
              <Typography variant="subtitle2" className="mb-2">Tasks:</Typography>
              <List dense>
                {run.tasks.map((task, index) => (
                  <ListItem key={index} className="pl-0">
                    <ListItemText
                      primary={
                        <Box className="flex items-center gap-2">
                          <span>{getStatusEmoji(task.status)}</span>
                          <span>{task.name}</span>
                          {task.duration && (
                            <Chip label={task.duration} size="small" variant="outlined" />
                          )}
                          {task.detail && (
                            <Typography variant="caption" color="textSecondary">
                              {task.detail}
                            </Typography>
                          )}
                        </Box>
                      }
                    />
                    {task.status === 'running' && task.progress && (
                      <Box className="w-24 ml-2">
                        <LinearProgress variant="determinate" value={task.progress} />
                      </Box>
                    )}
                  </ListItem>
                ))}
              </List>
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}

