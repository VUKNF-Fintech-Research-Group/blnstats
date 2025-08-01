import React, { useState, useEffect } from "react";
import axios from "axios";

import { TextField, Box, FormControl, Grid, MenuItem, Button, Modal, Stack, Typography  } from "@mui/material";

import CancelIcon from '@mui/icons-material/Cancel';
import toast from 'react-hot-toast';

export default function AddEditAdministrator({ rowData, highestRowID, setOpen, getData }) {
  const [data, setData] = useState(undefined);
  const [changePassword, setChangePassword] = useState(false);

  

  useEffect(() => {
    if (rowData !== undefined) {
      // Editing an existing user: start with no password change
      setData({
        id: rowData.row.id,
        email: rowData.row.email,
        enabled: rowData.row.enabled,
        password: '',
        confirmPassword: '',
        admin: 1,
      });
      setChangePassword(false);
    } else {
      // Creating a new user: password fields always required
      setData({
        id: '',
        email: '',
        enabled: 1,
        password: '',
        confirmPassword: '',
        admin: 1,
      });
      setChangePassword(true);
    }
  }, [rowData]);



  async function sendData(postData) {
    const response = await axios.post("/api/admin/administrators", postData, { withCredentials: true });

    if (response.data.type === 'ok') {
      toast.success(<b>Saved</b>, { duration: 3000 });
    } else if (response.data.type === 'error') {
      toast.error(<b>Failed:<br/>{response.data.reason}</b>, { duration: 8000 });
    } else {
      toast.error(<b>Failed:<br/>Unknown response.</b>, { duration: 8000 });
    }
    getData();
    setOpen(false);
  }

  function handleSaveButton() {
    const postData = {
      action: 'insertupdate',
      id: data.id,
      email: data.email,
      enabled: data.enabled,
      password: data.password,
      admin: 1,
    };
    sendData(postData);
  }

  async function handleDeleteButton() {
    const postData = {
      action: 'delete',
      id: data.id
    };
    sendData(postData);
  }

  if (data === undefined) {
    return null;
  }

  const passwordsMatch = data.password === data.confirmPassword;
  
  // Determine conditions for disabling Save button
  // If inserting a new user or changing password on edit: require matching non-empty passwords.
  // If editing without changing password: passwords can be empty and it's allowed to save.
  const disableSave = 
    (changePassword && (!passwordsMatch || data.password === '' || data.confirmPassword === '')) ||
    (data.email.trim() === '');



  return (
    <Modal
      open={true}
      onClose={() => setOpen(false)}
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <Box sx={{ width: '500px', borderRadius: 2, boxShadow: 3, backgroundColor: 'white', p: 4 }}>
        <Box className="mb-5">
          <div className="flex justify-between items-start">
            <Typography component="h2" fontSize="1.25em" mb="0.25em" className="mb-[30px]">
              Administrator
            </Typography>

            <Button
              onClick={() => setOpen(false)}
              className="p-0 rounded-full bg-transparent outline-transparent ml-auto"
              style={{ color: 'white', backgroundColor: 'white' }}
            >
              <CancelIcon className="text-red-500" />
            </Button>
          </div>
        </Box>

        <Stack spacing={3}>
          <FormControl size="lg" color="primary">
            <TextField
              disabled
              sx={{ backgroundColor: "lightgrey" }}
              label="ID"
              value={data.id}
            />
          </FormControl>

          <FormControl size="lg" color="primary">
            <TextField
              type="email"
              required
              label="Email"
              value={data.email}
              onChange={(e) => setData(prevData => ({ ...prevData, email: e.target.value }))}
            />
          </FormControl>

          <FormControl size="lg" color="primary">
            <TextField
              select
              label="Enabled"
              value={data.enabled}
              onChange={(e) => setData(prevData => ({ ...prevData, enabled: e.target.value }))}
            >
              <MenuItem value={1}>Yes</MenuItem>
              <MenuItem value={0}>No</MenuItem>
            </TextField>
          </FormControl>

          {rowData !== undefined && !changePassword && (
            <Box>
              <Button
                variant="outlined"
                onClick={() => setChangePassword(true)}
                className="w-full text-black mb-[10px]"
              >
                Change Password
              </Button>
            </Box>
          )}

          {(changePassword || rowData === undefined) && (
            <>
              <FormControl size="lg" color="primary">
                <TextField
                  type="password"
                  label="Password"
                  value={data.password}
                  onChange={(e) => setData(prevData => ({ ...prevData, password: e.target.value }))}
                />
              </FormControl>

              <FormControl size="lg" color="primary">
                <TextField
                  type="password"
                  label="Confirm Password"
                  value={data.confirmPassword}
                  error={!passwordsMatch && data.confirmPassword !== ''}
                  helperText={!passwordsMatch && data.confirmPassword !== '' ? 'Passwords do not match' : ''}
                  onChange={(e) => setData(prevData => ({ ...prevData, confirmPassword: e.target.value }))}
                />
              </FormControl>
            </>
          )}

          <div className="mt-[100px]"></div>

          <Box>
            <div className="flex gap-2">
              <Button
                type="submit"
                className={`flex-1 text-white shadow-[0px_8px_15px_rgba(0,0,0,0.1)] ${
                  disableSave ? 'bg-gray-900' : 'bg-[rgb(123,0,63)]'
                }`}
                sx={{
                  backgroundColor: disableSave ? 'gray' : 'rgb(123,0,63)',
                  color: 'white',
                  '&:hover': {
                    backgroundColor: disableSave ? 'gray' : 'rgb(123,0,63)'
                  }
                }}
                onClick={() => handleSaveButton()}
                disabled={disableSave}
              >
                {rowData !== undefined ? 'Save' : 'Insert'}
              </Button>

              {rowData !== undefined && (
                <Button
                  className="flex-1 bg-red-500 text-white shadow-[0px_8px_15px_rgba(0,0,0,0.1)]"
                  onClick={() => handleDeleteButton()}
                  sx={{
                    backgroundColor: 'blue',
                    color: 'white',
                    '&:hover': {
                      backgroundColor: 'blue',
                    }
                  }}
                >
                  Delete Record
                </Button>
              )}
            </div>
          </Box>
        </Stack>
      </Box>
    </Modal>
  );
}
