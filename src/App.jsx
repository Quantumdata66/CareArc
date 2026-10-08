import { useState } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import HomePage from "./pages/Home";
import DashboardLayout from "./pages/DashboardLayout";
import Dashboard from "./pages/Dashboard"
import Patients from "./pages/Patients";
import Appointments from "./pages/Appointments";
import Settings from "./pages/Settings";
import Profile from "./pages/Profile";
import System from "./pages/System";
import Notifications from "./pages/Notifications";
import Thresholds from "./pages/Thresholds";
import AddPatientPage from "./pages/AddPatientPage";
import PatientsDetail from "./pages/PatientsDetail.jsx";
import PersonalizedOverview from "./pages/PersonalizedOverview.jsx";
import PersonalizedAppointments from "./pages/PersonalizedAppointments.jsx";
import PersonalizedNotes from "./pages/PersonalizedNotes.jsx";
import PatientTimeline from "./pages/PatientTimeline.jsx";

function App() {

  return (
    <Router> {/* Navigation manager of the whole app */}
      <Routes> {/*Container that holds all the route rules*/}

        {/*Main Pages*/}
        <Route path="/" element={<HomePage />} /> {/*Defines one specific path and the component that should load*/}

        <Route path="/dashboard" element={<DashboardLayout />}>

          {/*DashboardLayout renders sidebar + outlet, hence why all the nested routes live in the parent route*/}
          <Route index element={<Dashboard />} />{/*Default child route, this is what will be shown in outlet by default when dashboard is clicked*/}

          {/*Actual Patients Page*/}
          <Route path="patients" element={<Patients />} />

          {/*Add Patients page*/}
          <Route path="patients/addpatientpage" element={<AddPatientPage />} />

          {/*Patients Details Page*/}
          <Route path="patients/patientsdetail/:patientsId" element={<PatientsDetail />} >
            <Route index element={<Navigate to="overview" replace />} />
            <Route path="overview" element={<PersonalizedOverview />} />
            <Route path="appointments" element={<PersonalizedAppointments />} />
            <Route path="notes" element={<PersonalizedNotes />} />
            <Route path="timeline" element={<PatientTimeline />} />
          </Route>

          {/*React router appends /dashboard automatically because it is nested*/}
          <Route path="appointments" element={<Appointments />} />

          {/*Settings Page with nested routes */}
          <Route path="settings" element={<Settings />}>
            <Route index element={<Profile />} />
            <Route path="profile" element={<Profile />} />
            <Route path="system" element={<System />} />
            <Route path="notifications" element={<Notifications />} />
            <Route path="thresholds" element={<Thresholds />} />
          </Route>

        </Route>
      </Routes>
    </Router>
  )
}

export default App
