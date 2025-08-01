'use client';

import { useState, useEffect } from 'react';
import { Divider, Box, Container, Grid, Typography, MenuItem } from "@mui/material";
import { useTranslations, useLocale } from "next-intl";

import Image from "next/image";
import Link from "next/link";

import FacebookIcon from "@mui/icons-material/Facebook";
import * as React from "react";





export default function Footer() {

  // Get locale and translations
  const locale = useLocale();

  // Field names
  const t_map = {
    "en": "description_en",
    "lt": "description",
  };

  // Fetch sections
  const [sections, setSections] = useState([]);
  useEffect(() => {
    fetch('/flask/api/main_page_sections/')
      .then((response) => response.json())
      .then((data) => setSections(data));
  }, []);



  return (
    <footer>
      <Divider />

      <Container>

        {/* Text section */}
        <Box sx={{ p: 4 }}>
          {sections.map((section) => (
            <div key={section.id}>
              { section.name === "Footer" &&
                <Typography dangerouslySetInnerHTML={{ __html: section[t_map[locale]] }}></Typography>
              }
            </div>
          ))}
        </Box>

        {/* Links section */}
        <Grid container spacing={{ lg: 4, sm: 1 }} className="flex flex-col justify-center">
          <Grid item xs={12} sm={4}>
            <Link href={"https://www.knf.vu.lt"} passHref>
              <MenuItem>
                <Box className="flex flex-col justify-center">
                  <Image src={"/knf-color_w220.png"} alt="Vilniaus universiteto Kauno fakultetas" width={220} height={94} />
                </Box>
              </MenuItem>
            </Link>
          </Grid>

          <Grid item xs={12} sm={4}>
            <Link href={"https://www.lmt.lt"} passHref>
              <MenuItem>
                <Box className="flex justify-center p-2.5">
                  <Image src={"/lmt_w160.png"} alt="Lietuvos mokslo taryba" width={162} height={72} />
                </Box>
              </MenuItem>
            </Link>
          </Grid>

          <Grid item xs={12} sm={4}>
            <Link href={"https://www.facebook.com/skaitmeninehumanitarika"} passHref>
              <MenuItem>
                <Box className="flex justify-center p-2.5">
                  <FacebookIcon className="mr-2" style={{ fontSize: 64 }} />
                  Skaitmeninė <br /> humanitarika <br /> ir kultūra
                </Box>
              </MenuItem>
            </Link>
          </Grid>
        </Grid>

      </Container>
    </footer>
  );
}