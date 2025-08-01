'use client';
import { DataGrid, QuickFilter, QuickFilterControl, QuickFilterClear } from "@mui/x-data-grid";
import React, { useState, useEffect } from "react";
import axios from "axios";
import { Box, Button, LinearProgress, Paper, TextField, InputAdornment } from '@mui/material';
import AddCircleOutlinedIcon from '@mui/icons-material/AddCircleOutlined';

import AddEditAdministrator from "./AddEditAdministrator/AddEditAdministrator";

import CancelIcon from '@mui/icons-material/Cancel';
import SearchIcon from '@mui/icons-material/Search';


function QuickSearchToolbar({ triggerAddNew }) {
  return (
    <Box sx={{ margin: 1, display: 'flex', flexDirection: 'row' }}>
      <QuickFilter>
        <QuickFilterControl 
          render={({ ref, ...other }) => (
            <TextField
              {...other}
              sx={{ width: 260 }}
              inputRef={ref}
              size="small"
              aria-label="Search"
              placeholder="Search..."
              slotProps={{
                input: {
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon fontSize="small" />
                    </InputAdornment>
                  ),
                  endAdornment: other.value ? (
                    <InputAdornment position="end">
                      <QuickFilterClear
                        edge="end"
                        size="small"
                        aria-label="Clear search"
                        material={{ sx: { marginRight: -0.75 } }}
                      >
                        <CancelIcon fontSize="small" />
                      </QuickFilterClear>
                    </InputAdornment>
                  ) : null,
                  ...other.slotProps?.input,
                },
                ...other.slotProps,
              }}
            />
          )}
        />
      </QuickFilter>

      <Button 
        variant="contained"
        sx={{
          marginLeft: '10px',
          paddingLeft: '15px',
          paddingRight: '10px',
          fontSize: '14px',
          height: 40,
          backgroundColor: 'rgb(123,0,63)',
          color: 'white',
        }}
        onClick={() => { triggerAddNew() }}
      >
        <AddCircleOutlinedIcon style={{paddingRight: 8, fontSize: '28px'}}/>
        Add new
      </Button>
      
    </Box>
  );
}



const AdministratorsTable = () => {
  const [loadingData, setLoadingData] = useState(true);
  const [data, setData] = useState([]);
  const [openBackdrop, setOpenBackdrop] = useState(false);


  const AdministratorsTable_Columns = [
    {
      field: "id",
      headerName: "ID",
      width: 70
    },
    {
      field: "email",
      headerName: "Email",
      width: 350,
    },
    {
      field: "enabled",
      headerName: "Enabled",
      width: 100,

      renderCell: (params) => {
        function selectColor(statusID){
          if(statusID === 0){        // Turned OFF
            return 'grey';
          }
          else if(statusID === 1){   // Turned ON
            return 'green';
          }
        }
  
        function selectText(statusID){
          if(statusID === 0){        // Turned OFF
            return 'Disabled';
          }
          else if(statusID === 1){   // Turned ON
            return 'Enabled';
          }
        }
  

        return (
          <div style={{backgroundColor: selectColor(params.row.enabled), borderRadius: 9, width: 80, textAlign: 'center'}}>
            {selectText(params.row.enabled)}
          </div>
        );
      },
    },
    {
      field: "lastseen",
      headerName: "Last seen",
      width: 220,
    },
  ];







  async function getData() {
    try {
      const response = await axios.get("/api/admin/administrators", { withCredentials: true });
      setData(response.data);
      setLoadingData(false);
    } catch (error) {
      if (error.response.status === 401) {
        window.location.href = '/login';
      }
    }
  }



  useEffect(() => {
    getData();
  }, [openBackdrop]);




  // Edit or Add line
  const [userLineData, setUserLineData] = React.useState();

  const handleRowClick = (params) => {
    let modifiedParams = { ...params };
    setUserLineData(modifiedParams);
    setOpenBackdrop(true);
  };

  const triggerAddNew = () => {
    setUserLineData(undefined);
    setOpenBackdrop(true);
  }



  return (
    <Paper className="w-full overflow-hidden" sx={{ paddingRight: 4, borderRadius: 0 }}>
      <Box sx={{ fontSize: '24px', color: 'gray', margin: 2, width: '100%' }}>
        Administrators List
        <DataGrid
          sx={{ height: 'calc(100vh - 185px)', cursor:'pointer',  backgroundColor: 'background.paper'}}
          rows={data}
          columns={AdministratorsTable_Columns}
          pageSize={100}
          rowsPerPageOptions={[100]}
          rowHeight={30}
          onRowClick={handleRowClick}

          initialState={{
            columns: {
              columnVisibilityModel: {
              },
            },
          }}

          loading={loadingData}

          slots={{
            toolbar: QuickSearchToolbar,
            LoadingOverlay: LinearProgress,
          }}
          slotProps={{
            toolbar: {
              triggerAddNew: triggerAddNew
            }
          }}
          showToolbar
        />
      </Box>
      {openBackdrop? 
        <AddEditAdministrator 
          rowData={userLineData}
          setOpen={setOpenBackdrop} 
          getData={getData}
        /> 
      :
        <></> 
      }
    </Paper>
  );
};

export default AdministratorsTable;
