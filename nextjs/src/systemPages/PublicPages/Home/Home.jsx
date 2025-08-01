'use client';

import { useState, useEffect } from 'react';
import PublicPageLayout from "@/systemPages/PublicPages/PublicPageLayout"
// import Footer from './components/Footer';
// import SectionCard from '@/components/SectionCard';
import { Card, Box, CardContent, Typography, Divider, Container, MenuItem, Stack, Grid } from "@mui/material";
import Link from "next/link";
import Image from 'next/image';
import CurrencyBitcoinIcon from '@mui/icons-material/CurrencyBitcoin';
import HubIcon from '@mui/icons-material/Hub';
import PolylineIcon from '@mui/icons-material/Polyline';
import StatsWidget from './components/StatsWidget';
import axios from 'axios';


import GeneralChart from './components/GeneralChart';



export default function Home({ authData }) {

  const [rawData, setRawData] = useState(null);
  useEffect(() => {
    async function getData() {
      try {
        const response = await axios.get(`/rawdata/GENERATED/General_Stats/20XX-XX-01.json`);
        setRawData(response.data);
      } catch (error) {}
    }
    getData();
  }, []);



  // --- Extract latest stats ---
  let latest = null, prev = null, lastDate = null, prevDate = null;
  if (rawData && rawData.data) {
    const keys = Object.keys(rawData.data).sort((a, b) => Number(a) - Number(b));
    const lastKey = keys[keys.length - 1];
    const prevKey = keys[keys.length - 2];
    latest = rawData.data[lastKey];
    prev = rawData.data[prevKey];
    lastDate = rawData.data[lastKey]["date"];
    prevDate = rawData.data[prevKey]["date"];
  }

  // --- Calculate percent changes ---
  function percentChange(current, previous) {
    if (previous === 0 || previous === undefined) return "0.0";
    return (((current - previous) / previous) * 100).toFixed(1);
  }




  return (
    <PublicPageLayout authData={authData} fullWidth={false}>
      {(authData) => (
        <div className="flex flex-col items-center justify-center lg:w-[1000px] px-4 lg:px-0">
          <div className="w-full px-4">
            <div className="flex flex-col md:flex-row gap-6">
              <StatsWidget
                icon={CurrencyBitcoinIcon}
                title="Total Network Capacity"
                value={
                  latest
                    ? `${latest.network_capacity.toLocaleString(undefined, { maximumFractionDigits: 2 })} BTC`
                    : "—"
                }
                changePercent={
                  latest && prev
                    ? percentChange(latest.network_capacity, prev.network_capacity)
                    : "0.0"
                }
                isPositive={
                  latest && prev
                    ? latest.network_capacity >= prev.network_capacity
                    : true
                }
                changeLabel={`${lastDate} vs ${prevDate}`}
              />

              <StatsWidget
                icon={HubIcon}
                title="Total Node Count"
                value={latest ? latest.node_count.toLocaleString() : "—"}
                changePercent={
                  latest && prev
                    ? percentChange(latest.node_count, prev.node_count)
                    : "0.0"
                }
                isPositive={
                  latest && prev
                    ? latest.node_count >= prev.node_count
                    : true
                }
                changeLabel={`${lastDate} vs ${prevDate}`}
              />

              <StatsWidget
                icon={PolylineIcon}
                title="Total Channel Count"
                value={latest ? latest.channel_count.toLocaleString() : "—"}
                changePercent={
                  latest && prev
                    ? percentChange(latest.channel_count, prev.channel_count)
                    : "0.0"
                }
                isPositive={
                  latest && prev
                    ? latest.channel_count >= prev.channel_count
                    : true
                }
                changeLabel={`${lastDate} vs ${prevDate}`}
              />
            </div>
          </div>

          {/* Divider */}
          <div className="w-full border-t border-gray-300 m-8"></div>

          <div className="w-full px-4">
            <GeneralChart
              title="Total network capacity in the BLN network"
              yAxisLabel="Total Network Capacity (BTC)"
              data={rawData}
              dataKey="network_capacity"
              height={400}
            />

            <GeneralChart
              title="Total node count in the BLN network"
              yAxisLabel="Total Number of Nodes"
              data={rawData}
              dataKey="node_count"
              height={400}
            />

            <GeneralChart
              title="Total channel count in the BLN network"
              yAxisLabel="Total Number of Channels"
              data={rawData}
              dataKey="channel_count"
              height={400}
            />
          </div>


          {/* Divider */}
          <div className="w-full border-t border-gray-300 m-8"></div>

          

        </div>
      )}
    </PublicPageLayout>
  );
}