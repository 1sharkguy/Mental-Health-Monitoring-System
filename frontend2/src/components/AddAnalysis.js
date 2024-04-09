import React, { useState } from 'react';
import {useLocation} from 'react-router-dom';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';
import "./AddAnalysis.css"
import CircularProgress from '@mui/material/CircularProgress';

function AddAnalysis() {
  const [loading, setLoading] = useState(false);
  const [audioFile, setAudioFile] = useState(null); 
  const handleFileChange = (event) => {
    // Access the selected file from the input event
    const file = event.target.files[0];
    // Set the state to hold the selected file
    setAudioFile(file);
  };
  const location = useLocation();
  const { patientId, patientAge, patientName } = location.state;

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (!patientId || !patientAge || !patientName || !audioFile) {
        throw new Error('Patient data or audio file is missing.');
      }
      
      setLoading(true);
      const formData = new FormData();
      formData.append('file', audioFile);
      
      const xhr = new XMLHttpRequest();
      xhr.open('POST', process.env.REACT_APP_URL_PREDICT, true);
      
      xhr.onload = function() {
        if (xhr.status === 200) {
          // Success callback
          const responseData = JSON.parse(xhr.responseText);
          // Handle the response as needed
          console.log(responseData);
          localStorage.setItem('analysisResult', JSON.stringify(responseData));
          // Redirect to the home page
          window.location.href = `/patient/${patientId}`;
        } else {
          // Error callback
          console.error('Error adding analysis:', xhr.statusText);
          setLoading(false); 
        }
      };
      
      xhr.onerror = function() {
        console.error('Error adding analysis:', xhr.statusText);
        setLoading(false); 
      };
    
      xhr.send(formData);
    } catch (error) {
      console.error('Error adding analysis:', error);
    }
  }
    
  
  
  return (
    <div className='container'>
      <div className="titleflex">
          <h1 style={{ flex: '1' }}>Welcome to Dashboard</h1>
      </div>
      <Box className='yoyo' sx={{alignItems: 'center'}}>
        <div className='all'>
          <form onSubmit={handleSubmit}>
            <label htmlFor="audioFileInput" className="fileInputLabel" >
              Choose Audio File
            </label>
            <input 
              id="audioFileInput"
              type="file" 
              accept="audio/*" 
              onChange={handleFileChange} 
              className="fileInput"
            />
            {/* Render the selected file name */}
            {audioFile && <p>Selected Audio: {audioFile.name}</p>}
            {/* You can also render an audio player to play the selected audio */}
            {audioFile && (
              <audio controls className="audioPlayer">
                <source src={URL.createObjectURL(audioFile)} type="audio/*" />
              </audio>
            )}
            <Button type="submit" variant="contained" sx={{ marginTop: '20px'}}>
              Add Analysis
            </Button>
            {loading && <CircularProgress size={24} sx={{ marginTop: '20px' }} />}
          </form>
        </div>
      </Box>
    </div>
  );
}

export default AddAnalysis;
