import { ThermometerIcon, ActivityIcon, CalendarIcon, DropletsIcon, HeartIcon, Wind } from "lucide-react";
import { DocumentPlusIcon, DocumentIcon, DocumentTextIcon } from "@heroicons/react/24/outline";
import { useState, useEffect } from "react";
import { Outlet, useParams } from "react-router-dom";
import usePatients from "../hooks/usePatients.jsx";
import useVitals from "../hooks/useVitals.jsx";
import useNotes from "../hooks/useNotes.jsx";
import useAppointments from "../hooks/useAppointments.jsx";
import BasicPatientInfo from "../components/BasicPatientInfo";
import PatientsVitalsCard from "../components/PatientsVitalsCard";
import ActionCards from "../components/ActionCards";
import IndividualNavLink from "../components/IndividualNavLink";
import { PatientDetailContext } from "../context/PatientsDetailContext";
import PersonalizedQuickActions from "../components/PersonalizedQuickActions.jsx";
import AddNoteForm from "../components/AddNoteForm.jsx";
import AppointmentForm from "../components/AppointmentForm.jsx";
import RecordVitalsForm from "../components/RecordVitalsForm.jsx";
import PatientTimeline from "./PatientTimeline.jsx";
import { computeDeltas } from "../utils/deltaEngine.js";

