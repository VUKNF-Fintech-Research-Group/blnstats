"use client";

import Link from "next/link";
import { Box, Paper, Button } from "@mui/material";
import { useState, useEffect } from "react";



// Collapse/Expand Sidebar
import KeyboardDoubleArrowLeftIcon from '@mui/icons-material/KeyboardDoubleArrowLeft';
import KeyboardDoubleArrowRightIcon from '@mui/icons-material/KeyboardDoubleArrowRight';

// Main
import AirIcon from '@mui/icons-material/Air';

// System
import BadgeIcon from '@mui/icons-material/Badge';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import StorageIcon from '@mui/icons-material/Storage';
import ExitToAppIcon from "@mui/icons-material/ExitToApp";



export default function AdminSidebar({ authData }) {


  const [open, setopen] = useState(true);
  useEffect(() => {
    setopen(localStorage.getItem("sidebarOpen") !== "false");
  }, [])

  const toggleOpen = () => {
    var sidebarOpendNewValue = !open;
    setopen(sidebarOpendNewValue)
    localStorage.setItem('sidebarOpen', sidebarOpendNewValue);
  }

  console.log(authData);

  return (
    <Paper className="px-[10px]" sx={{ borderRadius: 0 }}>
      <ul className="list-none m-0 p-0">
        
        {/* Toggle sidebar */}
        <Button onClick={toggleOpen} className="cursor-pointer w-full" sx={{ backgroundColor: 'primary.main', color: "darkgray", marginTop: '10px' }}>
          {open ? 
            <KeyboardDoubleArrowLeftIcon className="align-middle" /> : 
            <KeyboardDoubleArrowRightIcon className="align-middle" />
          }
        </Button>




        {/* MAIN */}
        <p className="text-[10px] font-bold text-[#999] mt-[15px] mb-[2px] whitespace-pre-wrap">
          {open ? "MAIN" : "-----"}
        </p>
        <Link href="/admin" className="no-underline">
          <li className="flex items-center p-[3px] pl-[6px] pr-[10px] cursor-pointer whitespace-nowrap hover:bg-[#999] hover:rounded">
            <AirIcon className="text-[17px]" sx={{ color: 'primary.main' }} />
            {open ? <span className="text-[13px] font-semibold ml-[10px]">Workflows</span> : <></>}
          </li>
        </Link>

        <Link href="/admin/administrators" className="no-underline">
          <li className="flex items-center p-[3px] pl-[6px] pr-[10px] cursor-pointer whitespace-nowrap hover:bg-[#999] hover:rounded">
            <BadgeIcon className="text-[17px]" sx={{ color: 'primary.main' }}/>
            {open ? <span className="text-[13px] font-semibold ml-[10px]">Administrators</span> : <></>}
          </li>
        </Link>
        


        {/* SUBSYSTEMS */}
        <>
          <p className="text-[10px] font-bold text-[#999] mt-[15px] mb-[2px] whitespace-pre-wrap">
            {open ? "SUBSYSTEMS" : "-----"}
          </p>


          <Link href="/filebrowser" className="no-underline" target="_blank" rel="noopener noreferrer">
            <li className="flex items-center p-[3px] pl-[6px] pr-[10px] cursor-pointer whitespace-nowrap hover:bg-[#999] hover:rounded">
              <UploadFileIcon className="text-[17px]" sx={{ color: 'primary.main' }} />
              {open ? <span className="text-[13px] font-semibold ml-[10px]">File Browser</span> : <></>}
            </li>
          </Link>


          <Link href="/prefect" className="no-underline" target="_blank" rel="noopener noreferrer">
            <li className="flex items-center p-[3px] pl-[6px] pr-[10px] cursor-pointer whitespace-nowrap hover:bg-[#999] hover:rounded">
              <AccountTreeIcon className="text-[17px]" sx={{ color: 'primary.main' }} />
              {open ? <span className="text-[13px] font-semibold ml-[10px]">Prefect Server</span> : <></>}
            </li>
          </Link>


          <Link href="/dbgate" className="no-underline" target="_blank" rel="noopener noreferrer">
            <li className="flex items-center p-[3px] pl-[6px] pr-[10px] cursor-pointer whitespace-nowrap hover:bg-[#999] hover:rounded">
              <StorageIcon className="text-[17px]" sx={{ color: 'primary.main' }} />
              {open ? <span className="text-[13px] font-semibold ml-[10px]">DBGate</span> : <></>}
            </li>
          </Link>
        </>


        <p className="text-[10px] font-bold text-[#999] mt-[15px] mb-[2px] whitespace-pre-wrap">
          {open ? "ACCOUNT" : "-----"}
        </p>
        <Link href="/login" className="no-underline">
          <li className="flex items-center p-[3px] pl-[6px] pr-[10px] cursor-pointer whitespace-nowrap hover:bg-[#999] hover:rounded">
            <ExitToAppIcon className="text-[17px]" sx={{ color: 'primary.main' }} />
            {open ? <span className="text-[13px] font-semibold ml-[10px]">Logout</span> : <></>}
          </li>
        </Link>



      </ul>
    </Paper>
  );
}