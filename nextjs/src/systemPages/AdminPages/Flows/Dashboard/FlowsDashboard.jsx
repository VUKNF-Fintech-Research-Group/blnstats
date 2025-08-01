'use client';

import React, { useState, useEffect } from "react";
import axios from "axios";
import toast, { Toaster } from 'react-hot-toast';
import { 
  Box, 
  Typography, 
  Paper,
  Tab,
  Tabs
} from '@mui/material';

import CurrencyBitcoinIcon from '@mui/icons-material/CurrencyBitcoin';





// Import our new components
import QuickActions from './components/QuickActions';
import ActiveWorkflows from './components/ActiveWorkflows';
import WorkflowTemplates from './components/WorkflowTemplates';
import SystemStatus from './components/SystemStatus';
import LogsViewer from './components/LogsViewer';

export default function FlowsDashboard() {
  const [activeTab, setActiveTab] = useState(0);
  const [workflowRuns, setWorkflowRuns] = useState([
    {
      id: 'ln-stats-pipeline-2024-01-15',
      name: 'Lightning Network Analytics Pipeline',
      status: 'running',
      progress: 45,
      startTime: '2024-01-15 14:30:00',
      estimatedEnd: '16:45:00',
      tasks: [
        { name: 'transformNodeMetrics', status: 'completed', duration: '2m 34s' },
        { name: 'generateGeneralStats', status: 'running', progress: 65 },
        { name: 'generateCoefficientCharts', status: 'pending' },
        { name: 'generateLorenzCharts', status: 'pending' },
        { name: 'generateCSV_EntityMetrics', status: 'pending' }
      ]
    },
    {
      id: 'blockchain-sync-daily',
      name: 'Daily Blockchain Synchronization',
      status: 'running',
      progress: 12,
      startTime: '2024-01-15 13:00:00',
      estimatedEnd: '18:30:00',
      tasks: [
        { name: 'sync_blocks', status: 'completed', duration: '45m 12s' },
        { name: 'sync_transactions', status: 'running', progress: 12, detail: '1.2M/10M transactions' }
      ]
    }
  ]);

  const [systemStatus, setSystemStatus] = useState({
    prefectServer: 'connected',
    workerPool: { active: 2, total: 3 },
    database: { blocks: '15.2M', transactions: '45.6M' },
    storage: { used: '245GB', total: '500GB', percentage: 49 }
  });

  const [workflowTemplates] = useState([
    {
      id: 'ln-analytics',
      name: 'Lightning Network Analytics Pipeline',
      description: 'Complete analysis including node metrics, statistics, and charts',
      estimatedDuration: '2-3 hours',
      lastRun: '2024-01-14 08:00:00'
    },
    {
      id: 'blockchain-sync',
      name: 'Blockchain Synchronization',
      description: 'Sync blocks and transactions from the network',
      estimatedDuration: '4-6 hours',
      lastRun: '2024-01-15 00:00:00'
    },
    {
      id: 'db-maintenance',
      name: 'Database Maintenance',
      description: 'Initialize database and import LND data',
      estimatedDuration: '30-60 minutes',
      lastRun: '2024-01-10 12:00:00'
    }
  ]);




  // Simulate real-time updates
  useEffect(() => {
    const interval = setInterval(() => {
      setWorkflowRuns(prev => prev.map(run => {
        if (run.status === 'running') {
          const newProgress = Math.min(run.progress + Math.random() * 2, 95);
          return { ...run, progress: newProgress };
        }
        return run;
      }));
    }, 3000);

    return () => clearInterval(interval);
  }, []);




  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };



  const triggerWorkflow = async (workflowId, parameters = {}) => {
    try {
      toast.loading(`Starting ${workflowId}...`);
      // Simulated API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      toast.dismiss();
      toast.success(`${workflowId} started successfully!`);
      
      // Add new workflow run (simulation)
      const newRun = {
        id: `${workflowId}-${Date.now()}`,
        name: workflowTemplates.find(t => t.id === workflowId)?.name || workflowId,
        status: 'running',
        progress: 0,
        startTime: new Date().toLocaleString(),
        tasks: []
      };
      setWorkflowRuns(prev => [newRun, ...prev]);
    } catch (error) {
      toast.error(`Failed to start ${workflowId}`);
    }
  };



  const stopWorkflow = async (runId) => {
    try {
      toast.loading('Stopping workflow...');
      await new Promise(resolve => setTimeout(resolve, 1000));
      toast.dismiss();
      toast.success('Workflow stopped');
      
      setWorkflowRuns(prev => prev.map(run => 
        run.id === runId ? { ...run, status: 'stopped' } : run
      ));
    } catch (error) {
      toast.error('Failed to stop workflow');
    }
  };



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



  return (
    <div className="w-full">
      <Toaster position="top-right" />
      <Box className="min-h-[calc(100vh-115px)] w-full flex flex-col p-6 bg-gray-50">
        
        {/* Header */}
        <Box className="mb-4">
          <Typography variant="h4" className="font-bold mb-2 flex items-center gap-2">
            <CurrencyBitcoinIcon className="text-yellow-500" sx={{ fontSize: 40 }} /> 
            BLN Stats - Workflow Dashboard
          </Typography>
          <Typography variant="subtitle1" color="textSecondary">
            Manage and monitor Lightning Network data processing workflows
          </Typography>
        </Box>

        {/* Quick Actions */}
        <QuickActions triggerWorkflow={triggerWorkflow} />

        {/* Main Content Tabs */}
        <Paper className="flex-1">
          <Tabs value={activeTab} onChange={handleTabChange} className="border-b">
            <Tab label={`Active Workflows (${workflowRuns.filter(r => r.status === 'running').length})`} />
            <Tab label="Templates" />
            {/* <Tab label="System Status" />
            <Tab label="Logs" /> */}
          </Tabs>

          <Box className="p-4">
            {/* Active Workflows Tab */}
            {activeTab === 0 && (
              <ActiveWorkflows 
                workflowRuns={workflowRuns}
                stopWorkflow={stopWorkflow}
                getStatusColor={getStatusColor}
                getStatusEmoji={getStatusEmoji}
              />
            )}

            {/* Workflow Templates Tab */}
            {activeTab === 1 && (
              <WorkflowTemplates 
                workflowTemplates={workflowTemplates}
                triggerWorkflow={triggerWorkflow}
              />
            )}

          </Box>
        </Paper>
      </Box>
    </div>
  );
}
