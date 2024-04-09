import React, { useState, useEffect } from "react";
import './Dashboard.css';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import ButtonGroup from '@mui/material/ButtonGroup';
import fetchPatients from './FetchPatients';
import { useNavigate } from 'react-router-dom';

function Dashboard() {
    const navigate = useNavigate();
    const [searchTerm, setSearchTerm] = useState('');
    const [patients, setPatients] = useState([]);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const data = await fetchPatients();
                setPatients(data);
            } catch (error) {
                console.error('Error fetching patients:', error);
                // Handle the error, show an error message, etc.
            }
        };

        fetchData();
    }, []);

    const filteredOptions = patients.filter(patient =>
        patient.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        patient.id.toString().includes(searchTerm.toLowerCase())
    );

    const handlePatientClick = async (patient) => {
        navigate(`/patient/${patient.id}`);
    };

    const handleAddNewPatient = () => {
        navigate('/add-patient');
    };

    return (
        <div>
            <div className="titleflex">
                <h1 style={{ flex: '1' }}>Welcome to Dashboard</h1>
            </div>

            <div className="boxes">
                <Box className="patientlist">
                    <h3>Patient's List</h3>
                    <TextField
                        label="Search"
                        variant="outlined"
                        value={searchTerm}
                        sx={{ width: '275px' }}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                    <Box className='searchspace' sx={{ height: 300, width: '80', overflow: 'auto', border: '1px solid #ccc', borderRadius: '4px', marginTop: '16px' }}>
                        <ButtonGroup
                            orientation="vertical"
                            variant="text"
                            sx={{ width: '100%' }}
                        >
                            {filteredOptions.map(patient => (
                                <Button
                                    key={patient.id}
                                    onClick={() => handlePatientClick(patient)}
                                    sx={{
                                        width: '100%',
                                        color: 'black',
                                        '&:hover': {
                                            color: 'blue'
                                        }
                                    }}
                                >
                                    {`${patient.id} - ${patient.name}`}
                                </Button>
                            ))}
                        </ButtonGroup>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', marginTop: '20px' }}>
                        <Button variant="contained" onClick={handleAddNewPatient}>
                            Add New Patient
                        </Button>
                    </Box>
                </Box>
                <Box className="analysis" sx={{ width: '75%' }}>
                    <div style={{ display: 'flex', alignItems: 'center' }}>
                        <h3 style={{ marginTop: '0', marginRight: 'auto' }}>Analysis</h3>
                    </div>
                </Box>
            </div>
        </div>
    );
}

export default Dashboard;