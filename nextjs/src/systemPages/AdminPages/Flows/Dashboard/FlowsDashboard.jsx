'use client';

import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import toast, { Toaster } from 'react-hot-toast';
import { 
  Box, 
  Typography, 
  Paper,
  Tab,
  Tabs,
  Alert,
  CircularProgress
} from '@mui/material';

import CurrencyBitcoinIcon from '@mui/icons-material/CurrencyBitcoin';

// Import our new components
import QuickActions from './components/QuickActions';
import ActiveWorkflows from './components/ActiveWorkflows';
import WorkflowTemplates from './components/WorkflowTemplates';

// --- Static Helper Functions ---

const calculateDuration = (startTime, endTime, status) => {
  if (!startTime) return null;
  const start = new Date(startTime);
  const end = endTime ? new Date(endTime) : new Date();
  if (status !== 'completed' && status !== 'running') return null;
  const durationMs = end - start;
  if (durationMs < 1000) return `${durationMs}ms`;
  if (durationMs < 60000) return `${Math.round(durationMs / 1000)}s`;
  if (durationMs < 3600000) return `${Math.round(durationMs / 60000)}m`;
  return `${(durationMs / 3600000).toFixed(1)}h`;
};

const mapPrefectStateToStatus = (stateType) => {
  switch (stateType?.toLowerCase()) {
    case 'completed': return 'completed';
    case 'running': return 'running';
    case 'pending': case 'scheduled': return 'pending';
    case 'failed': return 'failed';
    case 'cancelled': case 'canceled': return 'stopped';
    default: return 'pending';
  }
};

// --- Main Dashboard Component ---

