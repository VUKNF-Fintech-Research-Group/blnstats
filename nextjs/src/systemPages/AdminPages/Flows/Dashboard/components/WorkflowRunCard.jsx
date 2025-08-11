import React, { useState } from 'react';
import { 
  Box, 
  Typography, 
  Button, 
  Card, 
  CardContent, 
  Chip, 
  List,
  ListItem,
  ListItemText,
  Divider,
  Collapse,
  IconButton
} from '@mui/material';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';

// --- Static Helper Functions ---

const getStatusColor = (status) => {
  switch (status) {
    case 'completed': return 'success';
    case 'running': return 'primary';
    case 'pending': return 'default';
    case 'failed': return 'error';
    case 'stopped': return 'warning';
    default: return 'default';
  }
};

const getStatusEmoji = (status) => {
  switch (status) {
    case 'completed': return '✅';
    case 'running': return '🔄';
    case 'pending': return '⏳';
    case 'failed': return '❌';
    case 'stopped': return '⏹️';
    default: return '⏳';
  }
};

// --- Child Components ---

const TaskItem = ({ item }) => (
  <Box className="flex items-center gap-2">
    <span>{getStatusEmoji(item.status)}</span>
    <span>{item.name}</span>
    {item.duration && (
      <Chip label={item.duration} size="small" variant="outlined" />
    )}
  </Box>
);

const SubflowItem = ({ item }) => {
  const [open, setOpen] = useState(true);
  return (
    <Box className="w-full">
      <Box className="flex items-center">
        <Box className="flex items-center gap-2 flex-grow">
          <span>{getStatusEmoji(item.status)}</span>
          <span className="font-semibold">{item.name}</span>
          {item.duration && (
            <Chip label={item.duration} size="small" variant="outlined" color={getStatusColor(item.status)} />
          )}
        </Box>
        <IconButton aria-label="expand row" size="small" onClick={() => setOpen(!open)}>
          {open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
        </IconButton>
      </Box>
      <Collapse in={open} timeout="auto" unmountOnExit>
        <Box className="pl-6 border-l-2 border-gray-300">
          <List dense>
            {item.tasks.map((task) => (
              <ListItem key={task.id} className="pl-2">
                <ListItemText primary={<TaskItem item={task} />} />
              </ListItem>
            ))}
          </List>
        </Box>
      </Collapse>
    </Box>
  );
};

// --- Main Card Component ---

export default function WorkflowRunCard({ run }) {
  return (
    <Box className="w-full border-2 border-gray-200 rounded-md">
      <Card>
        <CardContent>
          <Box className="flex justify-between items-start mb-3">
            <Box>
              <Typography variant="h6" className="flex items-center gap-4">
                <div>{getStatusEmoji(run.status)}</div>
                <div>{run.name}</div>
                <Chip label={run.status} color={getStatusColor(run.status)} size="small" />
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Started: {run.startTime}
              </Typography>
            </Box>
            <Box className="flex gap-1">
              <Button 
                component="a"
                href={`/prefect/flow-runs/flow-run/${run.id}`}
                target="_blank"
                rel="noopener noreferrer"
                size="small"
                variant="outlined"
              >
                View in Prefect
              </Button>
            </Box>
          </Box>
          
          <Divider className="my-3" />

          {run.tasks && run.tasks.length > 0 && (
            <Box>
              <Typography variant="subtitle2" className="mb-2">Tasks:</Typography>
              <List dense>
                {run.tasks.map((item) => (
                  <ListItem key={item.id} className="pl-0">
                    {item.type === 'subflow'
                      ? <SubflowItem item={item} />
                      : <TaskItem item={item} />
                    }
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

