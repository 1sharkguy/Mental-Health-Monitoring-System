import React, { useState, useEffect } from "react";
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import BottomNavigation from '@mui/material/BottomNavigation';
import BottomNavigationAction from '@mui/material/BottomNavigationAction';
import ButtonGroup from '@mui/material/ButtonGroup';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { PieChart, Pie, Tooltip } from 'recharts';
import fetchPatients from './FetchPatients';

function PatientDashboard() {
    const { patientId } = useParams();
    const navigate = useNavigate();
    const [searchTerm, setSearchTerm] = useState('');
    const [patients, setPatients] = useState([]);
    const [analysisResults, setAnalysisResults] = useState([]);
    const [selectedAnalysis, setSelectedAnalysis] = useState(null);
    const [selectedPatient, setSelectedPatient] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const data = await fetchPatients();
                setPatients(data);
            } catch (error) {
                console.error('Error fetching patients:', error);
            }
        };

        fetchData();
    }, []);

    useEffect(() => {
        if (selectedPatient) {
            fetchAnalysisData();
        }
    }, [selectedPatient]);

    const fetchAnalysisData = async () => {
        try {
            const response = await axios.get(`https://mental-health-monitoring-system.onrender.com/getanalysis/${selectedPatient.id}`);
            if (response.status === 200) {
                setAnalysisResults(response.data);
            } else {
                console.error('Error fetching analysis data:', response.statusText);
            }
        } catch (error) {
            console.error('Error fetching analysis data:', error);
        }
    };

    const filteredOptions = patients.filter(patient =>
        patient.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        patient.id.toString().includes(searchTerm.toLowerCase())
    );

    const handlePatientClick = async (patient) => {
        setSelectedPatient(patient);
        setAnalysisResults([]);
        setSelectedAnalysis(null);
        navigate(`/patient/${patient.id}`);
    };

    const handleAddAnalysis = () => {
        if (selectedPatient) {
            navigate('/add-analysis', {
                state: {
                    patientId: selectedPatient.id,
                    patientAge: selectedPatient.age,
                    patientName: selectedPatient.name
                }
            });
        }
    };

    const handleRemoveAnalysis = async () => {
        try {
            if (selectedAnalysis) {
                const response = await axios.get(`https://mental-health-monitoring-system.onrender.com/deleteanalysis/${selectedAnalysis.id}`);
                if (response.status === 200) {
                    console.log('Analysis deleted successfully');
                    setAnalysisResults(prevResults => prevResults.filter(result => result.id !== selectedAnalysis.id));
                    setSelectedAnalysis(null);
                } else {
                    console.error('Error deleting analysis:', response.statusText);
                }
            }
        } catch (error) {
            console.error('Error deleting analysis:', error);
        }
    };

    const handleAddNewPatient = () => {
        navigate('/add-patient');
    };

    const handleDeletePatient = async () => {
        try {
            if (selectedPatient) {
                const url = `https://mental-health-monitoring-system.onrender.com/deletepatient/${selectedPatient.id}`;
                const response = await axios.get(url);

                if (response.status === 200) {
                    console.log('Patient and associated analysis deleted successfully');
                    navigate('/');
                } else {
                    console.error('Error deleting patient:', response.statusText);
                }
            }
        } catch (error) {
            console.error('Error deleting patient:', error);
        }
    };

    return (
        <div>
            <div className="titleflex">
                <h1 style={{ flex: '1' }}>Patient Dashboard</h1>
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
                                        },
                                        '&.selected': {
                                            color: 'blue'
                                        }
                                    }}
                                    className={patient.id === parseInt(patientId) ? 'selected' : ''}
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
                        {selectedPatient && (
                            <Button variant="contained" color="error" onClick={handleDeletePatient}>
                                Delete Patient
                            </Button>
                        )}
                    </Box>
                </Box>
                <Box className="analysis" sx={{ width: '75%' }}>
                    <div style={{ display: 'flex', alignItems: 'center' }}>
                        <h3 style={{ marginTop: '0', marginRight: 'auto' }}>Analysis</h3>
                        {selectedPatient && (
                            <>
                                <div style={{ textAlign: 'center', marginTop: '0' }}>
                                    <p style={{ marginTop: '0' }}>
                                        <span style={{ fontWeight: 'bold' }}>ID:</span> {selectedPatient.id} &nbsp;
                                        <span style={{ fontWeight: 'bold' }}>Name:</span> {selectedPatient.name} &nbsp;
                                        <span style={{ fontWeight: 'bold' }}>Age:</span> {selectedPatient.age}
                                    </p>
                                </div>
                                <Box sx={{ display: 'flex', marginTop: '0', marginLeft: 'auto' }}>
                                    <Button variant="contained" onClick={handleAddAnalysis}>Add New Analysis</Button>
                                    {selectedAnalysis && <Button variant="contained" color="error" sx={{ marginLeft: '10px' }} onClick={handleRemoveAnalysis}>Remove Analysis</Button>}
                                </Box>
                                <BottomNavigation
                                    showLabels
                                    value={selectedAnalysis ? analysisResults.findIndex(result => result.id === selectedAnalysis.id) : -1}
                                    onChange={(event, newValue) => {
                                        setSelectedAnalysis(analysisResults[newValue]);
                                    }}
                                    sx={{
                                        position:'absolute',
                                        marginTop: '150px'
                                    }}
                                >
                                    {analysisResults.map((result, index) => (
                                        <BottomNavigationAction key={result.id} label={`Analysis ${index + 1}`} />
                                    ))}
                                </BottomNavigation>

                                {selectedAnalysis && (
                                    <div style={{ marginTop: '600px', position: 'absolute', display: 'flex'}}>
                                        <div>
                                            <h3>Selected Analysis Details</h3>
                                            <p>Timestamp: {new Date(selectedAnalysis.timestamp).toLocaleString()}</p>
                                            <p>Analysis ID: {selectedAnalysis.id}</p>
                                        </div>
                                        <div style={{ display: 'flex', alignItems: 'center' }}>
                                            <div style={{ width: 400, height: 400 }}>
                                                <PieChart width={400} height={400}>
                                                    <Pie
                                                        dataKey="value"
                                                        data={selectedAnalysis.emotion_percentages.map((percentage, index) => ({
                                                            name: selectedAnalysis.emotions[index],
                                                            value: percentage,
                                                            fill: `hsl(${index * 360 / selectedAnalysis.emotions.length}, 70%, 50%)`, // Colorful sections
                                                        }))}
                                                        cx="50%"
                                                        cy="50%"
                                                        outerRadius={80}
                                                        fill="#8884d8"
                                                        label
                                                    />
                                                    <Tooltip />
                                                </PieChart>
                                            </div>
                                            <div style={{ marginLeft: 20 }}>
                                                {selectedAnalysis.emotions.map((emotion, index) => (
                                                    <div key={index} style={{ display: 'flex', alignItems: 'center', marginBottom: 5 }}>
                                                        <div
                                                            style={{
                                                                width: 10,
                                                                height: 10,
                                                                borderRadius: '50%',
                                                                backgroundColor: `hsl(${index * 360 / selectedAnalysis.emotions.length}, 70%, 50%)`,
                                                                marginRight: 5,
                                                            }}
                                                        ></div>
                                                        <p style={{ margin: 0 }}>{emotion}</p>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                </Box>
            </div>
        </div>
    );
}

export default PatientDashboard;
