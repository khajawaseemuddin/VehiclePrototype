import subprocess
import sys
import os
import time

def main():
    # Create necessary directories
    os.makedirs('src/templates', exist_ok=True)
    os.makedirs('outputs/detections', exist_ok=True)
    os.makedirs('outputs/speeding', exist_ok=True)
    os.makedirs('outputs/plates', exist_ok=True)
    os.makedirs('outputs/improved_plates', exist_ok=True)
    os.makedirs('outputs/challans', exist_ok=True)

    print("=== Starting Traffic Violation Detection and Challan System ===")
    
    # Start speed detection and wait for it to complete
    print("\n[1/4] Running speed detection...")
    speed_detection_process = subprocess.run([sys.executable, 'src/speed_detection.py'])
    
    # Run license plate detection
    print("\n[2/4] Running license plate detection...")
    plate_detection_process = subprocess.run([sys.executable, 'src/license_plate_detection.py'])
    
    # Run improved license plate detection
    print("\n[3/4] Running improved license plate detection with Fast-ALPR...")
    improved_detection_process = subprocess.run([sys.executable, 'src/run_improved_detection.py'])
    
    # Generate challans for all speeding vehicles
    print("\n[4/4] Generating challans for speeding vehicles...")
    challan_process = subprocess.run([sys.executable, 'src/challan_system.py', '--all'])
    
    print("\n=== Processing completed! Starting web interface... ===")
    print("Access the dashboard at http://localhost:5000")
    
    # Start the web server
    web_server_process = subprocess.Popen([sys.executable, 'src/web_server.py'])
    
    try:
        # Wait for the web server
        web_server_process.wait()
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        web_server_process.terminate()
        print("\nShutting down...")

if __name__ == '__main__':
    main() 