import axios from 'axios';

// Function to fetch patients from the backend API
const fetchPatients = async () => {
  try {
    // Make a GET request to the /getpatients endpoint of your backend API
    const response = await axios.get("http://localhost:8000/getpatients");

    // Extract the patient data from the response
    const patients = response.data;

    // Return the array of patients
    return patients;
  } catch (error) {
    // Handle any errors that occur during the request
    console.error('Error fetching patients:', error);
    return []; // Return an empty array in case of error
  }
};

export default fetchPatients;
