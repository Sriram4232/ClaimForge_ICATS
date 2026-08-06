import React, { useState } from "react";

export default function LoginOverlay({ onLogin }) {
    const [email, setEmail] = useState("nominee@icats.in");
    const [password, setPassword] = useState("nominee");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");
        setLoading(true);
        try {
            const apiBaseUrl = import.meta.env.VITE_API_URL || "";
            const res = await fetch(`${apiBaseUrl}/api/auth/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password })
            });
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || "Invalid credentials.");
            }
            const data = await res.json();
            onLogin(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const fillCredentials = (emailVal, passVal) => {
        setEmail(emailVal);
        setPassword(passVal);
        setError("");
    };

    return (
        <div id="auth-overlay" className="auth-overlay">
            <div className="auth-card">
                <div className="auth-logo">
                    <i className="fa-solid fa-shield-halved"></i>
                </div>
                <h2>ICATS Portal</h2>
                <p>Insurance Claim Assistance & Tracking System</p>
                
                <form id="auth-form" onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label htmlFor="login-email">Portal Username / Email</label>
                        <input 
                            type="email" 
                            id="login-email" 
                            required 
                            placeholder="e.g. nominee@icats.in"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                        />
                    </div>
                    <div className="form-group">
                        <label htmlFor="login-password">Password</label>
                        <input 
                            type="password" 
                            id="login-password" 
                            required 
                            placeholder="••••••••"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                        />
                    </div>
                    {error && (
                        <div style={{ color: "var(--color-danger)", fontSize: "12px", marginBottom: "16px", fontWeight: "600" }}>
                            <i className="fa-solid fa-triangle-exclamation"></i> {error}
                        </div>
                    )}
                    <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
                        {loading ? (
                            <>
                                <i className="fa-solid fa-spinner fa-spin"></i> Authenticating...
                            </>
                        ) : (
                            <>
                                <i className="fa-solid fa-right-to-bracket"></i> Login & Authenticate
                            </>
                        )}
                    </button>
                </form>
                
                <div className="demo-credentials">
                    <h4><i className="fa-solid fa-circle-info"></i> Demo Accounts (MongoDB Verified)</h4>
                    <div className="credential-item" onClick={() => fillCredentials('nominee@icats.in', 'nominee')}>
                        <strong>Claimant (Nominee)</strong>
                        <span>nominee@icats.in / nominee</span>
                    </div>
                    <div className="credential-item" onClick={() => fillCredentials('agent@sbi.co.in', 'agent')}>
                        <strong>Bank Intermediary</strong>
                        <span>agent@sbi.co.in / agent</span>
                    </div>
                    <div className="credential-item" onClick={() => fillCredentials('assessor@lic.co.in', 'assessor')}>
                        <strong>Insurer Assessor (Underwriter)</strong>
                        <span>assessor@lic.co.in / assessor</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
