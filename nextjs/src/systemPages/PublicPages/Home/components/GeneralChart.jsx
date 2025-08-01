import React, { useMemo } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Brush
} from 'recharts';
import { useTheme } from '@mui/material/styles';



const formatBitcoin = (value) => `${value.toLocaleString(undefined, { maximumFractionDigits: 2 })} BTC`;
const formatNodeCount = (value) => `${value.toLocaleString()} nodes`;




// Custom tooltip component
const CustomTooltip = ({ active, payload, dataKey }) => {
  const theme = useTheme();



  if (active && payload && payload.length) {
    const data = payload[0].payload;
    const value = payload[0].value;
    
    // Format value based on data type
    const formatValue = (val) => {
      if (dataKey === 'network_capacity') {
        return formatBitcoin(val);
      } else if (dataKey === 'node_count') {
        return formatNodeCount(val);
      }
      return val.toLocaleString();
    };

    return (
      <div className="bg-gray-800 text-white p-3 rounded-lg shadow-lg border border-gray-600">
        <div className="font-semibold mb-1" style={{ color: theme.palette.primary.accent }}>
          {data.date}  {/* Use the date field directly (already in YYYY-MM-DD format) */}
        </div>
        <div className="text-lg font-bold">
          {formatValue(value)}
        </div>
        <div className="text-xs text-gray-300 mt-1">
          Block: {data.blockHeight}
        </div>
      </div>
    );
  }
  return null;
};



// Custom Y-axis tick formatter
const formatYAxisTick = (value) => {
  if (value >= 1000) {
    return `${(value / 1000).toFixed(0)}k`;
  }
  return value.toLocaleString();
};








export default function GeneralChart({ data, height = 400, title, dataKey, yAxisLabel }) {
  const theme = useTheme();


  // Transform data from object to array
  const chartData = useMemo(() => {
    if (!data?.data) return [];
    
    return Object.entries(data.data)
      .map(([blockHeight, entry]) => ({
        blockHeight,
        timestamp: entry.timestamp,
        date: entry.date,
        [dataKey]: entry[dataKey],
      }))
      .sort((a, b) => a.timestamp - b.timestamp);
  }, [data]);




  const formatXAxisTick = (tickItem) => {
    // Find the corresponding date from chartData
    const dataPoint = chartData.find(item => item.timestamp === tickItem);
    if (dataPoint && dataPoint.date) {
      return dataPoint.date.substring(0, 7); // Extract YYYY-MM from YYYY-MM-DD
    }
    // Fallback to timestamp conversion if date not found
    const date = new Date(tickItem * 1000);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    return `${year}-${month}`;
  };



  if (!chartData.length) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500 bg-gray-50 rounded-lg">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
          <div>Loading chart data...</div>
        </div>
      </div>
    );
  }



  // Handle mousedown to prevent focus
  const handleMouseDown = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };



  return (
    <div className="w-full">
      <div className="p-4 bg-gray-50 rounded-lg mb-8">
        <h3 className="text-2xl font-bold text-gray-800 mb-4">
          {title}
        </h3>
      
        <div 
          className="bg-white p-4 rounded-lg shadow-sm border" 
          onMouseDown={handleMouseDown}
          style={{ outline: 'none' }}
        >
          <ResponsiveContainer width="100%" height={height}>
          <AreaChart
            data={chartData}
          >
            <defs>
              <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={theme.palette.primary.accent} stopOpacity={0.8}/>
                <stop offset="100%" stopColor={theme.palette.primary.accent} stopOpacity={0.1}/>
              </linearGradient>
            </defs>
            <CartesianGrid 
              strokeDasharray="3 3" 
              stroke="#e2e8f0" 
              strokeOpacity={0.6}
            />
            <XAxis
              dataKey="timestamp"
              type="number"
              scale="time"
              domain={['dataMin', 'dataMax']}
              tickFormatter={formatXAxisTick}
              stroke="#64748b"
              fontSize={12}
              tickMargin={8}
              minTickGap={30}
            />
            <YAxis
              tickFormatter={formatYAxisTick}
              stroke="#64748b"
              fontSize={12}
              tickMargin={8}
              label={{ 
                value: yAxisLabel, 
                angle: -90, 
                position: 'insideLeft',
                style: { textAnchor: 'middle', fill: '#64748b', fontSize: '12px' }
              }}
            />
            <Tooltip
              content={<CustomTooltip dataKey={dataKey} />}
              cursor={{
                stroke: theme.palette.primary.main,
                strokeWidth: 1,
                strokeDasharray: '5 5'
              }}
            />
            <Area
              type="monotone"
              dataKey={dataKey}
              stroke={theme.palette.primary.main}
              strokeWidth={2}
              fill="url(#colorGradient)"
              dot={false}
              activeDot={{
                r: 6,
                stroke: theme.palette.primary.main,
                strokeWidth: 2,
                fill: '#ffffff'
              }}
            />
            
            {/* Brush for time range selection */}
            <Brush
              dataKey="timestamp"
              height={20}
              stroke={theme.palette.primary.main}
              fill="#f8fafc"
              tickFormatter={formatXAxisTick}
              className="recharts-brush"
            />
          </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
} 