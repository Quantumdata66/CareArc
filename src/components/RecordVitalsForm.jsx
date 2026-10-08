import { useState } from "react";
import InputComponent from './InputComponent';


export default function RecordVitalsForm({ setIsVitalFormOpen, setVitalsArray, patientId }) {

    const [formData, setFormData] = useState({
        heartRate: "",
        systolic: "",
        diastolic: "",
        oxygen: "",
        temperature: "",
        respiratoryRate: "",
        recordedBy: ""
    });


    const parseOptionalNumber = (val) => {
        if (val === "" || val === null || val === undefined) return null;
        const trimmed = typeof val === "string" ? val.trim() : val;
        if (trimmed === "") return null;
        const num = Number(trimmed);
        return Number.isFinite(num) ? num : null;
    };

    const handleSubmit = (e) => {
        e.preventDefault();

        const heartRate = parseOptionalNumber(formData.heartRate);
        const systolic = parseOptionalNumber(formData.systolic);
        const diastolic = parseOptionalNumber(formData.diastolic);
        const oxygen = parseOptionalNumber(formData.oxygen);
        const temperature = parseOptionalNumber(formData.temperature);
        const respiratoryRate = parseOptionalNumber(formData.respiratoryRate);

        const newVitals = {
            id: `VIT-${Date.now()}`, // A unique ID for the new vital
            patientId: patientId,
            timestamp: new Date().toISOString(), //the date the vital was recorded

            heartRate,
            bloodPressure: (systolic !== null || diastolic !== null)
                ? { systolic, diastolic }
                : null,
            oxygen,
            temperature,
            respiratoryRate,
            recordedBy: formData.recordedBy //the staff or doctor who recorded the vital
        };

        setVitalsArray(prev => [...prev, newVitals]);
        setFormData({
            heartRate: "",
            systolic: "",
            diastolic: "",
            oxygen: "",
            temperature: "",
            respiratoryRate: "",
            recordedBy: ""
        });
        setIsVitalFormOpen(false);
    };

    return (
        <form
            onSubmit={handleSubmit}
            className="w-full max-w-lg bg-white border border-gray-200 shadow-xl rounded-xl overflow-hidden flex flex-col max-h-[90vh]">
            <div className="flex flex-col gap-4 px-6 py-5 overflow-y-auto">
                <div className="flex justify-between items-center border-b border-gray-100 pb-3 mb-2">
                    <h2 className="font-semibold text-xl">Record Vitals</h2>
                    <button
                        type="button"
                        onClick={() => setIsVitalFormOpen(false)}
                        className="text-gray-400 hover:text-gray-600 font-bold"
                    >
                        ✕
                    </button>
                </div>

                <div className="flex flex-col gap-4">
                    <InputComponent
                        label="Heart Rate"
                        placeholder="72 BPM"
                        type="number"
                        value={formData.heartRate}
                        onChange={(e) => {
                            setFormData({ ...formData, heartRate: e.target.value });
                        }}
                    />

                    <InputComponent
                        label="Systolic BP"
                        placeholder="120 mmHg"
                        type="number"
                        value={formData.systolic}
                        onChange={(e) => {
                            setFormData({ ...formData, systolic: e.target.value });
                        }}
                    />

                    <InputComponent
                        label="Diastolic BP"
                        placeholder="80 mmHg"
                        type="number"
                        value={formData.diastolic}
                        onChange={(e) => {
                            setFormData({ ...formData, diastolic: e.target.value });
                        }}
                    />

                    <InputComponent
                        label="Oxygen Rate"
                        placeholder="98%"
                        type="number"
                        value={formData.oxygen}
                        onChange={(e) => {
                            setFormData({ ...formData, oxygen: e.target.value });
                        }}
                    />

                    <InputComponent
                        label="Temperature"
                        placeholder="36.5°C"
                        type="number"
                        value={formData.temperature}
                        onChange={(e) => {
                            setFormData({ ...formData, temperature: e.target.value });
                        }}
                    />

                    <InputComponent
                        label="Respiratory Rate"
                        placeholder="18"
                        type="number"
                        value={formData.respiratoryRate}
                        onChange={(e) => {
                            setFormData({ ...formData, respiratoryRate: e.target.value });
                        }}
                    />

                    <InputComponent
                        label="Recorded By"
                        placeholder="Nurse Fatima"
                        type="text"
                        value={formData.recordedBy}
                        onChange={(e) => {
                            setFormData({ ...formData, recordedBy: e.target.value });
                        }}
                    />


                    <div className="flex flex-row justify-end gap-3 mt-4 border-t border-gray-100 pt-4">
                        <button
                            type="button"
                            onClick={() => setIsVitalFormOpen(false)}
                            className="px-4 py-2 border border-gray-300 rounded-md bg-white hover:bg-gray-50 text-gray-700 text-sm font-semibold transition"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            className="px-4 py-2 rounded-md bg-blue-600 text-white hover:bg-blue-700 text-sm font-semibold transition"
                        >
                            Add Vitals
                        </button>
                    </div>
                </div>
            </div>
        </form>
    )
}
