const API_URL = "http://localhost:8000";

export const fetchDevices = async () => {
  try {
    const response = await fetch(`${API_URL}/api/devices`);
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
    await fetch(`${API_URL}/api/scan`, { method: 'POST' });
  } catch (error) {
    console.error("Error triggering scan:", error);
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

export const triggerPanicMode = async () => {
  try {
    const response = await fetch(`${API_URL}/api/panic`, { method: 'POST' });
    return await response.json();
  } catch (error) {
    console.error("Error fetching devices:", error);
    return [];
  }
};