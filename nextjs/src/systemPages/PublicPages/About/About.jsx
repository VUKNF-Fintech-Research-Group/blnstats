'use client';
import PublicPageLayout from "@/systemPages/PublicPages/PublicPageLayout"
import Image from 'next/image';
import { Card, Box, CardContent, Typography } from '@mui/material';


export default function About({ authData }) {

  

  return (
    <PublicPageLayout authData={authData} fullWidth={false}>
      {(authData) => (
        <div className="w-full">

          <Card elevation={1} className="w-full">
            <Box className="flex flex-col lg:flex-row">
              <CardContent>
                <Typography
                  style={{textAlign: 'justify'}}
                >
                  This is the about page.
                </Typography>
              </CardContent>
            </Box>
          </Card>



        </div>
      )}
    </PublicPageLayout>
  );
}