import Dashboard from "./components/Dashboard.js";
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import AddNewPatient from './components/AddNewPatient.js';
import AddAnalysis from "./components/AddAnalysis.js";
import PatientDashboard from './components/PatientDashboard';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/add-patient" element={<AddNewPatient/>} />
        <Route path="/add-analysis" element={<AddAnalysis/>}/>
        <Route path="/patient/:patientId" element={<PatientDashboard/>} />
      </Routes>
    </Router>
  );
}

export default App;