"""
AI Model Runner - Train and test AI detection models
"""

import sys
import os

# Fix Windows encoding for emojis
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_detector import get_ai_detector
from database import get_all_devices, get_device_count
import json

def print_status():
    """Print current AI detector status."""
    print("\n" + "="*60)
    print("🤖 AI DETECTOR STATUS")
    print("="*60)
    
    ai_detector = get_ai_detector()
    
    # Check ML availability
    try:
        from sklearn.ensemble import RandomForestClassifier
        ml_available = True
    except ImportError:
        ml_available = False
    
    device_count = get_device_count()
    has_device_model = ai_detector.device_classifier is not None
    has_os_model = ai_detector.os_classifier is not None
    training_samples = len(ai_detector.learning_data)
    
    print(f"📊 ML Libraries Available: {'✅ Yes' if ml_available else '❌ No (using rule-based)'}")
    print(f"📱 Devices in Database: {device_count}")
    print(f"🎯 Device Classifier Loaded: {'✅ Yes' if has_device_model else '❌ No'}")
    print(f"💻 OS Classifier Loaded: {'✅ Yes' if has_os_model else '❌ No'}")
    print(f"📚 Training Samples Collected: {training_samples}")
    print(f"🔧 Detection Mode: {'ML Models' if (has_device_model or has_os_model) else 'Rule-Based'}")
    
    if device_count > 0:
        print(f"\n💡 Tip: Run 'python run_ai.py train' to train models on {device_count} devices")
    else:
        print(f"\n💡 Tip: Run scans first to collect device data, then train models")
    
    print("="*60 + "\n")

def train_models():
    """Train AI models on collected device data."""
    print("\n" + "="*60)
    print("🎓 TRAINING AI MODELS")
    print("="*60)
    
    device_count = get_device_count()
    
    if device_count < 10:
        print(f"❌ Not enough devices to train models!")
        print(f"   Need at least 10 devices, currently have {device_count}")
        print(f"   Run some scans first to collect device data.")
        print("="*60 + "\n")
        return False
    
    print(f"📊 Found {device_count} devices in database")
    print("🔄 Loading training data...")
    
    try:
        training_data = get_all_devices()
        print(f"✅ Loaded {len(training_data)} devices")
        
        ai_detector = get_ai_detector()
        print("🧠 Training models...")
        
        ai_detector.train_models(training_data)
        
        print("\n✅ Training completed successfully!")
        print("💾 Models saved to backend/models/")
        print("🚀 AI detection is now active!")
        print("="*60 + "\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Training failed: {e}")
        import traceback
        traceback.print_exc()
        print("="*60 + "\n")
        return False

def test_detection():
    """Test AI detection on sample device data."""
    print("\n" + "="*60)
    print("🧪 TESTING AI DETECTION")
    print("="*60)
    
    ai_detector = get_ai_detector()
    
    # Sample device data for testing
    test_devices = [
        {
            "ip": "192.168.1.100",
            "mac": "aa:bb:cc:dd:ee:01",
            "vendor": "Samsung Electronics",
            "hostname": "android-abc123",
            "open_ports": [443, 80],
            "risk_score": 10,
            "ttl": 64,
            "device_type": "mobile",
            "os_type": "Android"
        },
        {
            "ip": "192.168.1.101",
            "mac": "00:11:22:33:44:55",
            "vendor": "Apple, Inc.",
            "hostname": "MacBook-Pro.local",
            "open_ports": [22, 443],
            "risk_score": 15,
            "ttl": 64,
            "device_type": "laptop",
            "os_type": "macOS"
        },
        {
            "ip": "192.168.1.1",
            "mac": "aa:bb:cc:00:00:01",
            "vendor": "TP-Link Technologies",
            "hostname": "router",
            "open_ports": [80, 443, 8080],
            "risk_score": 20,
            "ttl": 64,
            "device_type": "router",
            "os_type": "Router OS"
        }
    ]
    
    print("Testing detection on sample devices:\n")
    
    for i, device in enumerate(test_devices, 1):
        print(f"Device {i}:")
        print(f"  IP: {device['ip']}")
        print(f"  Vendor: {device['vendor']}")
        print(f"  Hostname: {device['hostname']}")
        
        # Test OS detection
        os_detected = ai_detector.detect_os_ai(device)
        print(f"  OS Detected: {os_detected}")
        
        # Test device type classification
        device_type = ai_detector.classify_device_type_ai(device)
        print(f"  Device Type: {device_type}")
        
        # Test intelligent naming
        display_name, sub_label = ai_detector.generate_intelligent_name(device)
        print(f"  Display Name: {display_name}")
        print(f"  Sub Label: {sub_label}")
        print()
    
    print("="*60 + "\n")

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print_status()
        print("\nUsage:")
        print("  python run_ai.py status   - Show AI detector status")
        print("  python run_ai.py train    - Train models on collected devices")
        print("  python run_ai.py test     - Test AI detection on sample data")
        return
    
    command = sys.argv[1].lower()
    
    if command == "status":
        print_status()
    elif command == "train":
        train_models()
    elif command == "test":
        test_detection()
    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: status, train, test")

if __name__ == "__main__":
    main()
