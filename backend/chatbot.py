import re
from database import get_all_devices, get_recent_logs, get_device_count
from ai_detector import get_ai_detector

class AegisChatbot:
    """
    Expert system chatbot for Aegis that provides intelligence about the network status.
    """
    def __init__(self):
        self.context_patterns = [
            (r'(how many|count).*devices', self._get_device_count),
            (r'(devices connected|connected devices)', self._get_device_count),
            (r'(how many|count).*blocked', self._get_blocked_count),
            (r'(what|list).*blocked', self._list_blocked_devices),
            (r'(high risk|dangerous|threat).*devices', self._get_high_risk_devices),
            (r'(status|info).* ([\\d\\.]+)', self._get_device_status),
            (r'(is|are|any).*scanning', self._get_scan_status),
            (r'(auto.*scan|automatic scan).* (status|on|off)', self._get_auto_scan_info),
            (r'(recent|what).*logs', self._get_recent_logs_text),
            (r'(threat|danger|harmful|risky|critical).*', self._get_threat_summary),
            (r'(summary|overview).*network', self._get_threat_summary),
            (r'(recommendation|secure|improve|fix).*', self._get_recommendations),
            (r'(help|what can you do)', self._get_help),
            (r'(hello|hi|hey)', lambda _: "Hello! I'm your Aegis Assistant. How can I help you with your network security today?"),
            (r'thank', lambda _: "You're welcome! Stay safe."),
        ]

    def ask(self, query: str) -> str:
        query = query.lower()
        
        for pattern, handler in self.context_patterns:
            match = re.search(pattern, query)
            if match:
                return handler(match)
        
        return self._generate_fallback_response(query)

    def _get_device_count(self, _):
        count = get_device_count()
        return f"There are currently {count} devices detected on your network."

    def _get_blocked_count(self, _):
        devices = get_all_devices()
        blocked = [d for d in devices if d.get('is_blocked') or d.get('isBlocked')]
        count = len(blocked)
        if count == 0:
            return "No devices are currently blocked. Your network is fully accessible."
        return f"You have {count} devices currently blocked/quarantined."

    def _list_blocked_devices(self, _):
        devices = get_all_devices()
        blocked = [d for d in devices if d.get('is_blocked') or d.get('isBlocked')]
        if not blocked:
            return "There are no blocked devices at the moment."
        
        names = [f"{d.get('vendor') or d.get('nickname') or d.get('ip')} ({d.get('ip')})" for d in blocked]
        return "The following devices are blocked: " + ", ".join(names)

    def _get_high_risk_devices(self, _):
        devices = get_all_devices()
        high_risk = [d for d in devices if (d.get('risk_score') or 0) > 50]
        if not high_risk:
            return "Great news! I didn't find any high-risk devices on your network."
        
        names = [f"{d.get('vendor') or d.get('ip')} (Score: {d.get('risk_score')}%)" for d in high_risk]
        return f"Warning! I found {len(high_risk)} high-risk devices: " + ", ".join(names)
    
    def _get_threat_summary(self, _):
        devices = get_all_devices()
        ai = get_ai_detector()
        harmful = []
        for d in devices:
            try:
                ev = ai.evaluate_harmful_device(d)
                if ev.get('harmful'):
                    harmful.append((d, ev))
            except Exception:
                pass
        if not harmful:
            return "I don't see harmful indicators right now. No critical services exposed."
        harmful_sorted = sorted(harmful, key=lambda x: x[0].get('risk_score', 0), reverse=True)
        top = harmful_sorted[:3]
        names = []
        for d, ev in top:
            names.append(f"{d.get('vendor') or d.get('hostname') or d.get('ip')} (Score: {d.get('risk_score', 0)}%)")
        total = len(harmful)
        crit = sum(1 for _, ev in harmful if ev.get('has_critical_ports'))
        return f"Detected {total} harmful devices, {crit} with critical services. Top risks: " + ", ".join(names)

    def _get_device_status(self, match):
        ip = match.group(2)
        devices = get_all_devices()
        device = next((d for d in devices if d.get('ip') == ip), None)
        
        if not device:
            return f"I couldn't find any device with the IP address {ip} in my database."
        
        status = "Blocked" if (device.get('is_blocked') or device.get('isBlocked')) else "Online"
        risk = device.get('risk_score', 0)
        vendor = device.get('vendor', 'Unknown')
        
        return f"Status for {ip}: {status}. Vendor: {vendor}. Risk Score: {risk}%. OS: {device.get('os_type', 'Unknown')}."

    def _get_scan_status(self, _):
        from main import get_scan_status_safe
        status = get_scan_status_safe()
        if status.get("is_scanning"):
            return "Yes, a network scan is currently in progress."
        return "No scan is currently running. You can start one from the dashboard."

    def _get_auto_scan_info(self, match):
        from auto_scanner import get_auto_scan_status
        status = get_auto_scan_status()
        enabled = "enabled" if status.get("enabled") else "disabled"
        interval = status.get("interval_minutes", 5)
        return f"Automatic scanning is currently {enabled}. When enabled, it runs every {interval} minutes."

    def _get_recent_logs_text(self, _):
        logs = get_recent_logs()
        if not logs:
            return "I don't see any recent activity logs."
        
        latest = logs[0]
        return f"The most recent activity was at {latest.get('time')}: {latest.get('event')}. I have {len(logs)} logs in my history."
    
    def _get_recommendations(self, _):
        devices = get_all_devices()
        risky = [d for d in devices if (d.get('risk_score') or 0) > 50 or (d.get('open_ports_count') or 0) > 5]
        if not risky:
            return "Everything looks stable. Keep firmware updated and avoid exposing services to the internet."
        return ("Recommendations:\n"
                "- Disable Telnet, SMB, RDP, VNC where not needed\n"
                "- Reduce exposed ports and close unused services\n"
                "- Update device firmware and change default credentials\n"
                "- Enable automatic scanning to monitor changes")

    def _get_help(self, _):
        return ("I can help you monitor your network. You can ask me things like:\n"
                "- How many devices are on my network?\n"
                "- List all blocked devices\n"
                "- Show me high risk devices\n"
                "- What is the status of 192.168.1.5?\n"
                "- Are there any threats?")

    def _generate_fallback_response(self, query):
        if "risk" in query or "threat" in query or "safe" in query:
            return self._get_threat_summary(None)
        if "status" in query or "network" in query:
            return f"The network is active with {get_device_count()} devices. Use 'help' to see specific commands I understand."
        
        return "I'm not sure I understand that. Try asking about your device count, blocked devices, or specific IP statuses!"

# Singleton
_chatbot = AegisChatbot()

def get_chatbot():
    return _chatbot
