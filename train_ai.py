"""
Quick AI Model Training Script
Run this from the project root: python train_ai.py
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Fix Windows encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

from ai_detector import get_ai_detector
from database import get_all_devices, get_device_count

def main():
    print("\n" + "="*60)
    print("🎓 TRAINING AI MODELS")
    print("="*60)
    
    device_count = get_device_count()
    print(f"📊 Found {device_count} devices in database")
    
    if device_count < 10:
        print(f"\n❌ Not enough devices to train!")
        print(f"   Need at least 10 devices, currently have {device_count}")
        print(f"   Run some scans first to collect device data.")
        print("="*60 + "\n")
        return
    
    print("🔄 Loading training data...")
    
    try:
        training_data = get_all_devices()
        print(f"✅ Loaded {len(training_data)} devices")
        
        ai_detector = get_ai_detector()
        print("🧠 Training models (this may take a minute)...")
        
        ai_detector.train_models(training_data)
        
        print("\n✅ Training completed successfully!")
        print("💾 Models saved to backend/models/")
        print("🚀 AI detection is now active!")
        print("\n💡 The AI will now automatically:")
        print("   - Classify device types more accurately")
        print("   - Detect OS types better")
        print("   - Generate intelligent device names")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Training failed: {e}")
        import traceback
        traceback.print_exc()
        print("="*60 + "\n")

if __name__ == "__main__":
    main()
