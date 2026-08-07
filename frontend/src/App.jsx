import React, { useState, useEffect } from "react";
import LoginOverlay from "./components/LoginOverlay";
import Sidebar from "./components/Sidebar";
import NewClaimWizard from "./components/NewClaimWizard";
import ClaimTracker from "./components/ClaimTracker";
import BranchDirectory from "./components/BranchDirectory";
import AssessmentInbox from "./components/AssessmentInbox";
import ClearanceCertificate from "./components/ClearanceCertificate";
import NameAffidavit from "./components/NameAffidavit";
import AutopilotSimulator from "./components/AutopilotSimulator";

export default function App() {
    const [user, setUser] = useState(() => {
        const saved = localStorage.getItem("icats_user");
        return saved ? JSON.parse(saved) : null;
    });

    const [activeSection, setActiveSection] = useState(() => {
        if (!user) return "";
        if (user.role === "claimant") return "wizard-section";
        if (user.role === "bank_employee") return "branch-section";
        if (user.role === "insurer") return "inbox-section";
        return "";
    });

    const [claims, setClaims] = useState([]);
    const [activeClaimId, setActiveClaimId] = useState("");
    const [bgVideoSrc, setBgVideoSrc] = useState("/api/video/background?role=guest");

    // Fetch credentials helper with JWT token header
    const customFetch = async (url, options = {}) => {
        const headers = { ...options.headers };
        if (user && user.token) {
            headers["Authorization"] = `Bearer ${user.token}`;
        }
        const apiBaseUrl = import.meta.env.VITE_API_URL || "";
        const targetUrl = url.startsWith("http") ? url : `${apiBaseUrl}${url}`;
        return fetch(targetUrl, { ...options, headers });
    };

    const loadClaims = async () => {
        if (!user) return;
        try {
            const res = await customFetch("/api/claims");
            if (res.ok) {
                const data = await res.json();
                setClaims(data);
                if (data.length > 0 && !activeClaimId) {
                    setActiveClaimId(data[0].id);
                }
            }
        } catch (err) {
            console.error("Failed to load claims:", err);
        }
    };

    useEffect(() => {
        if (user) {
            loadClaims();
            setBgVideoSrc(`/api/video/background?role=${user.role}`);
        } else {
            setClaims([]);
            setBgVideoSrc("/api/video/background?role=guest");
        }
    }, [user]);

    const handleLogin = (loginData) => {
        localStorage.setItem("icats_user", JSON.stringify(loginData));
        setUser(loginData);
        // Direct roles to starting pages
        if (loginData.role === "claimant") {
            setActiveSection("wizard-section");
        } else if (loginData.role === "bank_employee") {
            setActiveSection("branch-section");
        } else if (loginData.role === "insurer") {
            setActiveSection("inbox-section");
        }
    };

    const handleLogout = () => {
        localStorage.removeItem("icats_user");
        setUser(null);
        setActiveSection("");
        setActiveClaimId("");
    };

    // Video source checker
    const getBgVideoHtml = () => {
        const apiBaseUrl = import.meta.env.VITE_API_URL || "";
        const videoUrl = bgVideoSrc.startsWith("http") ? bgVideoSrc : `${apiBaseUrl}${bgVideoSrc}`;
        return (
            <video key={videoUrl} autoPlay loop muted playsInline id="bg-video">
                <source src={videoUrl} type="video/mp4" />
            </video>
        );
    };

    return (
        <div>
            {/* Background matrices and videos */}
            <div className="fixed-bg-aurora"></div>
            <div className="fixed-bg-grid"></div>
            {getBgVideoHtml()}

            {!user ? (
                <LoginOverlay onLogin={handleLogin} />
            ) : (
                <div className="app-container">
                    <Sidebar 
                        user={user} 
                        activeSection={activeSection} 
                        onSectionChange={(sect) => {
                            setActiveSection(sect);
                        }} 
                        onLogout={handleLogout} 
                    />

                    <main className="main-workspace">
                        <div className="workspace-header">
                            <div className="workspace-title">
                                <h2 style={{ textTransform: "capitalize" }}>
                                    {activeSection.replace("-section", "").replace(/-/g, " ")} Workspace
                                </h2>
                                <p>Insurance Claims Assistance & Verification Portal</p>
                            </div>
                            
                            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                                {/* Autopilot simulator top-right button */}
                                <button 
                                    className="btn btn-secondary btn-sm" 
                                    style={{ padding: "8px 14px", fontSize: "12px" }}
                                    onClick={() => setActiveSection("autopilot-section")}
                                >
                                    <i className="fa-solid fa-robot"></i> Autopilot Simulator
                                </button>
                                
                                <span className="status-badge status-approved" style={{ fontSize: "11px", fontWeight: "700" }}>
                                    {user.role.replace("_", " ")}
                                </span>
                            </div>
                        </div>

                        {/* Route Content Panels */}
                        {activeSection === "wizard-section" && (
                            <NewClaimWizard 
                                activeClaimId={activeClaimId}
                                onNavigateToTracker={() => setActiveSection("tracker-section")}
                                reloadClaims={loadClaims}
                                customFetch={customFetch}
                            />
                        )}
                        {activeSection === "tracker-section" && (
                            <ClaimTracker claims={claims} activeClaimId={activeClaimId} />
                        )}
                        {activeSection === "branch-section" && (
                            <BranchDirectory 
                                claims={claims} 
                                reloadClaims={loadClaims} 
                                customFetch={customFetch} 
                            />
                        )}
                        {activeSection === "inbox-section" && (
                            <AssessmentInbox 
                                claims={claims} 
                                reloadClaims={loadClaims} 
                                customFetch={customFetch}
                                onNavigateToCert={() => setActiveSection("certificate-section")}
                            />
                        )}
                        {activeSection === "certificate-section" && (
                            <ClearanceCertificate claims={claims} activeClaimId={activeClaimId} />
                        )}
                        {activeSection === "affidavit-section" && (
                            <NameAffidavit claims={claims} activeClaimId={activeClaimId} />
                        )}
                        {activeSection === "autopilot-section" && (
                            <AutopilotSimulator reloadClaims={loadClaims} customFetch={customFetch} />
                        )}
                    </main>
                </div>
            )}
        </div>
    );
}
