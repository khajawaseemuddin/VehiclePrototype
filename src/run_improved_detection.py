import os
import sys
import json
import logging
from improved_plate_detection import ImprovedPlateDetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('outputs/improved_detection.log'),
        logging.StreamHandler()
    ]
)

def main():
    """Run the improved license plate detection on speeding vehicles"""
    logging.info("Starting improved license plate detection")
    
    # Check if speed data exists
    speed_data_path = os.path.join('outputs', 'speeding', 'speed_data.json')
    if not os.path.exists(speed_data_path):
        logging.error(f"Speed data not found at {speed_data_path}")
        print(f"Error: Speed data not found at {speed_data_path}")
        print("Please run the speed detection system first")
        return 1
    
    # Create detector and run detection
    try:
        detector = ImprovedPlateDetector()
        results = detector.detect_plates_from_speeding_images(speed_data_path)
        
        # Print summary
        print("\n=== Improved License Plate Detection Results ===")
        print(f"Processed {len(results)} speeding vehicles\n")
        
        for vehicle_id, data in results.items():
            print(f"Vehicle ID: {vehicle_id}")
            print(f"License Plate: {data['plate_text']}")
            print(f"Confidence: {data['confidence']:.2f}")
            print(f"Speed: {data['speed']} km/h")
            print(f"Image saved to: {data['image_path']}")
            print("-" * 40)
        
        logging.info("Improved license plate detection completed successfully")
        return 0
    
    except Exception as e:
        logging.error(f"Error in improved license plate detection: {str(e)}")
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 