export default function FlowsDashboard() {
  const [activeTab, setActiveTab] = useState(0);
  
  const [workflowRuns, setWorkflowRuns] = useState([]);
  const [runsLoading, setRunsLoading] = useState(true);
  const [runsError, setRunsError] = useState(null);

  const [prefectDeployments, setPrefectDeployments] = useState([]);
  const [deploymentsLoading, setDeploymentsLoading] = useState(true);
  const [deploymentsError, setDeploymentsError] = useState(null);

  const [workflowTemplates, setWorkflowTemplates] = useState([]);

  // --- Data Fetching and Processing ---

  const fetchPrefectDeployments = useCallback(async () => {
    try {
      setDeploymentsLoading(true);
      setDeploymentsError(null);
      const response = await axios.post('/prefect/api/deployments/filter', {}, {
        headers: { 'Content-Type': 'application/json' },
        withCredentials: true
      });
      const newDeployments = response.data;
      setPrefectDeployments(newDeployments);
      const templates = newDeployments.map(d => ({
        id: d.id, name: d.name, description: d.description || 'Prefect deployment',
        flowName: d.flow_name, lastRun: d.updated
      }));
      setWorkflowTemplates(templates);
    } catch (error) {
      setDeploymentsError(error.message || 'Failed to connect to Prefect');
      setPrefectDeployments([]);
      setWorkflowTemplates([]);
    } finally {
      setDeploymentsLoading(false);
    }
  }, []);

  const processFlowRunData = useCallback((runs, flows, tasks, deployments) => {
    const flowsById = new Map(flows.map(f => [f.id, f]));
    const tasksByFlowRunId = new Map();
    for (const task of tasks) {
        if (!tasksByFlowRunId.has(task.flow_run_id)) {
            tasksByFlowRunId.set(task.flow_run_id, []);
        }
        tasksByFlowRunId.get(task.flow_run_id).push(task);
    }

    const subflowsByParentTaskId = new Map();
    for (const run of runs) {
        if (run.parent_task_run_id) {
            subflowsByParentTaskId.set(run.parent_task_run_id, run);
        }
    }
    
    const topLevelRuns = runs.filter(run => !run.parent_task_run_id);

    return topLevelRuns.map(run => {
        const deployment = deployments.find(d => d.id === run.deployment_id);
        const flow = flowsById.get(run.flow_id);
        const displayName = deployment ? deployment.name : (flow ? flow.name : run.name);

        const runTasks = tasksByFlowRunId.get(run.id) || [];
        const runItems = runTasks.map(task => {
            const subflowRun = subflowsByParentTaskId.get(task.id);
            if (subflowRun) {
                const subflowFlow = flowsById.get(subflowRun.flow_id);
                const subflowName = subflowFlow ? subflowFlow.name : subflowRun.name;
                const subflowStatus = mapPrefectStateToStatus(subflowRun.state?.type);
                const subflowTasks = (tasksByFlowRunId.get(subflowRun.id) || [])
                    .sort((a,b) => new Date(a.start_time) - new Date(b.start_time))
                    .map(sft => {
                        const sftStatus = mapPrefectStateToStatus(sft.state?.type);
                        return { type: 'task', id: sft.id, name: sft.name, status: sftStatus, duration: calculateDuration(sft.start_time, sft.end_time, sftStatus), startTime: sft.start_time };
                    });
                return { type: 'subflow', id: subflowRun.id, name: subflowName, status: subflowStatus, duration: calculateDuration(subflowRun.start_time, subflowRun.end_time, subflowStatus), startTime: task.start_time, tasks: subflowTasks };
            }
            const taskStatus = mapPrefectStateToStatus(task.state?.type);
            return { type: 'task', id: task.id, name: task.name, status: taskStatus, duration: calculateDuration(task.start_time, task.end_time, taskStatus), startTime: task.start_time };
        });

        runItems.sort((a,b) => new Date(a.startTime) - new Date(b.startTime));

        return { id: run.id, name: displayName, status: mapPrefectStateToStatus(run.state?.type), startTime: run.start_time ? new Date(run.start_time).toLocaleString() : 'Not started', tasks: runItems };
    });
  }, []);

  const fetchAndProcessRuns = useCallback(async (isBackgroundRefresh = false) => {
    if (!isBackgroundRefresh) setRunsLoading(true);
    try {
      const runsResponse = await axios.post('/prefect/api/flow_runs/filter', { sort: "START_TIME_DESC", limit: 50, flow_runs: { state: { type: { any_: ["RUNNING", "PENDING", "SCHEDULED", "COMPLETED", "FAILED", "CANCELLED"] } } } }, { headers: { 'Content-Type': 'application/json' }, withCredentials: true });
      const flowRuns = runsResponse.data;
      if (flowRuns.length === 0) {
        setWorkflowRuns([]);
        return;
      }
      const allFlowIds = [...new Set(flowRuns.map(run => run.flow_id))];
      const flowsResponse = await axios.post('/prefect/api/flows/filter', { flows: { id: { any_: allFlowIds } } }, { headers: { 'Content-Type': 'application/json' }, withCredentials: true });
      const taskRunsResponse = await axios.post('/prefect/api/task_runs/filter', { flow_runs: { id: { any_: flowRuns.map(r => r.id) } } }, { headers: { 'Content-Type': 'application/json' }, withCredentials: true });
      
      const finalRuns = processFlowRunData(flowRuns, flowsResponse.data, taskRunsResponse.data, prefectDeployments);
      setWorkflowRuns(finalRuns);
      setRunsError(null);
    } catch (error) {
      console.error('Error fetching Prefect flow runs:', error);
      if (!isBackgroundRefresh) {
        setRunsError(error.message || 'Failed to fetch flow runs');
        setWorkflowRuns([]);
      }
    } finally {
      if (!isBackgroundRefresh) setRunsLoading(false);
    }
  }, [prefectDeployments, processFlowRunData]);

  // --- Effects ---

  useEffect(() => {
    fetchPrefectDeployments();
  }, [fetchPrefectDeployments]);
  
  useEffect(() => {
    if (!deploymentsLoading) {
      fetchAndProcessRuns(false);
    }
  }, [deploymentsLoading, fetchAndProcessRuns]);

  useEffect(() => {
    const intervalId = setInterval(() => {
      if (!deploymentsLoading) {
        fetchAndProcessRuns(true);
      }
    }, 10000);
    return () => clearInterval(intervalId);
  }, [deploymentsLoading, fetchAndProcessRuns]);

  // --- Handlers ---

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const triggerWorkflow = async (workflowId) => {
    try {
      toast.loading(`Starting workflow...`);
      const deployment = prefectDeployments.find(d => d.id === workflowId);
      if (deployment) {
        await axios.post(`/prefect/api/deployments/${deployment.id}/create_flow_run`, {}, { headers: { 'Content-Type': 'application/json' }, withCredentials: true });
        toast.dismiss();
        toast.success(`Successfully triggered '${deployment.name}'`);
        setTimeout(() => fetchAndProcessRuns(), 1500);
      } else {
        toast.dismiss();
        toast.error('Deployment not found');
      }
    } catch (error) {
      toast.dismiss();
      toast.error(`Failed to start workflow: ${error.response?.data?.detail || error.message}`);
    }
  };

  // The stopWorkflow function has been removed.

  // --- Render ---

  return (
    <div className="w-full">
      <Toaster position="top-right" />
      <Box className="min-h-[calc(100vh-115px)] w-full flex flex-col p-4 bg-gray-50">
        
        <Box sx={{ fontSize: '24px', color: 'gray', width: '100%' }}>
          Workflows
        </Box>

        {deploymentsError && (
          <Alert severity="error" className="mb-4" action={<button onClick={fetchPrefectDeployments} className="text-red-600 underline hover:no-underline">Retry</button>}>
            <strong>Deployments Error:</strong> {deploymentsError}
          </Alert>
        )}
        {runsError && !runsLoading && (
          <Alert severity="error" className="mb-4" action={<button onClick={() => fetchAndProcessRuns(false)} className="text-red-600 underline hover:no-underline">Retry</button>}>
            <strong>Flow Runs Error:</strong> {runsError}
          </Alert>
        )}

        <QuickActions triggerWorkflow={triggerWorkflow} />

        <Paper className="flex-1">
          <Tabs value={activeTab} onChange={handleTabChange} className="border-b">
            <Tab label={`Active Workflows ${!runsLoading ? `(${workflowRuns.filter(r => r.status === 'running').length})` : ''}`} />
            <Tab label={`Templates ${deploymentsLoading ? '' : `(${workflowTemplates.length})`}`} />
          </Tabs>

          <Box className="p-4">
            {activeTab === 0 && (
              runsLoading ? (
                <Box className="flex items-center justify-center py-8">
                  <CircularProgress />
                  <Typography className="ml-2">Loading flow runs...</Typography>
                </Box>
              ) : (
                <ActiveWorkflows workflowRuns={workflowRuns} />
              )
            )}
            {activeTab === 1 && (
              deploymentsLoading ? (
                 <Box className="flex items-center justify-center py-8">
                    <CircularProgress />
                    <Typography className="ml-2">Loading deployments...</Typography>
                  </Box>
              ) : (
                 <WorkflowTemplates workflowTemplates={workflowTemplates} triggerWorkflow={triggerWorkflow} />
              )
            )}
          </Box>
        </Paper>
      </Box>
    </div>
  );
}
