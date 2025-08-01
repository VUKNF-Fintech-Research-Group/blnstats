'use client';

import { Box } from "@mui/material";
import Header from "@/components/Header"
import AdminSidebar from "@/components/Admin/Sidebar/Sidebar"


export default function AdminPageLayout({ authData, children }) {
  return (
    <Box className="flex flex-col">
      <Header authData={authData}/>
      <Box className="flex flex-row">
        <AdminSidebar authData={authData}/>
        {children}
      </Box>
      <Box className="h-[30px] flex justify-center items-center text-[0.7em]" sx={{ backgroundColor: 'primary.main', color: 'white' }}>
        Copyright © | All Rights Reserved | Vilnius university Kaunas faculty
      </Box>
    </Box>
  )
}
