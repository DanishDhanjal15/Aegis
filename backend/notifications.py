from twilio.rest import Client
import logging

# --- CONFIGURATION (Get these from Twilio Console) ---
TWILIO_ACCOUNT_SID = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" # <--- Paste SID here
TWILIO_AUTH_TOKEN = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"   # <--- Paste Auth Token here
TWILIO_FROM_NUMBER = "+1234567890"                    # <--- Your Twilio Number
USER_PHONE_NUMBER = "+1987654321"                      # <--- Your Personal Mobile Number

# Initialize Client
try:
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
except Exception as e:
    print(f"⚠️ Twilio Config Error: {e}")
    client = None

# Cache to prevent spamming SMS for the same device repeatedly
sent_alerts = set()

def send_sms_alert(device):
    """
    Sends an SMS if a device is Medium or Critical risk.
    """
    ip = device['ip']
    risk = device['risk_score']
    
    # 1. Check if we already alerted about this IP to avoid SMS spam
    if ip in sent_alerts:
        return

    # 2. Define Alert Level
    if risk >= 75:
        level = "🚨 CRITICAL ALERT"
    elif risk >= 40:
        level = "⚠️ WARNING"
    else:
        return # Do not alert for low risk

    # 3. Construct Message
    body_text = (
        f"{level}: Security Threat Detected!\n"
        f"Device: {device['vendor']}\n"
        f"IP: {ip}\n"
        f"Risk Score: {risk}%\n"
        f"Open Ports: {device['hostname']}\n"
        f"Action: Investigate Immediately."
    )

    # 4. Send via Twilio
    if client:
        try:
            message = client.messages.create(
                body=body_text,
                from_=TWILIO_FROM_NUMBER,
                to=USER_PHONE_NUMBER
            )
            print(f"📨 SMS Sent to {USER_PHONE_NUMBER}: {message.sid}")
            sent_alerts.add(ip) # Add to cache so we don't send again this session
        except Exception as e:
            print(f"❌ Failed to send SMS: {e}")
    else:
        print("❌ Twilio client not initialized. Check credentials.")