import React, { useState } from "react";
import { auth } from "../firebase";
import { sendPasswordResetEmail } from "firebase/auth";

/**
 * Firebase Email Diagnostic Tool
 * Use this component to test if Firebase email sending is working
 */
const FirebaseEmailTest = () => {
    const [testEmail, setTestEmail] = useState("");
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(false);

    const addLog = (message, type = "info") => {
        const timestamp = new Date().toLocaleTimeString();
        setLogs(prev => [...prev, { message, type, timestamp }]);
        console.log(`[${type.toUpperCase()}] ${message}`);
    };

    const testPasswordReset = async () => {
        setLogs([]);
        setLoading(true);
        
        addLog("🔍 Starting Firebase email test...", "info");
        addLog(`Testing with email: ${testEmail}`, "info");

        try {
            // Check Firebase config
            addLog("✅ Firebase Auth initialized", "success");
            addLog(`Auth domain: ${auth.config.authDomain}`, "info");
            addLog(`API Key exists: ${!!auth.config.apiKey}`, "info");

            // Attempt to send email
            addLog("📧 Attempting to send password reset email...", "info");
            
            await sendPasswordResetEmail(auth, testEmail);
            
            addLog("✅ SUCCESS! Email sent successfully!", "success");
            addLog("📬 Check your inbox (and spam folder)", "success");
            addLog(`Email should arrive from: noreply@${auth.config.authDomain}`, "info");
            
        } catch (error) {
            addLog(`❌ ERROR: ${error.code}`, "error");
            addLog(`Message: ${error.message}`, "error");
            
            // Detailed error analysis
            switch (error.code) {
                case "auth/user-not-found":
                    addLog("💡 This email is NOT registered in Firebase", "warning");
                    addLog("🔧 Solution: Sign up with this email first, then test reset", "warning");
                    break;
                case "auth/invalid-email":
                    addLog("💡 Email format is invalid", "warning");
                    break;
                case "auth/network-request-failed":
                    addLog("💡 Network connection issue", "warning");
                    addLog("🔧 Check your internet connection", "warning");
                    break;
                case "auth/too-many-requests":
                    addLog("💡 Too many attempts from this device", "warning");
                    addLog("🔧 Wait 10-15 minutes before trying again", "warning");
                    break;
                default:
                    addLog("🔧 Check Firebase Console for more details", "warning");
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed bottom-20 right-6 w-96 bg-white dark:bg-zinc-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-zinc-800 p-6 z-50">
            <div className="mb-4">
                <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-1">
                    🔧 Firebase Email Tester
                </h3>
                <p className="text-xs text-slate-500 dark:text-zinc-500">
                    Diagnostic tool to test password reset emails
                </p>
            </div>

            <div className="space-y-3">
                <div>
                    <label className="text-xs font-bold text-slate-700 dark:text-zinc-300 mb-1 block">
                        Test Email Address
                    </label>
                    <input
                        type="email"
                        value={testEmail}
                        onChange={(e) => setTestEmail(e.target.value)}
                        placeholder="Enter registered email"
                        className="w-full px-3 py-2 bg-gray-50 dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 rounded-lg text-sm dark:text-white focus:ring-2 focus:ring-blue-500/50 outline-none"
                    />
                    <p className="text-xs text-slate-500 dark:text-zinc-500 mt-1">
                        ⚠️ Email must be registered in Firebase first
                    </p>
                </div>

                <button
                    onClick={testPasswordReset}
                    disabled={loading || !testEmail}
                    className="w-full bg-slate-900 dark:bg-white text-white dark:text-black font-semibold py-2.5 rounded-lg hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                    {loading ? "Testing..." : "🧪 Test Email Sending"}
                </button>
            </div>

            {/* Logs */}
            {logs.length > 0 && (
                <div className="mt-4 max-h-60 overflow-y-auto space-y-2 border-t border-gray-200 dark:border-zinc-800 pt-4">
                    {logs.map((log, idx) => (
                        <div
                            key={idx}
                            className={`text-xs p-2 rounded border ${
                                log.type === "success"
                                    ? "bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-400"
                                    : log.type === "error"
                                    ? "bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 text-red-700 dark:text-red-400"
                                    : log.type === "warning"
                                    ? "bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-400"
                                    : "bg-gray-50 dark:bg-zinc-800 border-gray-200 dark:border-zinc-700 text-slate-700 dark:text-zinc-300"
                            }`}
                        >
                            <div className="font-mono text-[10px] text-slate-400 dark:text-zinc-500 mb-1">
                                {log.timestamp}
                            </div>
                            <div className="font-medium">{log.message}</div>
                        </div>
                    ))}
                </div>
            )}

            <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                <p className="text-xs font-semibold text-blue-700 dark:text-blue-400 mb-1">
                    📋 Troubleshooting Tips:
                </p>
                <ul className="text-xs text-blue-600 dark:text-blue-400 space-y-1 ml-4 list-disc">
                    <li>Create account first, then test reset</li>
                    <li>Check spam/junk folder</li>
                    <li>Wait 2-3 minutes for email delivery</li>
                    <li>Try different email provider (Gmail, Outlook)</li>
                </ul>
            </div>
        </div>
    );
};

export default FirebaseEmailTest;
