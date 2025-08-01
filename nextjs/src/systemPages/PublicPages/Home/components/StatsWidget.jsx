import React from 'react';
import { Card, Typography } from '@mui/material';

const StatsWidget = ({ 
  icon: Icon, 
  title, 
  value, 
  changePercent, 
  isPositive = true,
  changeLabel = "vs last month" 
}) => {
  return (
    <Card
      className="flex-1 min-w-60 h-52 flex flex-col items-center justify-center text-center p-4"
      elevation={4}
    >
      <Icon color="primary" className="mb-2" sx={{ fontSize: 72 }} />
      <Typography variant="h6" className="mb-1">
        {title}
      </Typography>
      <Typography variant="h4" className="mb-2">
        {value}
      </Typography>
      <div className="flex flex-col items-center mt-2">
        <span className={`text-sm font-medium ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
          {isPositive ? '+' : ''}{changePercent}%
        </span>
        <span className="text-gray-500 text-xs ml-1">
          {changeLabel}
        </span>
      </div>
    </Card>
  );
};

export default StatsWidget; 