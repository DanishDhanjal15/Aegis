const API_URL = "http://localhost:8000";

// Helper function to get auth headers
const getAuthHeaders = () => {
  const token = localStorage.getItem("aegis_token");
  return {
    "Content-Type": "application/json",
    ...(token && { "Authorization": `Bearer ${token}` })
  };
};

export const fetchDevices = async () => {
  try {
    const response = await fetch(`${API_URL}/api/devices`, {
      headers: getAuthHeaders()
    });
    return await response.json();
  } catch (error) {
    console.error("Error fetching devices:", error);
    return [];
  }
};

export const fetchLogs = async () => {
  try {
    const response = await fetch(`${API_URL}/api/logs`);
    return await response.json();
  } catch (error) {
    console.error("Error fetching logs:", error);
    return [];
  }
};

export const triggerScan = async () => {
  try {
    const response = await fetch(`${API_URL}/api/scan`, { method: 'POST' });
    return await response.json();
  } catch (error) {
    console.error("Error triggering scan:", error);
    return { status: "error" };
  }
};

export const getScanStatus = async () => {
  try {
    const response = await fetch(`${API_URL}/api/scan/status`);
    return await response.json();
  } catch (error) {
    console.error("Error getting scan status:", error);
    return { is_scanning: false };
  }
};

export const forceScan = async () => {
  try {
    await fetch(`${API_URL}/api/scan/force`, { method: 'POST' });
  } catch (error) {
    console.error("Error triggering force scan:", error);
  }
};

export const toggleDeviceBlock = async (deviceId) => {
  // Guard clause: stop if ID is missing
  if (!deviceId) {
    console.error("Error: toggleDeviceBlock called with undefined or null deviceId");
    return;
  }

  try {
    const response = await fetch(`${API_URL}/api/device/${deviceId}/block`, { method: 'POST' });
    return await response.json();
  } catch (error) {
    console.error("Error toggling block:", error);
  }
};

export const updateDeviceNickname = async (deviceId, nickname) => {
  if (!deviceId) {
    console.error("Error: updateDeviceNickname called with undefined or null deviceId");
    return;
  }

  try {
    const params = new URLSearchParams({ nickname });
    const response = await fetch(
      `${API_URL}/api/device/${encodeURIComponent(deviceId)}/nickname?${params.toString()}`,
      { method: "POST" }
    );
    return await response.json();
  } catch (error) {
    console.error("Error updating nickname:", error);
    return { status: "error" };
  }
};

export const triggerPanicMode = async () => {
  try {
    const response = await fetch(`${API_URL}/api/panic`, { method: 'POST' });
    return await response.json();
  } catch (error) {
    console.error("Error fetching devices:", error);
    return [];
  }
};

export const triggerUnlockPanicControl = async () => {
  try {
    const response = await fetch(`${API_URL}/api/panic/unlock`, { method: 'POST' });
    return await response.json();
  } catch (error) {
    console.error("Error unlocking panic control:", error);
    return { status: "error" };
  }
};

export const trainAI = async () => {
  try {
    const response = await fetch(`${API_URL}/api/ai/train`, { method: "POST" });
    return await response.json();
  } catch (error) {
    console.error("Error training AI:", error);
    return { status: "error" };
  }
};

// Auto-scan API functions
export const startAutoScan = async (intervalMinutes = 5) => {
  try {
    const response = await fetch(`${API_URL}/api/auto-scan/start?interval_minutes=${intervalMinutes}`, { method: 'POST' });
    return await response.json();
  } catch (error) {
    console.error("Error starting auto-scan:", error);
    return { status: "error" };
  }
};

export const stopAutoScan = async () => {
  try {
    const response = await fetch(`${API_URL}/api/auto-scan/stop`, { method: 'POST' });
    return await response.json();
  } catch (error) {
    console.error("Error stopping auto-scan:", error);
    return { status: "error" };
  }
};

export const getAutoScanStatus = async () => {
  try {
    const response = await fetch(`${API_URL}/api/auto-scan/status`);
    return await response.json();
  } catch (error) {
    console.error("Error getting auto-scan status:", error);
    return { enabled: false, interval_minutes: 5 };
  }
};

export const sendMessageToChatbot = async (message) => {
  try {
    const response = await fetch(`${API_URL}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    return await response.json();
  } catch (error) {
    console.error("Error sending message to chatbot:", error);
    return { reply: "Sorry, I'm having trouble connecting to the Aegis server right now." };
  }
};

// Firebase authentication is now handled in Login.jsx
// These functions are no longer needed
