import React, { useState } from "react";

export default function Sidebar({ user, activeSection, onSectionChange, onLogout }) {
    const [collapsed, setCollapsed] = useState(false);

    const toggleSidebar = () => {
        setCollapsed(!collapsed);
    };

    const role = user.role;

    return (
        <aside className={`sidebar ${collapsed ? "collapsed" : ""}`}>
            <div className="sidebar-header" style={{ display: "flex", alignItems: "center", width: "100%" }}>
                <button 
                    id="toggle-sidebar" 
                    onClick={toggleSidebar} 
                    className="sidebar-logo-btn" 
                    title={collapsed ? "Expand Sidebar" : "Collapse Sidebar"}
                    style={{ background: "transparent", border: "none", cursor: "pointer", padding: 0, display: "flex", alignItems: "center", gap: "12px", textAlign: "left", width: "100%" }}
                >
                    <div className="sidebar-logo"><i className="fa-solid fa-shield-halved"></i></div>
                    <div className="sidebar-title-wrapper">
                        <h1 style={{ margin: 0, lineHeight: 1, fontSize: "22px", color: "var(--text-main)", fontFamily: "var(--font-heading)", fontWeight: 800 }}>ICATS</h1>
                        <span style={{ fontSize: "10px", color: "var(--text-muted)", display: "block", marginTop: "2px", fontFamily: "var(--font-body)" }}>Decision Engine</span>
                    </div>
                </button>
            </div>
            
            <nav style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                {/* Claimant Only Tab Links */}
                {role === "claimant" && (
                    <>
                        <a 
                            href="#" 
                            className={`menu-item ${activeSection === "wizard-section" ? "active" : ""}`}
                            onClick={() => onSectionChange("wizard-section")}
                        >
                            <i className="fa-solid fa-file-invoice-dollar"></i> <span>New Claim Wizard</span>
                        </a>
                        <a 
                            href="#" 
                            className={`menu-item ${activeSection === "tracker-section" ? "active" : ""}`}
                            onClick={() => onSectionChange("tracker-section")}
                        >
                            <i className="fa-solid fa-route"></i> <span>Claim Tracker</span>
                        </a>
                    </>
                )}
                
                {/* Bank Employee Only Tab Links */}
                {role === "bank_employee" && (
                    <a 
                        href="#" 
                        className={`menu-item ${activeSection === "branch-section" ? "active" : ""}`}
                        onClick={() => onSectionChange("branch-section")}
                    >
                        <i className="fa-solid fa-building-columns"></i> <span>Branch Directory</span>
                    </a>
                )}
                
                {/* Insurer Only Tab Links */}
                {role === "insurer" && (
                    <a 
                        href="#" 
                        className={`menu-item ${activeSection === "inbox-section" ? "active" : ""}`}
                        onClick={() => onSectionChange("inbox-section")}
                    >
                        <i className="fa-solid fa-inbox"></i> <span>Assessment Inbox</span>
                    </a>
                )}
                
                {/* Shared Clearance Certificate link */}
                <a 
                    href="#" 
                    id="menu-cert" 
                    className={`menu-item ${activeSection === "certificate-section" ? "active" : ""}`}
                    onClick={() => onSectionChange("certificate-section")}
                >
                    <i className="fa-solid fa-stamp"></i> <span>Clearance Certificate</span>
                </a>
                
                {/* Shared Name Affidavit link (visible for claimant & bank agent) */}
                {(role === "claimant" || role === "bank_employee") && (
                    <a 
                        href="#" 
                        id="menu-affidavit" 
                        className={`menu-item ${activeSection === "affidavit-section" ? "active" : ""}`}
                        onClick={() => onSectionChange("affidavit-section")}
                    >
                        <i className="fa-solid fa-file-contract"></i> <span>Name Affidavit</span>
                    </a>
                )}
            </nav>
            
            <div className="sidebar-footer">
                <div className="user-badge">
                    <div className="user-avatar"><i className="fa-regular fa-user-circle"></i></div>
                    <div className="user-info">
                        <h4 id="user-name">{user.name}</h4>
                        <span id="user-role" style={{ textTransform: "capitalize" }}>{user.role.replace("_", " ")}</span>
                    </div>
                </div>
                <button className="btn btn-secondary btn-block" onClick={onLogout}>
                    <i className="fa-solid fa-right-from-bracket text-danger"></i> <span>Logout</span>
                </button>
            </div>
        </aside>
    );
}
