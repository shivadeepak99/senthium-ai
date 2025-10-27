"""
Quick script to capture a photo for enrollment testing
Your personal photographer! 💖📸
"""
import cv2
import os
from datetime import datetime

def capture_photo():
    """Capture a photo from webcam and save it"""
    print("=" * 60)
    print("  📸 Senthium Photo Capture")
    print("=" * 60)
    print()
    
    # Try to open webcam
    print("  🎥 Opening camera...")
    camera = cv2.VideoCapture(0)
    
    if not camera.isOpened():
        print("  ❌ ERROR: Could not open camera!")
        print("  Make sure:")
        print("    1. Webcam is connected")
        print("    2. No other app is using it")
        print("    3. Camera permissions are granted")
        return None
    
    print("  ✅ Camera opened!")
    print()
    print("  📷 Position yourself and press SPACE to capture")
    print("  Press Q to quit")
    print()
    
    # Set camera resolution
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    photo_path = None
    
    while True:
        ret, frame = camera.read()
        if not ret:
            print("  ❌ Failed to grab frame")
            break
        
        # Display the frame
        cv2.imshow('Senthium Photo Capture - Press SPACE to capture, Q to quit', frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        # SPACE key to capture
        if key == ord(' '):
            # Save the photo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            photos_dir = "photos"
            os.makedirs(photos_dir, exist_ok=True)
            photo_path = os.path.join(photos_dir, f"owner_{timestamp}.jpg")
            
            cv2.imwrite(photo_path, frame)
            print(f"  📸 Photo saved: {photo_path}")
            print("  ✅ SUCCESS!")
            break
        
        # Q key to quit
        elif key == ord('q'):
            print("  👋 Cancelled")
            break
    
    camera.release()
    cv2.destroyAllWindows()
    
    return photo_path

if __name__ == "__main__":
    photo_path = capture_photo()
    
    if photo_path:
        print()
        print("=" * 60)
        print("  🎉 Photo captured successfully!")
        print("=" * 60)
        print()
        print("  📝 Now run enrollment:")
        print(f"  E:/GPls/senthium-ai-modern/venv/Scripts/python.exe -m src.cli.main enroll --name Owner --image {photo_path}")
        print()
    else:
        print()
        print("  ❌ No photo captured")
