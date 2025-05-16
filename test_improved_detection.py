import os
import sys
import time
import logging
from src.improved_plate_detection import ImprovedPlateDetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('outputs/test_improved_detection.log'),
        logging.StreamHandler()
    ]
)

def main():
    """
    Test the improved license plate detection system
    """
    print("=== Testing Improved License Plate Detection ===")
    
    # Create necessary directories
    os.makedirs('outputs/improved_plates', exist_ok=True)
    
    # Check if speed data exists
    speed_data_path = os.path.join('outputs', 'speeding', 'speed_data.json')
    if not os.path.exists(speed_data_path):
        print(f"Error: Speed data not found at {speed_data_path}")
        print("Please run the speed detection system first")
        return 1
    
    try:
        # Initialize the detector
        print("Initializing Fast-ALPR detector...")
        start_time = time.time()
        detector = ImprovedPlateDetector()
        
        # Run detection
        print("Running improved license plate detection...")
        results = detector.detect_plates_from_speeding_images(speed_data_path)
        elapsed_time = time.time() - start_time
        
        # Print results
        print("\nDetection completed in {:.2f} seconds".format(elapsed_time))
        print(f"Processed {len(results)} speeding vehicles")
        
        # Print detailed results for each vehicle
        for vehicle_id, data in results.items():
            print(f"\nVehicle ID: {vehicle_id}")
            print(f"  License Plate: {data['plate_text']}")
            print(f"  Confidence: {data['confidence']:.2f}")
            print(f"  Speed: {data['speed']} km/h")
            print(f"  Image saved to: {data['image_path']}")
        
        print("\nTest completed successfully!")
        return 0
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        logging.exception("Exception details:")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 