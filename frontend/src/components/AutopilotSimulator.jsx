import React, { useState } from "react";

export default function AutopilotSimulator({ reloadClaims, customFetch }) {
    const [preset, setPreset] = useState("CASE-002");
    const [logs, setLogs] = useState(["[System] Console initialized. Awaiting Autopilot simulation trigger..."]);
    const [simulating, setSimulating] = useState(false);

    const runAutopilot = async () => {
        if (simulating) return;
        setSimulating(true);
        setLogs(["[System] Connecting to autopilot microservices core..."]);
        
        try {
            const res = await customFetch(`/api/agents/simulate?case_id=${preset}`, {
                method: "POST"
            });
            if (res.ok) {
                const data = await res.json();
                
                // Typewriter simulation print loop
                let idx = 0;
                const printNext = () => {
                    if (idx < data.logs.length) {
                        setLogs(prev => [...prev, data.logs[idx]]);
                        idx++;
                        setTimeout(printNext, 600);
                    } else {
                        setLogs(prev => [...prev, `[System] Autopilot resolved Case ${preset} cleanly. Database updated.`]);
                        setSimulating(false);
                        reloadClaims();
                    }
                };
                
                printNext();
            } else {
                setLogs(prev => [...prev, "[System Error] Simulation connection failed."]);
                setSimulating(false);
            }
        } catch (err) {
            console.error("Simulation failed:", err);
            setLogs(prev => [...prev, "[System Error] Autopilot connection broke. Try checking MongoDB connection logs."]);
            setSimulating(false);
        }
    };

    const highlightLogs = (log) => {
        let text = log;
        text = text.replace(/\[Claimant Agent\]/g, '<span style="color:#60a5fa; font-weight:700;">[Claimant Agent]</span>');
        text = text.replace(/\[Bank Agent\]/g, '<span style="color:#f59e0b; font-weight:700;">[Bank Agent]</span>');
        text = text.replace(/\[Insurer Agent\]/g, '<span style="color:#10b981; font-weight:700;">[Insurer Agent]</span>');
        text = text.replace(/\[System\]/g, '<span style="color:#38bdf8; font-weight:700;">[System]</span>');
        text = text.replace(/\[System Error\]/g, '<span style="color:var(--color-danger); font-weight:700;">[System Error]</span>');
        return <span dangerouslySetInnerHTML={{ __html: text }}></span>;
    };

    return (
        <section id="autopilot-section" className="workspace-section active">
            <div className="glass-card">
                <h3>Automated Multi-Agent Autopilot Simulator</h3>
                <p className="card-desc">Run a simulation of three microservices (Claimant Agent, Bank Agent, and Insurer Agent) collaborating to resolve claims without manual interaction.</p>
                
                <div style={{ marginBottom: "16px", display: "flex", gap: "12px", alignItems: "center" }}>
                    <span style={{ fontSize: "13px" }}>Select Autopilot Preset:</span>
                    <select 
                        id="sim-preset" 
                        value={preset} 
                        onChange={(e) => setPreset(e.target.value)}
                        style={{ background: "rgba(0,0,0,0.3)", border: "1px solid var(--border-glass)", borderRadius: "6px", padding: "6px 12px", color: "var(--text-main)", fontFamily: "var(--font-body)", fontSize: "13px" }}
                        disabled={simulating}
                    >
                        <option value="CASE-002">Case 2: Accidental Death (Auto PMR/FIR Fetching)</option>
                        <option value="CASE-003">Case 3: Spelling Mismatch (Auto Affidavit generation & KYC verification)</option>
                    </select>
                    <button className="btn btn-primary" onClick={runAutopilot} disabled={simulating}>
                        <i className="fa-solid fa-play"></i> Launch Simulation
                    </button>
                </div>

                <div className="terminal-window">
                    <div className="terminal-header">
                        <div className="terminal-dots">
                            <div className="terminal-dot red"></div>
                            <div className="terminal-dot yellow"></div>
                            <div className="terminal-dot green"></div>
                        </div>
                        <span style={{ marginLeft: "10px" }}>Autopilot Logs Console</span>
                    </div>
                    <div className="terminal-body" id="autopilot-terminal" style={{ scrollBehavior: "smooth" }}>
                        {logs.map((log, idx) => (
                            <div key={idx} className="terminal-line">
                                {highlightLogs(log)}
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </section>
    );
}
