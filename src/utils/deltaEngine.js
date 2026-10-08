// Defining the vitals and their label metadata
const VITAL_CONFIG = {
    heartRate: { label: "Heart Rate", unit: "bpm" },
    oxygen: { label: "Blood Oxygen", unit: "%" },
    temperature: { label: "Temperature", unit: "°C" },
    respiratoryRate: { label: "Resp. Rate", unit: "brpm" },
};

const DEFAULT_NORMAL_RANGES = {
    heartRate: { min: 60, max: 100 },
    oxygen: { min: 95, max: 100 },
    temperature: { min: 36.5, max: 37.5 },
    respiratoryRate: { min: 12, max: 20 },
    bloodPressure: { min: 90, max: 130, systolicMin: 90, systolicMax: 130, diastolicMin: 60, diastolicMax: 85 },
};


export const computeDeltas = (vitalsArray) => {

    if (!vitalsArray || vitalsArray.length < 2) return null;

    //Sorting chronologically without mutating original array
    const sorted = [...vitalsArray].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
    const previous = sorted[sorted.length - 2];
    const latest = sorted[sorted.length - 1];

    const deltas = [];

    for (const [key, config] of Object.entries(VITAL_CONFIG)) {
        const from = previous[key]
        const to = latest[key]

        if (from == null || to == null) continue; //if either is missing, skip and continue

        //getting the differnce between to and from and converting to flat(1 decimal place)
        const change = +(to - from).toFixed(1) //+ converts the string back to a number
        const percentChange = from !== 0 ? +(change / from * 100).toFixed(1) : 0;


        //tells us which way the value is moving....increasing, decreasing or stable
        let direction;
        if (Math.abs(change) < 1) direction = "stable";
        else if (change > 0) direction = "increasing";
        else direction = "decreasing";

        //tells us by how much or how big the change was or the change moved
        let severity;
        if (Math.abs(percentChange) >= 15) severity = "significant";
        else if (Math.abs(percentChange) >= 5) severity = "moderate";
        else severity = "minimal";

        deltas.push({
            vital: key, label: config.label, unit: config.unit,
            from, to, change, percentChange, direction, severity
        });

    }

    //Now handling for bloodpressure seperately 

    if (previous.bloodPressure && latest.bloodPressure) {
        //getting the change between latest and previous systolic and diastolic blood pressure levels
        const sysChange = +(latest.bloodPressure.systolic - previous.bloodPressure.systolic).toFixed(1);
        const diaChange = +(latest.bloodPressure.diastolic - previous.bloodPressure.diastolic).toFixed(1);

        //getting the percentage change
        const sysPercentChange = previous.bloodPressure.systolic !== 0 ? +(sysChange / previous.bloodPressure.systolic * 100).toFixed(1) : 0;
        const diaPercentChange = previous.bloodPressure.diastolic !== 0 ? +(diaChange / previous.bloodPressure.diastolic * 100).toFixed(1) : 0;

        //tells us which way the value is moving....increaing, decreasing or stable
        let sysDirection;
        if (Math.abs(sysChange) < 1) sysDirection = "stable";
        else if (sysChange > 0) sysDirection = "increasing";
        else sysDirection = "decreasing";

        let diaDirection;
        if (Math.abs(diaChange) < 1) diaDirection = "stable";
        else if (diaChange > 0) diaDirection = "increasing";
        else diaDirection = "decreasing";

        //tells us by how much or how big the change was or the change moved
        let sysSeverity;
        if (Math.abs(sysPercentChange) >= 15) sysSeverity = "significant";
        else if (Math.abs(sysPercentChange) >= 5) sysSeverity = "moderate";
        else sysSeverity = "minimal";

        let diaSeverity;
        if (Math.abs(diaPercentChange) >= 15) diaSeverity = "significant";
        else if (Math.abs(diaPercentChange) >= 5) diaSeverity = "moderate";
        else diaSeverity = "minimal";

        const sysSign = sysChange > 0 ? "+" : "";
        const diaSign = diaChange > 0 ? "+" : "";


        deltas.push({
            vital: "bloodPressure", label: "Blood Pressure", unit: "mmHg",
            change: `${sysSign}${sysChange}/${diaSign}${diaChange}`,
            percentChange: sysPercentChange,
            direction: sysDirection,
            severity: sysSeverity
        });

    }
    return deltas;
}

