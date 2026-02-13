"""Train AI models - Run this directly"""
import sys
import os

# Fix Windows encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Import modules
from ai_detector import get_ai_detector
from database import get_all_devices, get_device_count

def main():
    print("\n" + "="*60)
    print("🎓 TRAINING AI MODELS")
    print("="*60)
    
    # Check device count
    device_count = get_device_count()
    print(f"📊 Found {device_count} devices in database")
    
    if device_count < 10:
        print(f"\n❌ Not enough devices to train!")
        print(f"   Need at least 10 devices, currently have {device_count}")
        print(f"   Run some scans first to collect device data.")
        print("="*60 + "\n")
        return False
    
    print("🔄 Loading training data...")
    
    try:
        # Get all devices
        training_data = get_all_devices()
        print(f"✅ Loaded {len(training_data)} devices")
        
        if len(training_data) == 0:
            print("❌ No devices found in database!")
            return False
        
        # Initialize AI detector
        ai_detector = get_ai_detector()
        print("🧠 Training models (this may take a minute)...")
        print("   - Device Type Classifier")
        print("   - OS Classifier")
        
        # Train models
        ai_detector.train_models(training_data)
        
        print("\n✅ Training completed successfully!")
        print("💾 Models saved to backend/models/")
        print("🚀 AI detection is now active!")
        print("\n💡 The AI will now automatically:")
        print("   ✓ Classify device types more accurately")
        print("   ✓ Detect OS types better")
        print("   ✓ Generate intelligent device names")
        print("="*60 + "\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Training failed: {e}")
        import traceback
        traceback.print_exc()
        print("="*60 + "\n")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
