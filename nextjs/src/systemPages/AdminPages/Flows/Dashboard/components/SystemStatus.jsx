import React from 'react';
import { 
  Box, 
  Typography, 
  Card, 
  CardContent, 
  LinearProgress, 
  Grid,
  List,
  ListItem,
  ListItemText
} from '@mui/material';

export default function SystemStatus({ systemStatus }) {
  return (
    <Box>
      <Typography variant="h6" className="mb-4">System Status</Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" className="mb-3">
                🌩️ Prefect Infrastructure
              </Typography>
              <List>
                <ListItem>
                  <ListItemText
                    primary="🟢 Prefect Server"
                    secondary="Connected and healthy"
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="🟢 Worker Pool"
                    secondary={`${systemStatus.workerPool.active}/${systemStatus.workerPool.total} workers active`}
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" className="mb-3">
                🗄️ Database Status
              </Typography>
              <List>
                <ListItem>
                  <ListItemText
                    primary="📦 Blocks"
                    secondary={systemStatus.database.blocks}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="💳 Transactions"
                    secondary={systemStatus.database.transactions}
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" className="mb-3">
                💾 Storage Usage
              </Typography>
              <Box className="flex justify-between items-center mb-1">
                <Typography variant="body2">
                  {systemStatus.storage.used} / {systemStatus.storage.total}
                </Typography>
                <Typography variant="body2">
                  {systemStatus.storage.percentage}%
                </Typography>
              </Box>
              <LinearProgress 
                variant="determinate" 
                value={systemStatus.storage.percentage}
                color={systemStatus.storage.percentage > 80 ? "secondary" : "primary"}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