export function derivePatientStatus(deltas, latestVitals, normalRanges = DEFAULT_NORMAL_RANGES) {

    if (!latestVitals) return "No Data";
    if (deltas == null || deltas == undefined) return "Stable";

    //checking for significant increase in any of the vitals as oxygen is exempted
    const hasSignificantWorsening = deltas.some(deltas =>
        (deltas.severity == "significant" && deltas.direction == "increasing" && deltas.vital == "heartRate") ||
        (deltas.severity == "significant" && deltas.direction == "increasing" && deltas.vital == "temperature") ||
        (deltas.severity == "significant" && deltas.direction == "increasing" && deltas.vital == "respiratoryRate") ||
        (deltas.severity == "significant" && deltas.direction == "decreasing" && deltas.vital == "oxygen")
    );

    //checking for significant decrease in any of the vitals as oxygen is exempted once again
    const hasSignificantImprovement = deltas.some(deltas =>
        ((deltas.severity == "moderate" || deltas.severity == "significant") && deltas.direction == "decreasing" && deltas.vital == "heartRate") ||
        ((deltas.severity == "moderate" || deltas.severity == "significant") && deltas.direction == "decreasing" && deltas.vital == "temperature") ||
        ((deltas.severity == "moderate" || deltas.severity == "significant") && deltas.direction == "decreasing" && deltas.vital == "respiratoryRate") ||
        ((deltas.severity == "moderate" || deltas.severity == "significant") && deltas.direction == "increasing" && deltas.vital == "oxygen")
    );

    //checking for out of normal range 
    const outOfRange = Object.entries(latestVitals).some(([key, value]) => {
        if (key === "bloodPressure" && typeof value === "object" && value !== null) {
            const range = normalRanges.bloodPressure;
            if (!range) return false;
            const sysMin = range.systolicMin ?? range.min;
            const sysMax = range.systolicMax ?? range.max;
            const diaMin = range.diastolicMin ?? 60;
            const diaMax = range.diastolicMax ?? 85;

            const sysOut = typeof value.systolic === "number" && (
                (sysMin != null && value.systolic < sysMin) ||
                (sysMax != null && value.systolic > sysMax)
            );
            const diaOut = typeof value.diastolic === "number" && (
                (diaMin != null && value.diastolic < diaMin) ||
                (diaMax != null && value.diastolic > diaMax)
            );
            return sysOut || diaOut;
        }

        const range = normalRanges[key];
        if (!range) return false;
        if (typeof (value) !== "number") return false;
        if (value < range.min || value > range.max) return true; //if out of range
        return false;
    });

    //based on these booleans...
    if (outOfRange && hasSignificantWorsening) return "Review";
    else if (outOfRange || hasSignificantWorsening) return "Watch";
    else if (hasSignificantImprovement && !outOfRange) return "Improving";
    else return "Stable";
}

//Function for generating the latest update in the vital card
export function generateLatestUpdate(deltas, latestNote) {
    if (!deltas || deltas.length === 0) return "No data yet"
    const summaryParts = [];
    for (const delta of deltas) {
        if (delta.severity == "minimal") {
            continue; //skips this iteration
        } else {
            const arrow = delta.direction == "increasing" ? "↑" : delta.direction == "decreasing" ? "↓" : "→";

            const sign = delta.change > 0 ? "+" : "";
            summaryParts.push(`${delta.label} ${arrow} ${sign}${delta.change} ${delta.unit}`)
        }
    };

    if (summaryParts.length == 0 && latestNote) {
        if (latestNote.content.length > 80) {
            return latestNote.content.slice(0, 80) + "..."
        } else {
            return latestNote.content;
        }
    } else if (summaryParts.length == 0 && !latestNote) {
        return "No significant changes to report"
    }
    else
        return summaryParts.join(" . ");


}

//Function for buikding the timeline
export function buildTimelineEvents(vitalsArray, notesArray) {
    if (vitalsArray == null)
        vitalsArray = [];

    if (notesArray == null)
        notesArray = []

    //Normalzing i.e transforming each array into a common shape

    //Transforming vitals into timeline events
    const vitalsEvents = vitalsArray.map((vital) => ({
        type: "vital",
        timestamp: vital.timestamp,
        title: "Vitals recorded",
        data: vital
    }));

    //Transforming note into timeline events
    const notesEvents = notesArray.map((note) => ({
        type: "note",
        timestamp: note.timestamp,
        title: "Note added",
        data: note
    }));

    //Merging vital and note timelines and soting them chronologically 

    //Merging 

    const allEvents = [...vitalsEvents, ...notesEvents];
    //Sorting by timestamp
    const sortedEvents = allEvents.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

    return sortedEvents;

}

