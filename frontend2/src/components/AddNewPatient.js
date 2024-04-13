import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import "./AddNewPatient.css"

function AddNewPatient() {
  const [patientData, setPatientData] = useState({
    name: '',
    age: '',
  });

  const navigate = useNavigate();

  const handleChange = (e) => {
    setPatientData({ ...patientData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!patientData.name || !patientData.age) {
      alert('Please fill in all fields');
      return;
    }
    try {
      await axios.post("https://mental-health-monitoring-system.onrender.com/addnewpatient", patientData);
      navigate('/'); // Redirect to the dashboard after adding the patient
    } catch (error) {
      console.error('Error adding patient:', error);
    }
  };

  return (
    <div className="container">
      <div className="titleflex">
            <h1 style={{ flex: '1' }}>Welcome to Dashboard</h1>
      </div>
      <Box className="yoyo">
        <h2>Add New Patient</h2>
        <form onSubmit={handleSubmit}>
          <TextField
            label="Name"
            name="name"
            value={patientData.name}
            onChange={handleChange}
            variant="outlined"
            fullWidth
            margin="normal"
          />
          <TextField
            label="Age"
            name="age"
            value={patientData.age}
            onChange={handleChange}
            variant="outlined"
            fullWidth
            margin="normal"
          />
          <Button type="submit" variant="contained" sx={{ marginTop: '20px'}}>
            Add Patient
          </Button>
        </form>
      </Box>
    </div>
  );
}

export default AddNewPatient;
