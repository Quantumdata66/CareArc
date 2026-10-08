import { useState } from "react";
import InputComponent from "../components/InputComponent";
import { useNavigate } from "react-router-dom";
import Toast from "../components/Toast";
import usePatients from "../hooks/usePatients";
import useVitals from "../hooks/useVitals";

export default function AddPatientPage() {

    const { patientsArray, setPatientsArray } = usePatients();
    const { setVitalsArray } = useVitals();


    const generatePatientId = (patientsArray) => {
        if (!patientsArray || patientsArray.length === 0) return "PT-001";

        const numbers = patientsArray
            .map(patient => {
                if (!patient?.id) return 0;
                const match = String(patient.id).match(/\d+/);
                return match ? parseInt(match[0], 10) : 0;
            })
            .filter(n => !isNaN(n) && n > 0);

        const maxNumber = numbers.length > 0 ? Math.max(...numbers) : 0;
        let nextDigit = maxNumber + 1;
        let nextId = `PT-${String(nextDigit).padStart(3, "0")}`;

        const existingIds = new Set(patientsArray.map(p => p.id));
        while (existingIds.has(nextId)) {
            nextDigit++;
            nextId = `PT-${String(nextDigit).padStart(3, "0")}`;
        }

        return nextId;
    };

    const navigate = useNavigate();
    const [showToast, setShowToast] = useState(false);
    const [formData, setFormData] = useState({
        name: "",
        age: "",
        gender: "",
        weight: "",
        room: "",
        condition: "",
        status: "",
        admitted: "",
        heartRate: "",
        systolic: "",
        diastolic: "",
        oxygen: "",
        temperature: "",
        respiratoryRate: ""
    });


    return (
        <div>
            {showToast && <Toast statement="Patient Added Successfully!" />}

            <form className="w-3/4 mx-auto flex flex-col m-5 px-7 py-3 bg-white rounded-xl"
                onSubmit={(e) => {

                    e.preventDefault();

                    //creating a new ID
                    const newId = generatePatientId(patientsArray);


                    //Splitting the data extracted now 

                    const newPatientData = {
                        id: newId,
                        name: formData.name,
                        age: formData.age,
                        gender: formData.gender,
                        weight: formData.weight,
                        room: formData.room,
                        condition: formData.condition,
                        status: formData.status,
                        admitted: formData.admitted,
                    }

                    const newVitals = {
                        patientId: newPatientData.id,
                        heartRate: formData.heartRate,
                        bloodPressure: { systolic: formData.systolic, diastolic: formData.diastolic },
                        oxygen: formData.oxygen,
                        temperature: formData.temperature,
                        respiratoryRate: formData.respiratoryRate,
                        timestamp: new Date().toISOString()
                    }


                    setVitalsArray(prev => [...prev, newVitals])
                    setPatientsArray(prev => [...prev, newPatientData])

                    setFormData({
                        name: "",
                        age: "",
                        gender: "",
                        weight: "",
                        room: "",
                        condition: "",
                        status: "",
                        admitted: "",
                        heartRate: "",
                        systolic: "",
                        diastolic: "",
                        oxygen: "",
                        temperature: "",
                        respiratoryRate: ""
                    });

                    setShowToast(true);
                    setTimeout(() =>
                        navigate("/dashboard/patients"), 800)
                    //returning to previous page and resetting the details
                }} >

                <div className="">
                    <h2 className="flex justify-center font-bold text-2xl my-5">Add New Patient</h2>

                    {/*Basic Information*/}
                    <section>
                        <h3 className="flex justify-center font-semibold text-2xl mt-5">Basic Information</h3>
                        {/*Full Name*/}
                        <InputComponent label="Full Name" type="text" placeholder="John Mary" value={formData.name} onChange={(e) => {
                            setFormData({ ...formData, name: e.target.value })
                        }} />

                        {/*Age*/}
                        <InputComponent label="Age" type="text" placeholder="45" value={formData.age} onChange={(e) => {
                            setFormData({ ...formData, age: e.target.value })
                        }} />

                        {/*Gender*/}
                        <InputComponent label="Gender" type="text" placeholder="Female" value={formData.gender} onChange={(e) => {
                            setFormData({ ...formData, gender: e.target.value })
                        }} />

                        {/*Weight*/}
                        <InputComponent label="Weight" type="text" placeholder="245lbs" value={formData.weight} onChange={(e) => {
                            setFormData({ ...formData, weight: e.target.value })
                        }} />
                    </section>


                    {/*Clinical Infp*/}
                    <section>
                        <h3 className="flex justify-center font-semibold text-2xl mt-5">Clinical Info</h3>

                        {/*Room*/}
                        <InputComponent label="Room" type="text" placeholder="ICU101" value={formData.room} onChange={(e) => {
                            setFormData({ ...formData, room: e.target.value })
                        }} />

                        {/*Primary Condition*/}
                        <InputComponent label="Primary Condition" type="text" placeholder="Tuberculosis" value={formData.condition} onChange={(e) => {
                            setFormData({ ...formData, condition: e.target.value })
                        }} />

                        {/*Status*/}
                        <InputComponent label="Status" type="text" placeholder="Critical" value={formData.status} onChange={(e) => {
                            setFormData({ ...formData, status: e.target.value })
                        }} />

                        {/*Admission Date*/}
                        <InputComponent label="Admission Date" type="date" placeholder="" value={formData.admitted} onChange={(e) => {
                            setFormData({ ...formData, admitted: e.target.value })
                        }} />
                    </section>

                    {/*Initial Vitals*/}
                    <section>
                        <h3 className="flex justify-center font-semibold text-2xl mt-5">Initial Vitals</h3>

                        {/*Heart Rate*/}
                        <InputComponent label="Heart Rate" type="text" placeholder="110 BPM" value={formData.heartRate} onChange={(e) => {
                            setFormData({ ...formData, heartRate: e.target.value })
                        }} />

                        {/*Blood Pressure - Systolic*/}
                        <InputComponent label="Systolic BP" type="text" placeholder="135 mmHg" value={formData.systolic} onChange={(e) => {
                            setFormData({ ...formData, systolic: e.target.value })
                        }} />

                        {/*Blood Pressure - Diastolic*/}
                        <InputComponent label="Diastolic BP" type="text" placeholder="90 mmHg" value={formData.diastolic} onChange={(e) => {
                            setFormData({ ...formData, diastolic: e.target.value })
                        }} />

                        {/*Oxygen*/}
                        <InputComponent label="Oxygen" type="text" placeholder="90%" value={formData.oxygen} onChange={(e) => {
                            setFormData({ ...formData, oxygen: e.target.value })
                        }} />

                        {/*Temperature*/}
                        <InputComponent label="Temperature" type="text" placeholder="33.1°C" value={formData.temperature} onChange={(e) => {
                            setFormData({ ...formData, temperature: e.target.value })
                        }} />

                        {/*Respiratory Rate*/}
                        <InputComponent label="Respiratory Rate" type="text" placeholder="20/min" value={formData.respiratoryRate} onChange={(e) => {
                            setFormData({ ...formData, respiratoryRate: e.target.value })
                        }} />
                    </section>
                </div>

                <button type="submit" className="flex justify-center mx-auto w-1/2 bg-blue-700 text-white px-3 py-2 rounded-md mt-3 hover:cursor-pointer hover:scale-105 hover:bg-blue-800">
                    Create Patient
                </button>
            </form>

        </div>

    )
}