import { createContext, useState, useEffect } from "react";

export const ThresholdContext = createContext();

const defaultRanges = {
    heartRate: { min: 60, max: 100 },
    bloodPressure: { min: 90, max: 130, systolicMin: 90, systolicMax: 130 },
    oxygen: { min: 95, max: 100 },
    temperature: { min: 35.5, max: 38.0 }
};

export default function ThresholdProvider({ children }) {
    const [thresholds, setThresholds] = useState(() => {
        const saved = localStorage.getItem("carearc_normal_ranges");
        if (saved) {
            try {
                return JSON.parse(saved);
            } catch (e) {
                console.error("Error parsing stored ranges", e);
            }
        }
        return defaultRanges;
    });

    useEffect(() => {
        localStorage.setItem("carearc_normal_ranges", JSON.stringify(thresholds));
    }, [thresholds]);

    return (
        <ThresholdContext.Provider value={{ thresholds, setThresholds }}>
            {children}
        </ThresholdContext.Provider>
    );
}
