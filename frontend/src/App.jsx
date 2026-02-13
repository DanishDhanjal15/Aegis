import React, { useEffect, useState } from "react";
import {
  fetchDevices,
  fetchLogs,
  triggerScan,
  toggleDeviceBlock,
  startAutoScan,
  stopAutoScan,
  getAutoScanStatus,
  triggerPanicMode,
  triggerUnlockPanicControl,
  updateDeviceNickname,
  getScanStatus,
} from "./api";
import {
  Sun, Moon, RefreshCw, Shield, AlertTriangle,
  ChevronRight, X, Laptop, Smartphone, Router, Server,
  Ban, History, FileText, CheckCircle2, Lock, Clock, Zap, Wifi, Activity
} from "lucide-react";
import Chatbot from "./components/Chatbot";
import Login from "./components/Login";
import FirebaseEmailTest from "./components/FirebaseEmailTest";
import { auth } from "./firebase";
import { onAuthStateChanged, signOut } from "firebase/auth";

function App() {
  // Toggle this to show/hide diagnostic tool
  const [showEmailTest, setShowEmailTest] = React.useState(false);
  const [user, setUser] = useState(localStorage.getItem("aegis_user"));
  const [devices, setDevices] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [processingId, setProcessingId] = useState(null);
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [activeTab, setActiveTab] = useState("dashboard");
  const [theme, setTheme] = useState(localStorage.getItem("theme") || "light");
  const [panicProcessing, setPanicProcessing] = useState(false);
  const [unlockProcessing, setUnlockProcessing] = useState(false);
  const [autoScanEnabled, setAutoScanEnabled] = useState(false);
  const [autoScanInterval, setAutoScanInterval] = useState(5);
  const [nicknameDraft, setNicknameDraft] = useState("");

  useEffect(() => {
    if (theme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
    localStorage.setItem("theme", theme);
  }, [theme]);

  const toggleTheme = () => setTheme(theme === "light" ? "dark" : "light");

  useEffect(() => {
    loadData();
    loadAutoScanStatus();

    // Listen for Firebase auth state changes
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      if (user) {
        // User is signed in, refresh token periodically
        const token = await user.getIdToken();
        localStorage.setItem("aegis_token", token);
        localStorage.setItem("aegis_user", user.email);
        setUser(user.email);
      } else {
        // User is signed out
        localStorage.removeItem("aegis_token");
        localStorage.removeItem("aegis_user");
        setUser(null);
      }
    });

    // Cleanup subscription on unmount
    return () => unsubscribe();
  }, []);

  // Poll for new devices when auto-scan is enabled
  useEffect(() => {
    if (!autoScanEnabled) return;

    let lastDeviceCount = devices.length;

    const pollInterval = setInterval(async () => {
      try {
        const currentDevices = await fetchDevices();
        const currentLogs = await fetchLogs();

        // Update if devices or logs changed
        if (currentDevices.length !== lastDeviceCount ||
          JSON.stringify(currentDevices) !== JSON.stringify(devices)) {
          setDevices(currentDevices);
          setLogs(currentLogs);
          lastDeviceCount = currentDevices.length;
        }
      } catch (error) {
        console.error("Error polling for updates:", error);
      }
    }, 15000); // Check every 15 seconds to reduce load

    return () => clearInterval(pollInterval);
  }, [autoScanEnabled]);

  const loadData = async () => {
    const [devicesData, logsData] = await Promise.all([
      fetchDevices(),
      fetchLogs()
    ]);
    setDevices(devicesData || []);
    setLogs(logsData || []);
  };

  const openDeviceModal = (device) => {
    setSelectedDevice(device);
    setNicknameDraft(device.nickname || device.name || device.vendor || "");
  };

  const isMeaningful = (val) => {
    if (!val || typeof val !== "string") return false;
    const trimmed = val.trim();
    if (trimmed.length <= 1) return false;
    if (/^\d+$/.test(trimmed)) return false;
    return true;
  };

  const displayNameFor = (device) => {
    if (isMeaningful(device.nickname)) return device.nickname;
    if (isMeaningful(device.hostname)) return device.hostname;
    if (isMeaningful(device.vendor)) return device.vendor;
    return device.ip;
  };

  const handleScan = async () => {
    setLoading(true);
    await triggerScan();

    // Poll for scan completion
    const pollInterval = setInterval(async () => {
      const status = await getScanStatus();
      if (!status.is_scanning) {
        clearInterval(pollInterval);
        await loadData(); // Refresh data after scan completes
        setLoading(false);
      }
    }, 1000); // Check every second

    // Timeout after 2 minutes
    setTimeout(() => {
      clearInterval(pollInterval);
      setLoading(false);
      loadData(); // Refresh anyway
    }, 120000);
  };

  const handlePanic = async () => {
    if (panicProcessing) return;
    setPanicProcessing(true);
    try {
      const res = await triggerPanicMode();
      if (res && res.status === "success") {
        alert(res.message || "Panic mode activated");
        const newLogs = await fetchLogs();
        setLogs(newLogs);
      } else {
        alert(res.message || "Failed to activate panic mode");
      }
    } catch (e) {
      alert("Error triggering panic mode");
    } finally {
      setPanicProcessing(false);
    }
  };

  const handleUnlockPanic = async () => {
    if (unlockProcessing) return;
    setUnlockProcessing(true);
    try {
      const res = await triggerUnlockPanicControl();
      if (res && res.status === "success") {
        alert(res.message || "Panic unlock activated");
        const newLogs = await fetchLogs();
        setLogs(newLogs);
      } else {
        alert(res.message || "Failed to unlock panic mode");
      }
    } catch (e) {
      alert("Error unlocking panic mode");
    } finally {
      setUnlockProcessing(false);
    }
  };

  const handleToggleBlock = async (mac) => {
    setProcessingId(mac);

    const result = await toggleDeviceBlock(mac);

    if (result && result.status === "success") {
      setDevices((prevDevices) =>
        prevDevices.map((device) =>
          device.mac === mac
            ? { ...device, isBlocked: result.isBlocked }
            : device
        )
      );

      if (selectedDevice && selectedDevice.mac === mac) {
        setSelectedDevice((prev) => ({
          ...prev,
          isBlocked: result.isBlocked,
        }));
      }

      const newLogs = await fetchLogs();
      setLogs(newLogs);
    }

    setProcessingId(null);
  };

  // Auto-scan functions
  const loadAutoScanStatus = async () => {
    const status = await getAutoScanStatus();
    setAutoScanEnabled(status.enabled);
    setAutoScanInterval(status.interval_minutes || 5);
  };

  const handleToggleAutoScan = async () => {
    if (autoScanEnabled) {
      const result = await stopAutoScan();
      if (result.status === "success") {
        setAutoScanEnabled(false);
        await loadData(); // Refresh data when stopping
      } else {
        alert("Failed to stop auto-scan: " + (result.message || "Unknown error"));
      }
    } else {
      const result = await startAutoScan(autoScanInterval);
      if (result.status === "success") {
        setAutoScanEnabled(true);
        // Start polling for new devices
        setTimeout(() => loadData(), 2000); // Initial refresh after 2 seconds
      } else {
        alert("Failed to start auto-scan: " + (result.message || "Unknown error"));
      }
    }
  };

  const generateQCReport = () => {
    const total = devices.length;
    const blocked = devices.filter(d => d.isBlocked || d.is_blocked).length;
    const highRisk = devices.filter(d => d.risk_score > 50).length;
    const timestamp = new Date().toLocaleString();

    let csvContent = "data:text/csv;charset=utf-8,";

    csvContent += "AEGIS SECURITY AUDIT REPORT\\n";
    csvContent += `Generated At,${timestamp}\\n`;
    csvContent += `Total Devices,${total}\\n`;
    csvContent += `Quarantined Devices,${blocked}\\n`;
    csvContent += `Critical Threats,${highRisk}\\n\\n`;

    csvContent += "DEVICE NAME,IP ADDRESS,MAC ADDRESS,OS,TYPE,RISK SCORE,OPEN PORTS,LATENCY,STATUS\\n";

    devices.forEach(d => {
      const status = (d.isBlocked || d.is_blocked) ? "BLOCKED" : (d.risk_score > 20 ? "VULNERABLE" : "SECURE");
      const latency = d.latency ? `${d.latency}ms` : "N/A";
      csvContent += `${d.vendor || d.name},${d.ip},${d.mac},${d.os_type || "Unknown"},${d.device_type || "unknown"},${d.risk_score}%,${d.open_ports || 0},${latency},${status}\\n`;
    });

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `Aegis_QC_Report_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  const getDeviceIcon = (type) => {
    const props = { size: 20, strokeWidth: 1.5 };
    switch (type) {
      case 'router': return <Router {...props} />;
      case 'laptop': return <Laptop {...props} />;
      case 'mobile': return <Smartphone {...props} />;
      case 'iot': return <Wifi {...props} />;
      case 'media': return <Activity {...props} />;
      case 'server': return <Server {...props} />;
      default: return <Server {...props} />;
    }
  };

  if (!user) {
    return <Login onLoginSuccess={(username) => setUser(username)} />;
  }

  return (
    <div className={`min-h-screen font-sans transition-colors duration-300 ${theme === 'dark' ? 'dark bg-zinc-950 text-zinc-200' : 'bg-gray-50 text-slate-900'} selection:bg-blue-100 dark:selection:bg-blue-900`}>

      {/* HEADER */}
      <header className="sticky top-0 z-40 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-md border-b border-gray-200 dark:border-zinc-800">
        <div className="max-w-5xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-8 h-8 bg-slate-900 dark:bg-white rounded-lg shadow-sm">
              <Shield size={16} className="text-white dark:text-black fill-current" />
            </div>
            <span className="font-semibold text-lg tracking-tight text-slate-900 dark:text-white">Aegis</span>
            <span className="text-[10px] text-emerald-500 font-bold uppercase tracking-wider">Sentry Mode Active</span>
          </div>

          <div className="flex items-center gap-3">
            {/* AUTO-SCAN TOGGLE */}
            <button
              onClick={handleToggleAutoScan}
              className={`flex items-center gap-2 px-3 py-2 text-xs font-medium rounded-lg border transition-all duration-200
                  ${autoScanEnabled
                  ? "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-900/20 dark:text-emerald-400 dark:border-emerald-800 animate-pulse"
                  : "bg-white text-slate-600 border-gray-200 dark:bg-zinc-900 dark:text-zinc-400 dark:border-zinc-700"}`}
            >
              <Zap size={14} className={autoScanEnabled ? "fill-current animate-spin" : ""} />
              {autoScanEnabled ? `Auto (${autoScanInterval}m)` : "Auto-Scan"}
            </button>

            {/* EMAIL TEST TOOL TOGGLE */}
            <button
              onClick={() => setShowEmailTest(!showEmailTest)}
              className={`flex items-center gap-2 px-3 py-2 text-xs font-medium rounded-lg border transition-all duration-200
                  ${showEmailTest
                  ? "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-900/20 dark:text-blue-400 dark:border-blue-800"
                  : "bg-white text-slate-600 border-gray-200 dark:bg-zinc-900 dark:text-zinc-400 dark:border-zinc-700"}`}
              title="Test Firebase Email"
            >
              🔧 Test Email
            </button>

            <button
              onClick={handlePanic}
              disabled={panicProcessing}
              className="flex items-center gap-2 px-3 py-2 text-xs font-bold text-white bg-red-600 hover:bg-red-700 rounded-lg shadow-sm transition-all"
            >
              <AlertTriangle size={14} /> {panicProcessing ? "Activating..." : "Panic"}
            </button>
            <button
              onClick={handleUnlockPanic}
              disabled={unlockProcessing}
              className="flex items-center gap-2 px-3 py-2 text-xs font-medium text-red-700 bg-red-50 hover:bg-red-100 rounded-lg border border-red-200 dark:text-red-400 dark:bg-red-900/20 dark:hover:bg-red-900/30 dark:border-red-800 transition-all"
            >
              <Lock size={14} /> {unlockProcessing ? "Unlocking..." : "Unlock Panic"}
            </button>
            <button
              onClick={handleScan}
              disabled={loading}
              className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg border transition-all duration-200
                  ${loading ? "bg-gray-50 text-gray-400 border-gray-200 cursor-not-allowed dark:bg-zinc-800 dark:border-zinc-700 dark:text-zinc-500"
                  : "bg-white text-slate-700 border-gray-200 hover:bg-gray-50 hover:shadow-sm dark:bg-zinc-900 dark:text-zinc-300 dark:border-zinc-700 dark:hover:bg-zinc-800"}`}
            >
              <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
              {loading ? "Scanning..." : "Scan"}
            </button>
            <button onClick={toggleTheme} className="p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:text-zinc-400 dark:hover:bg-zinc-800 transition-colors">
              {theme === "light" ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <button
              onClick={async () => {
                try {
                  await signOut(auth);
                  // Firebase onAuthStateChanged will handle cleanup
                } catch (error) {
                  console.error("Error signing out:", error);
                }
              }}
              className="p-2 rounded-lg text-gray-500 hover:bg-red-50 hover:text-red-600 dark:text-zinc-400 dark:hover:bg-red-900/20 dark:hover:text-red-400 transition-colors"
              title="Logout"
            >
              <X size={18} />
            </button>
          </div>
        </div>
      </header>

      {/* MAIN CONTENT */}
      <main className="max-w-5xl mx-auto px-6 py-8">

        {/* TABS */}
        <div className="flex items-center gap-6 mb-8 border-b border-gray-200 dark:border-zinc-800">
          <button onClick={() => setActiveTab("dashboard")} className={`pb-3 text-sm font-medium transition-all ${activeTab === 'dashboard' ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400' : 'text-slate-500 hover:text-slate-700 dark:text-zinc-500 dark:hover:text-zinc-300'}`}>Dashboard</button>
          <button onClick={() => setActiveTab("logs")} className={`pb-3 text-sm font-medium transition-all ${activeTab === 'logs' ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400' : 'text-slate-500 hover:text-slate-700 dark:text-zinc-500 dark:hover:text-zinc-300'}`}>Activity Logs</button>
        </div>

        {/* DASHBOARD TAB */}
        {activeTab === "dashboard" && (
          <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
            <div className="flex items-end justify-between mb-6">
              <div>
                <h1 className="text-xl font-medium text-slate-900 dark:text-white">Network Overview</h1>
                <p className="text-sm text-slate-500 dark:text-zinc-500 mt-1">{devices.length} Devices • {devices.filter(d => d.isBlocked || d.is_blocked).length} Blocked</p>
              </div>
              <button onClick={generateQCReport} className="text-xs font-medium text-slate-500 hover:text-blue-600 dark:text-zinc-500 dark:hover:text-blue-400 flex items-center gap-2 transition-colors border border-gray-200 dark:border-zinc-800 px-3 py-1.5 rounded-md hover:bg-gray-50 dark:hover:bg-zinc-800">
                <FileText size={14} /> Download QC Report
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {devices.map((device) => (
                <div
                  key={device.mac || device.id}
                  onClick={() => openDeviceModal(device)}
                  className={`group relative border rounded-xl p-5 cursor-pointer transition-all duration-200
                            ${(device.isBlocked || device.is_blocked)
                      ? "bg-gray-50 border-gray-200 opacity-75 grayscale dark:bg-zinc-900 dark:border-zinc-800"
                      : "bg-white dark:bg-zinc-900 border-gray-200 dark:border-zinc-800 hover:border-gray-300 dark:hover:border-zinc-600 hover:shadow-sm"}`}
                >
                  {device.harmful && <div className="absolute top-4 right-4 text-rose-500 text-xs font-bold uppercase">High Risk</div>}
                  <div className="flex justify-between items-start mb-4">
                    <div className="p-2.5 bg-gray-50 dark:bg-zinc-800 rounded-lg text-slate-600 dark:text-zinc-400">{getDeviceIcon(device.device_type)}</div>
                    <div className={`w-2 h-2 rounded-full mt-2 ${device.risk_score > 50 ? 'bg-rose-500' : device.risk_score > 20 ? 'bg-amber-400' : 'bg-emerald-500'}`}></div>
                  </div>
                  <h3 className="font-semibold text-slate-900 dark:text-white truncate pr-6">
                    {displayNameFor(device)}
                  </h3>
                  <p className="text-xs font-mono text-slate-400 dark:text-zinc-500 mt-1">{device.ip}</p>
                  <p className="text-xs text-slate-500 dark:text-zinc-500 mt-1">{device.os_type || device.hostname}</p>
                  {device.summary && (
                    <p className="text-xs text-slate-600 dark:text-zinc-400 mt-2">{device.summary}</p>
                  )}
                  <div className="flex items-center justify-between text-xs text-slate-500 dark:text-zinc-500 pt-4 mt-4 border-t border-gray-100 dark:border-zinc-800">
                    <span className={device.harmful ? "text-rose-600 font-medium" : ""}>
                      {device.harmful ? "High Risk Detected" : `${device.open_ports || 0} ports • ${device.latency ? device.latency + 'ms' : 'N/A'}`}
                    </span>
                    <ChevronRight size={14} className="text-gray-300 dark:text-zinc-600 group-hover:text-slate-600 dark:group-hover:text-white transition-colors" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* LOGS TAB */}
        {activeTab === "logs" && (
          <div className="bg-white dark:bg-zinc-900 rounded-xl border border-gray-200 dark:border-zinc-800 overflow-hidden animate-in fade-in slide-in-from-bottom-2 duration-300">
            <div className="p-4 border-b border-gray-200 dark:border-zinc-800 bg-gray-50/50 dark:bg-zinc-900/50">
              <h2 className="text-sm font-semibold text-slate-900 dark:text-white flex items-center gap-2"><History size={16} /> Audit Trail</h2>
            </div>
            <div className="divide-y divide-gray-100 dark:divide-zinc-800">
              {logs.map((log) => (
                <div key={log.id} className="p-4 flex gap-4 hover:bg-gray-50 dark:hover:bg-zinc-800/50 transition-colors">
                  <div className="w-20 text-xs text-slate-400 font-mono pt-0.5">{log.time}</div>
                  <div>
                    <p className={`text-sm font-medium ${log.type === 'danger' ? 'text-red-600 dark:text-red-400' : log.type === 'warning' ? 'text-amber-600 dark:text-amber-400' : 'text-slate-700 dark:text-zinc-300'}`}>
                      {log.event}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      {/* INSPECTOR MODAL */}
      {selectedDevice && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/20 dark:bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="bg-white dark:bg-zinc-900 w-full max-w-md rounded-2xl shadow-2xl overflow-hidden ring-1 ring-black/5 dark:ring-white/10">
            <div className="p-6 pb-0 flex justify-between items-start">
              <div>
                <h2 className="text-xl font-bold text-slate-900 dark:text-white">
                  {displayNameFor(selectedDevice)}
                </h2>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-sm text-slate-500 dark:text-zinc-400 font-mono">{selectedDevice.mac}</span>
                  {selectedDevice.harmful && <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-600 dark:bg-rose-900/30 dark:text-rose-400 uppercase">HIGH RISK</span>}
                </div>
              </div>
              <button onClick={() => setSelectedDevice(null)} className="p-1 rounded-full hover:bg-gray-100 dark:hover:bg-zinc-800 text-gray-400 transition-colors"><X size={20} /></button>
            </div>
            <div className="p-6 space-y-4">
              <div className="space-y-2">
                <label className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-zinc-500">
                  Device Label
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={nicknameDraft}
                    onChange={(e) => setNicknameDraft(e.target.value)}
                    placeholder="e.g. Living Room TV"
                    className="flex-1 px-3 py-2 text-sm rounded-lg border border-gray-200 dark:border-zinc-700 bg-white dark:bg-zinc-950 text-slate-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-blue-500/70"
                  />
                  <button
                    type="button"
                    onClick={async () => {
                      if (!selectedDevice) return;
                      const mac = selectedDevice.mac;
                      const result = await updateDeviceNickname(mac, nicknameDraft || "");
                      if (result && result.status === "success") {
                        // Update local lists
                        setDevices((prev) =>
                          prev.map((d) =>
                            d.mac === mac ? { ...d, nickname: nicknameDraft || "" } : d
                          )
                        );
                        setSelectedDevice((prev) =>
                          prev ? { ...prev, nickname: nicknameDraft || "" } : prev
                        );
                      }
                    }}
                    className="px-3 py-2 text-xs font-medium rounded-lg bg-slate-900 text-white hover:bg-slate-800 dark:bg-white dark:text-black dark:hover:bg-gray-200 transition-colors"
                  >
                    Save
                  </button>
                </div>
              </div>
              {!selectedDevice.harmful ? (
                <>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div className="p-3 bg-gray-50 dark:bg-zinc-800/50 rounded-lg">
                      <div className="text-xs text-slate-500 dark:text-zinc-500 mb-1">OS Type</div>
                      <div className="font-medium text-slate-900 dark:text-white">{selectedDevice.os_type || "Unknown"}</div>
                    </div>
                    <div className="p-3 bg-gray-50 dark:bg-zinc-800/50 rounded-lg">
                      <div className="text-xs text-slate-500 dark:text-zinc-500 mb-1">Device Type</div>
                      <div className="font-medium text-slate-900 dark:text-white capitalize">{selectedDevice.device_type || "unknown"}</div>
                    </div>
                    <div className="p-3 bg-gray-50 dark:bg-zinc-800/50 rounded-lg">
                      <div className="text-xs text-slate-500 dark:text-zinc-500 mb-1">Open Ports</div>
                      <div className="font-medium text-slate-900 dark:text-white">{selectedDevice.open_ports || 0}</div>
                    </div>
                    <div className="p-3 bg-gray-50 dark:bg-zinc-800/50 rounded-lg">
                      <div className="text-xs text-slate-500 dark:text-zinc-500 mb-1">Latency</div>
                      <div className="font-medium text-slate-900 dark:text-white">{selectedDevice.latency ? `${selectedDevice.latency}ms` : "N/A"}</div>
                    </div>
                  </div>
                  <div className="p-4 bg-gray-50 dark:bg-zinc-800/50 rounded-xl border border-gray-100 dark:border-zinc-800">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-zinc-500">Risk Assessment</span>
                      <span className={`text-sm font-bold ${selectedDevice.risk_score > 50 ? 'text-rose-600' : selectedDevice.risk_score > 20 ? 'text-amber-600' : 'text-emerald-600'}`}>{selectedDevice.risk_score}%</span>
                    </div>
                    <p className="text-sm text-slate-700 dark:text-zinc-300 leading-relaxed">{selectedDevice.summary || selectedDevice.port_summary || "No open ports detected"}</p>
                  </div>
                </>
              ) : (
                <div className="p-6 bg-rose-50 dark:bg-rose-900/10 rounded-xl border border-rose-100 dark:border-rose-900/30 text-center">
                  <AlertTriangle className="mx-auto h-8 w-8 text-rose-500 mb-2" />
                  <h3 className="text-rose-700 dark:text-rose-400 font-medium">High Risk Device</h3>
                  <p className="text-sm text-rose-600/80 dark:text-rose-400/70 mt-1">
                    Many open ports or critical services detected. Review configuration.
                  </p>
                </div>
              )}
            </div>
            <div className="p-4 bg-gray-50 dark:bg-zinc-950/50 border-t border-gray-100 dark:border-zinc-800 flex gap-3">
              <button onClick={() => setSelectedDevice(null)} className="flex-1 py-2.5 bg-slate-900 hover:bg-slate-800 dark:bg-white dark:hover:bg-gray-200 dark:text-black text-white font-medium rounded-lg transition-colors text-sm">Done</button>
            </div>
          </div>
        </div>
      )}
      {showEmailTest && <FirebaseEmailTest />}
      <Chatbot />
    </div>
  );
}

export default App;