export default function PateintDetail() {

    const { patientsArray } = usePatients();
    const { vitalsArray, setVitalsArray } = useVitals();
    const { notesArray, setNotesArray } = useNotes();
    const { appointmentsList, setAppointmentsList } = useAppointments();
    const [isNoteFormOpen, setIsNoteFormOpen] = useState(false);
    const [isAppointmentFormOpen, setIsAppointmentFormOpen] = useState(false);
    const [isVitalFormOpen, setIsVitalFormOpen] = useState(false);


    // useParams is how a page reads info from the URL
    const { patientsId } = useParams(); //this grabs <patient.id> from the URL    

    //.find returns a single patient
    const patient = patientsArray.find(patient => patient.id === patientsId);

    //Get their vitals and notes too
    //.filter returns multiple vitals
    const patientVitals = vitalsArray.filter(vital => vital.patientId === patientsId);
    const patientNotes = notesArray.filter(note => note.patientId === patientsId);
    const patientCompleteDetail = {
        ...patient,
        vitals: patientVitals,
        notes: patientNotes
    };

    const latestVital = patientCompleteDetail.vitals.length > 0
        ? patientCompleteDetail.vitals.reduce((latest, current) =>
            new Date(current.timestamp) > new Date(latest.timestamp)
                ? current : latest)
        : null;


    const deltas = computeDeltas(patientVitals);

    return (
        <>
            {isAppointmentFormOpen && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-xs z-50 flex items-center justify-center p-4">
                    <AppointmentForm
                        setAppointmentsList={setAppointmentsList}
                        setIsFormOpen={setIsAppointmentFormOpen}
                        defaultPatientId={patientsId}
                    />
                </div>
            )}
            {isNoteFormOpen && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-xs z-50 flex items-center justify-center p-4">
                    <AddNoteForm
                        setNotesArray={setNotesArray}
                        setIsNoteFormOpen={setIsNoteFormOpen}
                        patientId={patientsId}
                    />
                </div>
            )}
            {isVitalFormOpen && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-xs z-50 flex items-center justify-center p-4">
                    <RecordVitalsForm
                        setVitalsArray={setVitalsArray}
                        setIsVitalFormOpen={setIsVitalFormOpen}
                        patientId={patientsId}
                    />
                </div>
            )}
            <main className="p-5">
                <div className=" flex flex-col mb-5">
                    {/*Basic Patient Information*/}
                    <div className="flex flex-col my-5">
                        <BasicPatientInfo
                            name={patientCompleteDetail.name}
                            age={patientCompleteDetail.age}
                            id={patientCompleteDetail.id}
                            gender={patientCompleteDetail.gender}
                            weight={patientCompleteDetail.weight || "N/A"}
                            room={patientCompleteDetail.room}
                            condition={patientCompleteDetail.condition}
                            admitted={patientCompleteDetail.admitted}
                        />
                    </div>
                    {/*Quick Action Cards*/}
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                        <button onClick={() => { setIsVitalFormOpen(true) }}>
                            <PersonalizedQuickActions
                                icon={DocumentPlusIcon}
                                quickActionTitle="Record Vitals" />
                        </button>


                        {/*Appointment button*/}
                        <button onClick={() => { setIsAppointmentFormOpen(true) }}>
                            <PersonalizedQuickActions
                                icon={CalendarIcon}
                                quickActionTitle="+ Appointment" />
                        </button>

                        {/*Add Note button*/}
                        <button onClick={() => { setIsNoteFormOpen(true) }}>
                            <PersonalizedQuickActions
                                icon={DocumentIcon}
                                quickActionTitle="Add Note"
                            />
                        </button>


                        <button>
                            <PersonalizedQuickActions
                                icon={DocumentTextIcon}
                                quickActionTitle="Generate Report" />
                        </button>

                    </div>
                </div>

                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-10">

                    {/*Heart Rate*/}
                    <PatientsVitalsCard
                        icon={HeartIcon}
                        iconColor={"bg-red-100"}
                        iconTextColor={"text-red-600"}
                        vitalName="Heart Rate"
                        vital="heartRate"
                        vitalRate={latestVital?.heartRate}
                        unit="BPM"
                        delta={deltas && (deltas.find(delta => delta.vital === "heartRate"))}
                    />

                    {/*Blood Pressure*/}
                    <PatientsVitalsCard
                        icon={ActivityIcon}
                        iconColor={"bg-amber-100"}
                        iconTextColor={"text-amber-600"}
                        vitalName="Blood Pressure"
                        vital="bloodPressure"
                        vitalRate={latestVital?.bloodPressure ?
                            `${latestVital.bloodPressure.systolic} /
                             ${latestVital.bloodPressure.diastolic}`
                            : "--"}
                        unit="mmHg"
                        delta={deltas && (deltas.find(delta => delta.vital === "bloodPressure"))}
                    />

                    {/*Temperature*/}
                    <PatientsVitalsCard
                        icon={ThermometerIcon}
                        iconColor={"bg-green-100"}
                        iconTextColor={"text-green-600"}
                        vitalName="Temperature"
                        vital="temperature"
                        vitalRate={latestVital?.temperature}
                        unit="°C"
                        delta={deltas && (deltas.find(delta => delta.vital === "temperature"))}
                    />

                    {/*Blood Oxygen*/}
                    <PatientsVitalsCard
                        icon={DropletsIcon}
                        iconColor={"bg-blue-100"}
                        iconTextColor={"text-blue-600"}
                        vitalName="Blood Oxygen"
                        vital="oxygen"
                        vitalRate={latestVital?.oxygen}
                        unit="%"
                        delta={deltas && (deltas.find(delta => delta.vital === "oxygen"))}
                    />

                </div>

                {/*Action Cards*/}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
                    <ActionCards
                        action="View History"
                        actionInfo="Access past vital signs records" />

                    {/*AI Health Summary Card*/}
                    <ActionCards
                        action="AI Health Summary"
                        actionInfo="Get AI-powered insights and trends from patient data" />
                </div>

                {/*NAV LINKS*/}
                <nav className="bg-gray-200 flex flex-row flex-wrap sm:flex-nowrap w-full max-w-md gap-2 px-2 py-2 mb-7 font-semibold text-gray-500 rounded-xl">
                    <IndividualNavLink to="overview" name="Overview" />
                    <IndividualNavLink to="appointments" name="Appointments" />
                    <IndividualNavLink to="notes" name="Notes" patientNotes={patientNotes} />
                    <IndividualNavLink to="timeline" name="Timeline" />
                </nav>

                <div >
                    <PatientDetailContext.Provider value={{ patient, latestVital, patientNotes, patientVitals, setNotesArray, appointmentsList, setAppointmentsList }} >
                        {/*So everything in here can now access the data*/}
                        <Outlet />
                    </PatientDetailContext.Provider>
                </div>

            </main>
        </>

    )
}