'use client';

import { AppBar, Button, Toolbar, Box, MenuItem, Typography, Menu, IconButton, Divider, Container, ListItemIcon } from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import LoginIcon from "@mui/icons-material/Login";
import LogoutIcon from "@mui/icons-material/Logout";
import PersonAdd from '@mui/icons-material/PersonAdd';
import Settings from '@mui/icons-material/Settings';
import Logout from '@mui/icons-material/Logout';

import Link from "next/link";
import Image from 'next/image';


import ElectricBoltSharpIcon from '@mui/icons-material/ElectricBoltSharp';

// import { useTranslations, useLocale } from "next-intl";
import { usePathname } from 'next/navigation';
import Cookies from 'js-cookie';

import * as React from "react";

// import LanguageSwitcher from '@/components/LanguageSwitcher';
// import ThemeSwitcher from '@/components/ThemeSwitcher';


const NavbarButton = ({ href, text, pathname, newTab, show=true }) => {
  if(!show) return null;
  return (
    <Link href={href} passHref target={newTab ? "_blank" : "_self"}>
      <MenuItem size="large" color="inherit" sx={{ borderRadius: "5px", '&:hover': { backgroundColor: 'rgba(255, 255, 255, 0.1)' } }}>
        <Typography fontFamily={"Tahoma, sans-serif"} style={{ textDecoration: pathname === href ? "underline" : "none" }} >
          {text}
        </Typography>
      </MenuItem>
    </Link>
  );
};



export default function Header({ authData }) {

  // // Get locale and translations
  // const locale = useLocale();
  // const t = useTranslations("navbar");

  // Get current url
  const pathname = usePathname();







  let userLoginLogoutButton;
  if (authData !== undefined) {
    userLoginLogoutButton = (
      <Button className="ml-1 block" color="inherit"
        sx={{ '&:hover': { backgroundColor: 'rgba(255, 255, 255, 0.1)' } }}
        onClick={() => signOut()}
        startIcon={<LogoutIcon />}
      >
        Logout
      </Button>
    );
  } else {
    userLoginLogoutButton = (
      <Button
        sx={{ '&:hover': { backgroundColor: 'rgba(255, 255, 255, 0.1)' } }}
        className="ml-1"
        color="inherit"
        href={"/login?redirectTo=" + pathname}
        startIcon={<LoginIcon />}
      >
        Login
      </Button>
    );
  }




  // Sign out function
  const signOut = () => {
    Cookies.remove('session');
    window.location.reload();
  }



  // Mobile dropdown menu
  const [anchorEl, setAnchorEl] = React.useState(null);
  const handleClick = (event) => {
    setAnchorEl(event.currentTarget);
  };
  const handleClose = () => {
    setAnchorEl(null);
  };





  return (
    <AppBar position={"static"} color="primary">
      <Container maxWidth={false} disableGutters>
        <Toolbar>

          {/* Left side of navbar */}
          <Link href="/" passHref>
            <Image src={"/vulogo.png"} alt={"Logo"} width={80} height={80} className="cursor-pointer rounded-2xl p-3"/>
          </Link>

          <Link href="/" className="ml-4 text-decoration-none">
            <div className="border border-white rounded-xl text-white p-2 flex flex-row">
              <ElectricBoltSharpIcon className="mr-2"/>
              <div className="pr-1.5">Bitcoin LN Statistics</div>
            </div>
          </Link>

          <Box className="ml-4 hidden lg:flex">
            <Box className="flex justify-start p-2 m-2 mx-auto gap-1">
              <NavbarButton href={`/`} text={"Home"} pathname={pathname} />
              <NavbarButton href={`/datasources`} text={"Sources"} pathname={pathname} />
              <NavbarButton href={`/snapshots`} text={"Snapshots"} pathname={pathname} />
              <NavbarButton href={`/coefficients`} text={"Coefficients"} pathname={pathname} />
              <NavbarButton href={`/lorenz`} text={"Lorenz Curves"} pathname={pathname} />
              {/* <NavbarButton href={`/search`} text={"Search"} pathname={pathname} /> */}
              {/* <NavbarButton href={`/about`} text={"About"} pathname={pathname} /> */}
              <NavbarButton href={`/admin`} text={"Admin"} pathname={pathname} show={authData !== undefined} />
            </Box>
          </Box>

          


          
          {/* Right side of navbar */}
          <Box className="flex-grow justify-end hidden lg:flex gap-1">
            <NavbarButton href={`/rawdata`} text={"Raw Data"} pathname={pathname} newTab={true} />
            {userLoginLogoutButton}
            <IconButton edge="start" aria-label="menu" >
              <Menu keepMounted >
                {userLoginLogoutButton}
              </Menu>
            </IconButton>
          </Box>


          {/* Right side of navbar - Mobile menu button */}
          <Box className="flex-grow flex justify-end lg:hidden" sx={{width: 20}}>
            <IconButton
              aria-controls="mobile-menu"
              aria-haspopup="true"
              onClick={handleClick}
              color="inherit"
            >
              <MenuIcon />
            </IconButton>
            <Menu
              id="mobile-menu"
              anchorEl={anchorEl}
              keepMounted
              open={Boolean(anchorEl)}
              onClose={handleClose}
              transformOrigin={{ horizontal: 'right', vertical: 'top' }}
              anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
            >
              <NavbarButton href={`/`} text={"Home"} pathname={pathname} />
              <NavbarButton href={`/datasources`} text={"Sources"} pathname={pathname} />
              <NavbarButton href={`/snapshots`} text={"Snapshots"} pathname={pathname} />
              <NavbarButton href={`/coefficients`} text={"Coefficients"} pathname={pathname} />
              <NavbarButton href={`/lorenz`} text={"Lorenz Curves"} pathname={pathname} />
              {/* <NavbarButton href={`/admin`} text={"Admin"} pathname={pathname} show={authData !== undefined} /> */}
              <Divider />
              <NavbarButton href={`/rawdata`} text={"Raw Data"} pathname={pathname} newTab={true} />
              <Divider />
              <MenuItem onClick={handleClose}>
                {userLoginLogoutButton}
              </MenuItem>
            </Menu>
          </Box>
          
          
        </Toolbar>
      </Container>
    </AppBar>
  );
}