"""
AI-Powered Device Detection Module

Uses machine learning and pattern recognition to automatically detect:
- Device names (intelligent naming)
- OS types (enhanced detection)
- Device types (ML classification)
- Device models/brands
"""

import re
import json
import pickle
import os
from typing import Dict, List, Optional, Tuple
from collections import Counter
import numpy as np

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import LabelEncoder
    from sklearn.model_selection import train_test_split
    import pandas as pd
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("⚠️ scikit-learn/pandas not available. AI features will use rule-based fallbacks.")


class AIDeviceDetector:
    """
    AI-powered device detection system that learns from network patterns
    and uses ML models for classification.
    """
    
    def __init__(self, model_dir="backend/models"):
        self.model_dir = model_dir
        self.device_classifier = None
        self.os_classifier = None
        self.label_encoders = {}
        self.pattern_cache = {}
        self.learning_data = []
        
        # Ensure model directory exists
        os.makedirs(model_dir, exist_ok=True)
        
        # Load existing models if available
        self._load_models()
        
        # Initialize with rule-based fallbacks if ML not available
        if not ML_AVAILABLE:
            print("📊 Using rule-based AI detection (ML models will be created after training)")
    
    def _load_models(self):
        """Load pre-trained ML models if they exist."""
        try:
            device_model_path = os.path.join(self.model_dir, "device_classifier.pkl")
            os_model_path = os.path.join(self.model_dir, "os_classifier.pkl")
            encoders_path = os.path.join(self.model_dir, "label_encoders.pkl")
            
            if os.path.exists(device_model_path) and ML_AVAILABLE:
                with open(device_model_path, 'rb') as f:
                    self.device_classifier = pickle.load(f)
                print("✅ Loaded device classifier model")
            
            if os.path.exists(os_model_path) and ML_AVAILABLE:
                with open(os_model_path, 'rb') as f:
                    self.os_classifier = pickle.load(f)
                print("✅ Loaded OS classifier model")
            
            if os.path.exists(encoders_path) and ML_AVAILABLE:
                with open(encoders_path, 'rb') as f:
                    self.label_encoders = pickle.load(f)
        except Exception as e:
            print(f"⚠️ Could not load ML models: {e}. Using rule-based detection.")
    
    def _save_models(self):
        """Save trained ML models to disk."""
        if not ML_AVAILABLE:
            return
        
        try:
            device_model_path = os.path.join(self.model_dir, "device_classifier.pkl")
            os_model_path = os.path.join(self.model_dir, "os_classifier.pkl")
            encoders_path = os.path.join(self.model_dir, "label_encoders.pkl")
            
            if self.device_classifier:
                with open(device_model_path, 'wb') as f:
                    pickle.dump(self.device_classifier, f)
            
            if self.os_classifier:
                with open(os_model_path, 'wb') as f:
                    pickle.dump(self.os_classifier, f)
            
            if self.label_encoders:
                with open(encoders_path, 'wb') as f:
                    pickle.dump(self.label_encoders, f)
            
            print("💾 Saved ML models to disk")
        except Exception as e:
            print(f"⚠️ Could not save models: {e}")
    
    def extract_features(self, device_data: Dict) -> np.ndarray:
        """
        Extract numerical features from device data for ML models.
        
        Features:
        - MAC vendor encoding
        - Port presence (binary features for common ports)
        - TTL value
        - Hostname patterns
        - Port count
        - Risk score
        """
        features = []
        
        # MAC vendor encoding (first 3 octets as numeric)
        mac = device_data.get('mac', '00:00:00:00:00:00')
        mac_parts = mac.split(':')
        if len(mac_parts) >= 3:
            try:
                features.append(int(mac_parts[0], 16))
                features.append(int(mac_parts[1], 16))
                features.append(int(mac_parts[2], 16))
            except:
                features.extend([0, 0, 0])
        else:
            features.extend([0, 0, 0])
        
        # Port features (binary for common ports)
        open_ports = device_data.get('open_ports', [])
        
        # Handle different data types: list, int, float, or None
        if open_ports is None:
            open_ports = []
        elif isinstance(open_ports, (float, int)):
            # If it's a count or NaN, create empty list (we don't know which ports)
            open_ports = []
        elif not isinstance(open_ports, list):
            # Try to convert to list if it's a string representation
            try:
                if isinstance(open_ports, str):
                    # Try to parse string representation
                    open_ports = []
                else:
                    open_ports = []
            except:
                open_ports = []
        
        # Ensure it's a list
        if not isinstance(open_ports, list):
            open_ports = []
        
        common_ports = [22, 80, 443, 3389, 5900, 3306, 5432, 1883, 32400, 8080]
        for port in common_ports:
            features.append(1 if port in open_ports else 0)
        
        # Port count
        port_count = len(open_ports) if isinstance(open_ports, list) else device_data.get('open_ports_count', device_data.get('open_ports', 0))
        if isinstance(port_count, (float, int)):
            port_count = int(port_count) if not (isinstance(port_count, float) and np.isnan(port_count)) else 0
        else:
            port_count = 0
        features.append(min(port_count, 50))  # Cap at 50
        
        # Risk score
        features.append(device_data.get('risk_score', 0))
        
        # TTL (if available)
        ttl = device_data.get('ttl', 64)
        features.append(ttl)
        
        # Hostname patterns (length, contains numbers, contains dashes)
        hostname = device_data.get('hostname', '')
        features.append(len(hostname))
        features.append(1 if any(c.isdigit() for c in hostname) else 0)
        features.append(1 if '-' in hostname else 0)
        features.append(1 if hostname.lower().startswith('android') else 0)
        features.append(1 if hostname.lower().startswith('iphone') else 0)
        features.append(1 if hostname.lower().startswith('ipad') else 0)
        
        return np.array(features)
    
    def detect_os_ai(self, device_data: Dict) -> str:
        """
        AI-powered OS detection using ML model + pattern matching.
        """
        # Use ML model if available
        if self.os_classifier and ML_AVAILABLE:
            try:
                features = self.extract_features(device_data).reshape(1, -1)
                os_prediction = self.os_classifier.predict(features)[0]
                if os_prediction != "Unknown":
                    return os_prediction
            except Exception as e:
                pass
        
        # Fallback to enhanced pattern matching
        return self._detect_os_patterns(device_data)
    
    def _detect_os_patterns(self, device_data: Dict) -> str:
        """Enhanced OS detection using pattern matching."""
        hostname = str(device_data.get('hostname', '')).lower()
        vendor = str(device_data.get('vendor', '')).lower()
        ttl = device_data.get('ttl', 64)
        open_ports = device_data.get('open_ports', [])
        
        # Windows detection
        if any(x in hostname for x in ['windows', 'desktop', 'pc-', 'win-']):
            return "Windows"
        if 3389 in open_ports or 445 in open_ports:  # RDP or SMB
            if ttl <= 128:
                return "Windows"
        
        # Linux detection
        if any(x in hostname for x in ['linux', 'ubuntu', 'debian', 'raspberry']):
            return "Linux"
        if ttl <= 64 and 22 in open_ports:  # SSH
            return "Linux/Unix"
        
        # macOS detection
        if any(x in hostname for x in ['macbook', 'imac', 'mac-']):
            return "macOS"
        if 'apple' in vendor and ttl <= 64:
            return "macOS"
        
        # iOS detection
        if any(x in hostname for x in ['iphone', 'ipad', 'ipod']):
            return "iOS"
        if 'apple' in vendor and any(x in hostname for x in ['ios', 'mobile']):
            return "iOS"
        
        # Android detection
        if 'android' in hostname:
            return "Android"
        if any(x in vendor.lower() for x in ['samsung', 'google', 'xiaomi', 'huawei']):
            if 'mobile' in device_data.get('device_type', '').lower():
                return "Android"
        
        # Router/Network device
        if any(x in vendor.lower() for x in ['cisco', 'netgear', 'tp-link', 'linksys']):
            return "Router OS"
        
        # Default based on TTL
        if ttl <= 64:
            return "Linux/Unix/macOS"
        elif ttl <= 128:
            return "Windows"
        else:
            return "Network Device"
    
    def classify_device_type_ai(self, device_data: Dict) -> str:
        """
        AI-powered device type classification using ML model.
        """
        # Use ML model if available
        if self.device_classifier and ML_AVAILABLE:
            try:
                features = self.extract_features(device_data).reshape(1, -1)
                device_type = self.device_classifier.predict(features)[0]
                if device_type != "unknown":
                    return device_type
            except Exception as e:
                pass
        
        # Fallback to enhanced rule-based classification
        return self._classify_device_patterns(device_data)
    
    def _classify_device_patterns(self, device_data: Dict) -> str:
        """Enhanced device type classification using patterns."""
        vendor = str(device_data.get('vendor', '')).lower()
        hostname = str(device_data.get('hostname', '')).lower()
        open_ports = device_data.get('open_ports', [])
        device_type = device_data.get('device_type', '')
        
        # Router/Network Equipment
        router_keywords = ['cisco', 'netgear', 'tp-link', 'linksys', 'asus router', 
                          'd-link', 'router', 'gateway', 'modem']
        if any(x in vendor for x in router_keywords) or any(x in hostname for x in router_keywords):
            return "router"
        
        # Mobile Devices
        mobile_keywords = ['iphone', 'ipad', 'android', 'galaxy', 'pixel', 'oneplus']
        if any(x in hostname for x in mobile_keywords):
            return "mobile"
        if any(x in vendor for x in ['apple', 'samsung', 'google']) and device_type == 'mobile':
            return "mobile"
        
        # Smart Home / IoT
        iot_keywords = ['philips hue', 'nest', 'ring', 'ecobee', 'sonos', 'amazon echo', 
                       'google home', 'alexa', 'smart', 'iot']
        if any(x in vendor.lower() for x in iot_keywords) or any(x in hostname for x in iot_keywords):
            return "iot"
        if 1883 in open_ports or 8123 in open_ports or 5683 in open_ports:  # MQTT, Home Assistant, CoAP
            return "iot"
        
        # Media Devices
        media_keywords = ['roku', 'chromecast', 'apple tv', 'fire tv', 'nvidia shield']
        if any(x in vendor.lower() for x in media_keywords) or any(x in hostname for x in media_keywords):
            return "media"
        if 32400 in open_ports or 8096 in open_ports or 554 in open_ports:  # Plex, Jellyfin, RTSP
            return "media"
        
        # Servers
        server_ports = [3306, 5432, 27017, 1433, 6379, 9200]  # Databases
        if any(port in open_ports for port in server_ports):
            return "server"
        if any(port in open_ports for port in [22, 3389, 5900]):  # SSH, RDP, VNC
            if device_data.get('risk_score', 0) > 20:
                return "server"
        
        # Laptops/Desktops
        laptop_keywords = ['dell', 'hp', 'lenovo', 'asus', 'acer', 'msi', 'laptop', 'desktop']
        if any(x in vendor.lower() for x in laptop_keywords):
            return "laptop"
        
        # Printers
        if any(x in vendor.lower() for x in ['hp', 'canon', 'epson', 'brother']) and 9100 in open_ports:
            return "printer"
        
        return "unknown"
    
    def generate_intelligent_name(self, device_data: Dict) -> Tuple[str, str]:
        """
        Generate intelligent device name and sub-label using AI patterns.
        
        Returns: (display_name, sub_label)
        """
        hostname = device_data.get('hostname', '')
        vendor = device_data.get('vendor', 'Unknown Vendor')
        ip = device_data.get('ip', '')
        device_type = device_data.get('device_type', 'unknown')
        os_type = device_data.get('os_type', 'Unknown')
        
        # Clean hostname
        hostname_clean = hostname.replace('.local', '').replace('.lan', '').split('.')[0]
        
        # Pattern 1: Use hostname if it's meaningful (not just IP or generic)
        if hostname_clean and len(hostname_clean) > 2 and hostname_clean != ip:
            # Enhance hostname with context
            if device_type != 'unknown':
                display_name = f"{hostname_clean} ({device_type.title()})"
            else:
                display_name = hostname_clean
            
            # Create sub-label
            if vendor != "Unknown Vendor":
                sub_label = vendor
            elif os_type != "Unknown":
                sub_label = os_type
            else:
                sub_label = f"Device at {ip.split('.')[-1]}"
            
            return (display_name, sub_label)
        
        # Pattern 2: Use vendor + device type
        if vendor != "Unknown Vendor":
            # Extract brand name
            brand = vendor.split()[0] if vendor else "Device"
            
            if device_type != 'unknown':
                display_name = f"{brand} {device_type.title()}"
            else:
                display_name = vendor
            
            sub_label = os_type if os_type != "Unknown" else f"IP: {ip}"
            return (display_name, sub_label)
        
        # Pattern 3: Use device type + IP
        if device_type != 'unknown':
            display_name = f"{device_type.title()} Device"
            sub_label = f"{os_type} - {ip}" if os_type != "Unknown" else ip
            return (display_name, sub_label)
        
        # Pattern 4: Fallback
        display_name = f"Device-{ip.split('.')[-1]}"
        sub_label = os_type if os_type != "Unknown" else "Unknown Device"
        return (display_name, sub_label)
    
    def evaluate_harmful_device(self, device_data: Dict) -> Dict[str, object]:
        hostname = str(device_data.get('hostname', ''))
        vendor = str(device_data.get('vendor', ''))
        risk = int(device_data.get('risk_score', 0))
        open_ports_count = device_data.get('open_ports_count', device_data.get('open_ports', 0))
        try:
            if isinstance(open_ports_count, list):
                open_ports_count = len(open_ports_count)
            elif isinstance(open_ports_count, str):
                open_ports_count = int(open_ports_count) if open_ports_count.isdigit() else 0
            elif not isinstance(open_ports_count, int):
                open_ports_count = int(open_ports_count) if open_ports_count else 0
        except:
            open_ports_count = 0
        port_summary = str(device_data.get('port_summary', '')).lower()
        critical_keywords = ['telnet', 'smb', 'rdp', 'vnc', 'ftp', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch']
        has_critical = any(k in port_summary for k in critical_keywords)
        harmful = (risk >= 50) or (open_ports_count >= 5) or has_critical
        return {
            "risk_score": risk,
            "open_ports_count": open_ports_count,
            "has_critical_ports": has_critical,
            "harmful": harmful
        }
    
    def generate_device_summary(self, device_data: Dict) -> str:
        name = device_data.get('nickname') or device_data.get('hostname') or device_data.get('vendor') or device_data.get('ip')
        device_type = device_data.get('device_type', 'unknown')
        os_type = device_data.get('os_type', 'Unknown')
        eval_res = self.evaluate_harmful_device(device_data)
        ports = device_data.get('open_ports_count', device_data.get('open_ports', 0))
        if isinstance(ports, list):
            ports = len(ports)
        latency = device_data.get('latency')
        status_bits = []
        status_bits.append(f"{ports} open ports")
        if eval_res["has_critical_ports"]:
            status_bits.append("critical services exposed")
        if isinstance(latency, (int, float)):
            status_bits.append(f"{latency}ms latency")
        risk_tag = "High Risk" if eval_res["harmful"] else "Low Risk"
        summary = f"{name}: {device_type.title()} • {os_type} • {', '.join(status_bits)} • {risk_tag}"
        return summary
    
    def train_models(self, training_data: List[Dict]):
        """
        Train ML models on collected device data.
        
        training_data: List of device dictionaries with known labels
        """
        if not ML_AVAILABLE or len(training_data) < 10:
            print("⚠️ Need at least 10 samples to train models. Using rule-based detection.")
            return
        
        try:
            # Prepare data - convert to DataFrame
            df = pd.DataFrame(training_data)
            
            # Clean and prepare device data dictionaries
            cleaned_data = []
            for _, row in df.iterrows():
                device_dict = row.to_dict()
                # Ensure open_ports is a list
                if 'open_ports' in device_dict:
                    if pd.isna(device_dict['open_ports']) or device_dict['open_ports'] is None:
                        device_dict['open_ports'] = []
                    elif isinstance(device_dict['open_ports'], (int, float)):
                        # If it's a count, we don't know which ports - use empty list
                        device_dict['open_ports'] = []
                    elif not isinstance(device_dict['open_ports'], list):
                        device_dict['open_ports'] = []
                else:
                    device_dict['open_ports'] = []
                cleaned_data.append(device_dict)
            
            # Extract features from cleaned data
            X = np.array([self.extract_features(device) for device in cleaned_data])
            
            # Device type classification
            if 'device_type' in df.columns:
                y_device = df['device_type'].fillna('unknown')
                le_device = LabelEncoder()
                y_device_encoded = le_device.fit_transform(y_device)
                
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y_device_encoded, test_size=0.2, random_state=42
                )
                
                self.device_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
                self.device_classifier.fit(X_train, y_train)
                self.label_encoders['device_type'] = le_device
                
                accuracy = self.device_classifier.score(X_test, y_test)
                print(f"✅ Device classifier trained - Accuracy: {accuracy:.2%}")
            
            # OS classification
            if 'os_type' in df.columns:
                y_os = df['os_type'].fillna('Unknown')
                le_os = LabelEncoder()
                y_os_encoded = le_os.fit_transform(y_os)
                
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y_os_encoded, test_size=0.2, random_state=42
                )
                
                self.os_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
                self.os_classifier.fit(X_train, y_train)
                self.label_encoders['os_type'] = le_os
                
                accuracy = self.os_classifier.score(X_test, y_test)
                print(f"✅ OS classifier trained - Accuracy: {accuracy:.2%}")
            
            # Save models
            self._save_models()
            
        except Exception as e:
            print(f"⚠️ Error training models: {e}")
            import traceback
            traceback.print_exc()
    
    def add_training_sample(self, device_data: Dict):
        """Add a device sample for future model training."""
        self.learning_data.append(device_data.copy())
        
        # Auto-train when we have enough samples
        if len(self.learning_data) >= 50:
            print(f"📚 Training models on {len(self.learning_data)} samples...")
            self.train_models(self.learning_data)
            self.learning_data = []  # Clear after training


# Global instance
_ai_detector_instance = None

def get_ai_detector() -> AIDeviceDetector:
    """Get or create the global AI detector instance."""
    global _ai_detector_instance
    if _ai_detector_instance is None:
        _ai_detector_instance = AIDeviceDetector()
    return _ai_detector_instance
