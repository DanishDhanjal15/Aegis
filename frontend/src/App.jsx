import React, { useEffect, useState } from "react";
import { fetchDevices, fetchLogs, triggerScan, toggleDeviceBlock } from "./api";
import { 
  Sun, Moon, RefreshCw, Shield, AlertTriangle,
  ChevronRight, X, Laptop, Smartphone, Router, Server,
  Ban, History, FileText, CheckCircle2, Lock
} from "lucide-react";

function App() {
  const [devices, setDevices] = useState([]);
  const [logs, setLogs] = useState([]); 
  const [loading, setLoading] = useState(false);
  const [processingId, setProcessingId] = useState(null); // Tracks MAC of device being processed
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [activeTab, setActiveTab] = useState("dashboard");
  const [theme, setTheme] = useState(localStorage.getItem("theme") || "light");
  const [panicLoading, setPanicLoading] = useState(false);

  useEffect(() => {
    if (theme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
    localStorage.setItem("theme", theme);
  }, [theme]);

  const toggleTheme = () => setTheme(theme === "light" ? "dark" : "light");

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    const [devicesData, logsData] = await Promise.all([
      fetchDevices(),
      fetchLogs()
    ]);
    setDevices(devicesData || []);
    setLogs(logsData || []);
  };

  const handleScan = async () => {
    setLoading(true);
    await triggerScan();
    await loadData();
    setTimeout(() => setLoading(false), 800);
  };

  // --- PANIC MODE LOGIC ---
  const handlePanic = async () => {
      const confirm = window.confirm("🚨 EMERGENCY: Are you sure you want to block ALL devices?");
      if (!confirm) return;

      setPanicLoading(true);
      await triggerPanicMode();
      await loadData(); // Refresh list to show locks
      setPanicLoading(false);
      alert("Panic Mode Activated: All devices blocked.");
  };

  // --- BLOCK MODE LOGIC ---
  const handleToggleBlock = async (mac) => {
    setProcessingId(mac); // Start loading spinner using MAC

    // 1. Call Backend
    const result = await toggleDeviceBlock(mac);

    if (result && result.status === "success") {
      // 2. INSTANTLY Update the Main Device List
      // This ensures the "Blocked Devices" counter at the top updates immediately
      setDevices((prevDevices) =>
        prevDevices.map((device) =>
          device.mac === mac
            ? { ...device, isBlocked: result.isBlocked }
            : device
        )
      );

      // 3. INSTANTLY Update the Selected Device Modal
      // This ensures the button text changes from "Block" to "Restore" immediately
      if (selectedDevice && selectedDevice.mac === mac) {
        setSelectedDevice((prev) => ({
          ...prev,
          isBlocked: result.isBlocked,
        }));
      }

      // 4. Refresh logs in the background to show the new event
      const newLogs = await fetchLogs();
      setLogs(newLogs);
    }

    setProcessingId(null); // Stop loading
  };

  // --- REAL QC REPORT GENERATOR (CSV) ---
  const generateQCReport = () => {
    // 1. Calculate Stats
    const total = devices.length;
    const blocked = devices.filter(d => d.isBlocked).length;
    const highRisk = devices.filter(d => d.risk_score > 50).length;
    const timestamp = new Date().toLocaleString();

    // 2. Build CSV Content
    let csvContent = "data:text/csv;charset=utf-8,";
    
    // Header Section
    csvContent += "AEGIS SECURITY AUDIT REPORT\n";
    csvContent += `Generated At,${timestamp}\n`;
    csvContent += `Total Devices,${total}\n`;
    csvContent += `Quarantined Devices,${blocked}\n`;
    csvContent += `Critical Threats,${highRisk}\n\n`;

    // Table Header
    csvContent += "ID,DEVICE NAME,IP ADDRESS,MAC ADDRESS,TYPE,RISK SCORE,STATUS,ACTION REQUIRED\n";

    // Table Rows
    devices.forEach(d => {
        const status = d.isBlocked ? "BLOCKED" : (d.risk_score > 20 ? "VULNERABLE" : "SECURE");
        const action = d.action ? d.action.replace(/,/g, " ") : "None"; // Escape commas
        csvContent += `${d.id},${d.name},${d.ip},${d.mac},${d.type},${d.risk_score}%,${status},${action}\n`;
    });

    // 3. Trigger Download
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
      default: return <Server {...props} />;
    }
  };

  return (
    <div className="min-h-screen font-sans bg-gray-50 dark:bg-zinc-950 text-slate-900 dark:text-zinc-200 transition-colors duration-300 selection:bg-blue-100 dark:selection:bg-blue-900">
      
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
              {/* PANIC BUTTON */}
              <button 
                onClick={handlePanic}
                disabled={panicLoading}
                className="flex items-center gap-2 px-3 py-2 text-xs font-bold text-white bg-red-600 hover:bg-red-700 rounded-lg shadow-sm transition-all animate-pulse hover:animate-none"
              >
                  <AlertTriangle size={14} /> {panicLoading ? "LOCKING..." : "PANIC LOCK"}
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
                        <p className="text-sm text-slate-500 dark:text-zinc-500 mt-1">{devices.length} Devices • {devices.filter(d => d.isBlocked).length} Blocked</p>
                    </div>
                    {/* EXPORT BUTTON */}
                    <button onClick={generateQCReport} className="text-xs font-medium text-slate-500 hover:text-blue-600 dark:text-zinc-500 dark:hover:text-blue-400 flex items-center gap-2 transition-colors border border-gray-200 dark:border-zinc-800 px-3 py-1.5 rounded-md hover:bg-gray-50 dark:hover:bg-zinc-800">
                        <FileText size={14} /> Download QC Report
                    </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {devices.map((device) => (
                        <div 
                          key={device.mac || device.id} 
                          onClick={() => setSelectedDevice(device)}
                          className={`group relative border rounded-xl p-5 cursor-pointer transition-all duration-200
                            ${device.isBlocked 
                                ? "bg-gray-50 border-gray-200 opacity-75 grayscale dark:bg-zinc-900 dark:border-zinc-800" 
                                : "bg-white dark:bg-zinc-900 border-gray-200 dark:border-zinc-800 hover:border-gray-300 dark:hover:border-zinc-600 hover:shadow-sm"}`}
                        >
                            {device.isBlocked && <div className="absolute top-4 right-4 text-red-500"><Lock size={18} /></div>}
                            <div className="flex justify-between items-start mb-4">
                                <div className="p-2.5 bg-gray-50 dark:bg-zinc-800 rounded-lg text-slate-600 dark:text-zinc-400">{getDeviceIcon(device.type)}</div>
                                {!device.isBlocked && <div className={`w-2 h-2 rounded-full mt-2 ${device.risk_score > 50 ? 'bg-rose-500' : device.risk_score > 20 ? 'bg-amber-400' : 'bg-emerald-500'}`}></div>}
                            </div>
                            <h3 className="font-semibold text-slate-900 dark:text-white truncate pr-6">{device.name || device.vendor}</h3>
                            <p className="text-xs font-mono text-slate-400 dark:text-zinc-500 mt-1 mb-4">{device.ip}</p>
                            <div className="flex items-center justify-between text-xs text-slate-500 dark:text-zinc-500 pt-4 border-t border-gray-100 dark:border-zinc-800">
                                <span className={device.isBlocked ? "text-red-500 font-medium" : ""}>{device.isBlocked ? "Firewall Rule Active" : `Risk Score: ${device.risk_score}%`}</span>
                                <ChevronRight size={14} className="text-gray-300 dark:text-zinc-600 group-hover:text-slate-600 dark:group-hover:text-white transition-colors"/>
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
                        <h2 className="text-xl font-bold text-slate-900 dark:text-white">{selectedDevice.name}</h2>
                        <div className="flex items-center gap-2 mt-1">
                             <span className="text-sm text-slate-500 dark:text-zinc-400 font-mono">{selectedDevice.mac}</span>
                            {selectedDevice.isBlocked && <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400 uppercase">BLOCKED</span>}
                        </div>
                    </div>
                    <button onClick={() => setSelectedDevice(null)} className="p-1 rounded-full hover:bg-gray-100 dark:hover:bg-zinc-800 text-gray-400 transition-colors"><X size={20} /></button>
                </div>
                <div className="p-6 space-y-6">
                    {!selectedDevice.isBlocked ? (
                        <>
                            <div className="p-4 bg-gray-50 dark:bg-zinc-800/50 rounded-xl border border-gray-100 dark:border-zinc-800">
                                <div className="flex justify-between items-center mb-2">
                                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-zinc-500">Status</span>
                                    <span className={`text-sm font-bold ${selectedDevice.risk_score > 20 ? 'text-rose-600' : 'text-emerald-600'}`}>{selectedDevice.risk_score > 20 ? 'Vulnerable' : 'Secure'}</span>
                                </div>
                                <p className="text-sm text-slate-700 dark:text-zinc-300 leading-relaxed">{selectedDevice.reason || "Device appears consistent with known signatures."}</p>
                            </div>
                        </>
                    ) : (
                        <div className="p-6 bg-red-50 dark:bg-red-900/10 rounded-xl border border-red-100 dark:border-red-900/30 text-center">
                            <Lock className="mx-auto h-8 w-8 text-red-500 mb-2" />
                            <h3 className="text-red-700 dark:text-red-400 font-medium">Device Quarantined</h3>
                            <p className="text-sm text-red-600/80 dark:text-red-400/70 mt-1">
                                Firewall rule applied via ARP spoofing. Traffic dropped.
                            </p>
                        </div>
                    )}
                </div>
                <div className="p-4 bg-gray-50 dark:bg-zinc-950/50 border-t border-gray-100 dark:border-zinc-800 flex gap-3">
                    <button 
                      // ✅ UPDATED: Always uses MAC address
                      onClick={() => handleToggleBlock(selectedDevice.mac)} 
                      disabled={processingId === selectedDevice.mac}
                      className={`flex-1 py-2.5 font-medium rounded-lg transition-colors text-sm flex items-center justify-center gap-2 
                      ${selectedDevice.isBlocked 
                          ? "bg-white border border-gray-300 text-slate-700 hover:bg-gray-50 dark:bg-zinc-800 dark:border-zinc-700 dark:text-zinc-200" 
                          : "bg-red-50 text-red-600 hover:bg-red-100 dark:bg-red-900/20 dark:text-red-400 dark:hover:bg-red-900/30 border border-transparent"}
                      ${processingId === selectedDevice.mac ? "opacity-70 cursor-wait" : ""}`}
                    >
                        {processingId === selectedDevice.mac ? (
                            <><RefreshCw size={16} className="animate-spin"/> Applying...</>
                        ) : selectedDevice.isBlocked ? (
                            <><CheckCircle2 size={16} /> Restore Access</>
                        ) : (
                            <><Ban size={16} /> Block Access</>
                        )}
                    </button>
                    <button onClick={() => setSelectedDevice(null)} className="flex-1 py-2.5 bg-slate-900 hover:bg-slate-800 dark:bg-white dark:hover:bg-gray-200 dark:text-black text-white font-medium rounded-lg transition-colors text-sm">Done</button>
                </div>
            </div>
        </div>
      )}
    </div>
  );
}

export default App;