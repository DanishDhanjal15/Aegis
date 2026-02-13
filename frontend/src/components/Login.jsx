import React, { useState } from "react";
import { User, Lock, Mail, ChevronRight, ShieldCheck, ArrowLeft } from "lucide-react";
import { auth } from "../firebase";
import { 
    createUserWithEmailAndPassword, 
    signInWithEmailAndPassword, 
    sendPasswordResetEmail
} from "firebase/auth";

const Login = ({ onLoginSuccess }) => {
    const [isLogin, setIsLogin] = useState(true);
    const [isForgotPassword, setIsForgotPassword] = useState(false);
    const [formData, setFormData] = useState({
        email: "",
        password: "",
    });
    const [resetEmail, setResetEmail] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
        setError("");
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError("");
        setSuccess("");

        try {
            if (isLogin) {
                // Login with Firebase
                const userCredential = await signInWithEmailAndPassword(auth, formData.email, formData.password);
                const user = userCredential.user;

                // Get the ID token
                const idToken = await user.getIdToken();

                // Store token and user info
                localStorage.setItem("aegis_token", idToken);
                localStorage.setItem("aegis_user", user.email);

                onLoginSuccess(user.email);
            } else {
                // Signup with Firebase
                const userCredential = await createUserWithEmailAndPassword(auth, formData.email, formData.password);

                setSuccess("Account created! Please log in.");
                setIsLogin(true);
                setFormData({ email: "", password: "" });
            }
        } catch (err) {
            // Handle Firebase errors with user-friendly messages
            let errorMessage = "An error occurred";

            switch (err.code) {
                case "auth/email-already-in-use":
                    errorMessage = "Email already in use";
                    break;
                case "auth/invalid-email":
                    errorMessage = "Invalid email address";
                    break;
                case "auth/weak-password":
                    errorMessage = "Password should be at least 6 characters";
                    break;
                case "auth/user-not-found":
                    errorMessage = "No account found with this email";
                    break;
                case "auth/wrong-password":
                    errorMessage = "Incorrect password";
                    break;
                case "auth/invalid-credential":
                    errorMessage = "Invalid email or password";
                    break;
                case "auth/network-request-failed":
                    errorMessage = "Network error. Check your connection.";
                    break;
                default:
                    errorMessage = err.message || "Authentication failed";
            }

            setError(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    const handlePasswordReset = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError("");
        setSuccess("");

        if (!resetEmail.trim()) {
            setError("Please enter your email address");
            setLoading(false);
            return;
        }

        try {
            // Send password reset email without actionCodeSettings
            // Firebase will use default settings and redirect to its hosted page
            await sendPasswordResetEmail(auth, resetEmail);
            
            setSuccess("Password reset email sent! Check your inbox (including spam folder).");
            setResetEmail("");
            
            console.log("Password reset email sent successfully to:", resetEmail);
            
            // Switch back to login after 5 seconds
            setTimeout(() => {
                setIsForgotPassword(false);
                setSuccess("");
            }, 5000);
        } catch (err) {
            console.error("Password reset error:", err);
            let errorMessage = "Failed to send reset email";

            switch (err.code) {
                case "auth/invalid-email":
                    errorMessage = "Invalid email address";
                    break;
                case "auth/user-not-found":
                    errorMessage = "No account found with this email. Please sign up first.";
                    break;
                case "auth/network-request-failed":
                    errorMessage = "Network error. Check your connection.";
                    break;
                case "auth/too-many-requests":
                    errorMessage = "Too many attempts. Please try again later.";
                    break;
                case "auth/invalid-continue-uri":
                case "auth/missing-continue-uri":
                    errorMessage = "Configuration error. Using Firebase default reset page.";
                    break;
                default:
                    errorMessage = err.message || "Failed to send reset email";
            }

            setError(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-zinc-950 flex items-center justify-center p-4">
            {/* Background blobs for depth */}
            <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
                <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-500/5 rounded-full blur-[120px]"></div>
                <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-indigo-500/5 rounded-full blur-[120px]"></div>
            </div>

            <div className="w-full max-w-md bg-white dark:bg-zinc-900 rounded-[2.5rem] shadow-2xl border border-gray-100 dark:border-zinc-800 p-8 relative overflow-hidden animate-in fade-in zoom-in duration-500">
                {/* Header */}
                <div className="text-center mb-8">
                    <div className="w-16 h-16 bg-slate-900 dark:bg-white rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-xl shadow-slate-900/10 dark:shadow-white/5">
                        <ShieldCheck size={32} className="text-white dark:text-black" />
                    </div>
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2 tracking-tight">
                        Aegis Guardian
                    </h1>
                    <p className="text-slate-500 dark:text-zinc-400 text-sm font-medium">
                        {isForgotPassword 
                            ? "Reset your password via email verification." 
                            : isLogin 
                            ? "Welcome back, secure your network." 
                            : "Create your security administrator account."}
                    </p>
                </div>

                {/* Error/Success Messages */}
                {error && (
                    <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-100 dark:border-red-900/30 text-red-600 dark:text-red-400 text-xs font-semibold rounded-2xl flex items-center gap-3 animate-in slide-in-from-top-2">
                        <div className="w-1.5 h-1.5 bg-red-400 rounded-full animate-pulse"></div>
                        {error}
                    </div>
                )}
                {success && (
                    <div className="mb-6 p-4 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-100 dark:border-emerald-900/30 text-emerald-600 dark:text-emerald-400 text-xs font-semibold rounded-2xl flex items-center gap-3 animate-in slide-in-from-top-2">
                        <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse"></div>
                        {success}
                    </div>
                )}

                {/* Forgot Password Form */}
                {isForgotPassword ? (
                    <form onSubmit={handlePasswordReset} className="space-y-5">
                        <div className="space-y-1.5">
                            <label className="text-xs font-bold text-slate-700 dark:text-zinc-300 ml-1 uppercase tracking-wider">
                                Email Address
                            </label>
                            <div className="relative group">
                                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-400 dark:text-zinc-500 group-focus-within:text-blue-500 transition-colors">
                                    <Mail size={18} />
                                </div>
                                <input
                                    type="email"
                                    value={resetEmail}
                                    onChange={(e) => setResetEmail(e.target.value)}
                                    required
                                    placeholder="Enter your email"
                                    className="w-full pl-11 pr-4 py-3.5 bg-gray-50 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700/50 rounded-2xl text-sm focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 dark:text-white outline-none transition-all placeholder:text-slate-400/80 dark:placeholder:text-zinc-600"
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-slate-900 dark:bg-white text-white dark:text-black font-bold py-4 rounded-2xl shadow-lg hover:shadow-slate-900/20 dark:hover:shadow-white/10 hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-2 group disabled:opacity-50 disabled:hover:scale-100"
                        >
                            {loading ? (
                                <div className="w-5 h-5 border-2 border-white/30 dark:border-black/30 border-t-white dark:border-t-black rounded-full animate-spin"></div>
                            ) : (
                                <>
                                    Send Reset Link
                                    <ChevronRight size={18} className="group-hover:translate-x-1 transition-transform" />
                                </>
                            )}
                        </button>
                    </form>
                ) : (
                    /* Email/Password Login/Signup Form */
                    <form onSubmit={handleSubmit} className="space-y-5">
                        <div className="space-y-1.5">
                            <label className="text-xs font-bold text-slate-700 dark:text-zinc-300 ml-1 uppercase tracking-wider">
                                Email
                            </label>
                            <div className="relative group">
                                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-400 dark:text-zinc-500 group-focus-within:text-blue-500 transition-colors">
                                    <Mail size={18} />
                                </div>
                                <input
                                    type="email"
                                    name="email"
                                    value={formData.email}
                                    onChange={handleChange}
                                    required
                                    placeholder="Enter your email"
                                    className="w-full pl-11 pr-4 py-3.5 bg-gray-50 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700/50 rounded-2xl text-sm focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 dark:text-white outline-none transition-all placeholder:text-slate-400/80 dark:placeholder:text-zinc-600"
                                />
                            </div>
                        </div>

                        <div className="space-y-1.5">
                            <label className="text-xs font-bold text-slate-700 dark:text-zinc-300 ml-1 uppercase tracking-wider">
                                Password
                            </label>
                            <div className="relative group">
                                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-400 dark:text-zinc-500 group-focus-within:text-blue-500 transition-colors">
                                    <Lock size={18} />
                                </div>
                                <input
                                    type="password"
                                    name="password"
                                    value={formData.password}
                                    onChange={handleChange}
                                    required
                                    placeholder="••••••••"
                                    className="w-full pl-11 pr-4 py-3.5 bg-gray-50 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700/50 rounded-2xl text-sm focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 dark:text-white outline-none transition-all placeholder:text-slate-400/80 dark:placeholder:text-zinc-600"
                                />
                            </div>
                        </div>

                        {/* Forgot Password Link */}
                        {isLogin && (
                            <div className="text-right -mt-2">
                                <button
                                    type="button"
                                    onClick={() => {
                                        setIsForgotPassword(true);
                                        setError("");
                                        setSuccess("");
                                    }}
                                    className="text-xs font-semibold text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors"
                                >
                                    Forgot Password?
                                </button>
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full bg-slate-900 dark:bg-white text-white dark:text-black font-bold py-4 rounded-2xl shadow-lg hover:shadow-slate-900/20 dark:hover:shadow-white/10 hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-2 group disabled:opacity-50 disabled:hover:scale-100"
                        >
                            {loading ? (
                                <div className="w-5 h-5 border-2 border-white/30 dark:border-black/30 border-t-white dark:border-t-black rounded-full animate-spin"></div>
                            ) : (
                                <>
                                    {isLogin ? "Authenticate" : "Create Account"}
                                    <ChevronRight size={18} className="group-hover:translate-x-1 transition-transform" />
                                </>
                            )}
                        </button>
                    </form>
                )}

                <div className="mt-8 text-center">
                    <button
                        onClick={() => {
                            if (isForgotPassword) {
                                setIsForgotPassword(false);
                                setResetEmail("");
                            } else {
                                setIsLogin(!isLogin);
                            }
                            setError("");
                            setSuccess("");
                        }}
                        className="text-sm font-semibold text-slate-600 dark:text-zinc-400 hover:text-slate-900 dark:hover:text-white transition-colors flex items-center justify-center gap-2 mx-auto"
                    >
                        {isForgotPassword ? (
                            <>
                                <ArrowLeft size={16} /> Back to Login
                            </>
                        ) : isLogin ? (
                            <>
                                Don't have an account? <span className="text-blue-500 border-b border-blue-500/0 hover:border-blue-500 transition-all">Sign up</span>
                            </>
                        ) : (
                            <>
                                <ArrowLeft size={16} /> Back to Login
                            </>
                        )}
                    </button>
                </div>
            </div>

            <p className="absolute bottom-8 text-[11px] font-bold uppercase tracking-[0.2em] text-slate-400 dark:text-zinc-600">
                Aegis Network Security • 2026
            </p>
        </div>
    );
};

export default Login;
