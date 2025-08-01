'use client';

import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import Image from 'next/image';
import { useSearchParams } from 'next/navigation'

import { Button, Box, Stack, FormControl, TextField, Typography } from "@mui/material";

import Particles from './components/Particles/Particles';
import BouncingDotsLoader from './components/BouncingDotsLoader/BouncingDotsLoader';




export default function LoginPage({ deleteTokens }) {  

  // Delete Cookies
  const deleteTokensRef = useRef(deleteTokens);
  useEffect(() => {
    deleteTokensRef.current = deleteTokens;
  });
  useEffect(() => {
    deleteTokensRef.current();
  }, []);



  const [loggingIn, setLoggingIn] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorBoxText, setErrorBoxText] = useState("");



  // Get redirectTo from URL parameter
  const searchParams = useSearchParams()
  const redirectTo = searchParams.get('redirectTo')


  async function handleLogin(email, password) {
    await axios.post("/api/login", { email: email, password: password }).then((response) => {
      if(response.data === "OK"){
        window.location.href=redirectTo || '/'
      }
      else{
        setErrorBoxText(response.data);
      }
    });
  }





  return (
    <Box className="bg-gradient-to-br from-[#7b4397] to-[#dc2430] top-0 right-0 bottom-0 left-0 -z-2 h-screen overflow-scroll">


      {/* Login Form */}
      <Box className="absolute left-1/2 transform -translate-x-1/2 top-[15%] flex flex-col bg-white p-7 gap-4 rounded-[15px] z-[1] min-w-[350px]">

        <Image src='/knf-color.png' alt='' width={250} height={83} className="rounded-2xl"/>

        <Box className="text-center mt-2">
          <Typography component="h1" level="inherit" fontSize="1.25em" mb="0.25em">
            <b>Bitcoin LN Statistics</b>
          </Typography>
        </Box>

        <Stack spacing={2} className="mt-2.5 mb-2 text-black" >
          <FormControl color="primary">
            <TextField required className="text-black placeholder:text-black"
            variant="standard" label="Email" onChange={(e) => { setEmail(e.currentTarget.value) }} />
          </FormControl>

          <FormControl color="primary">
            <TextField required variant="standard" type="password" label="Password" onKeyDown={(e) => e.key === 'Enter' ? handleLogin(email, password) : ''} onChange={(e) => { setPassword(e.currentTarget.value) }} />
          </FormControl>
        </Stack>


        <Box className="text-xs text-red-500 text-center whitespace-pre-wrap">
          {errorBoxText}
        </Box>

        {loggingIn ?
          <Button onClick={() => {handleLogin(email, password)}} disabled={true} style={{ backgroundColor: 'grey', color: 'white', pointerEvents: 'none', }}>
            PLEASE WAIT <BouncingDotsLoader />
          </Button>
          :
          <Button sx={{ backgroundColor: 'rgb(123, 0, 63)', color: 'white' }} onClick={() => {handleLogin(email, password)}} >
            LOGIN
          </Button>
        }
      </Box>



      {/* Particles */}
      <Box className="fixed h-screen"><Particles/></Box>
      


      {/* Footer */}
      <Box className="h-[100px] w-full absolute bottom-0 flex items-center justify-center">
        <Box className="text-white text-[0.7em] leading-[10px] mt-[50px] text-center">
          Copyright © | All Rights Reserved | Vilnius university Kaunas faculty
        </Box>
      </Box>

      
    </Box>
  );
}


