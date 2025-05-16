import os
import cv2
import numpy as np
from fast_alpr import ALPR
import logging
from PIL import Image
import json
from config import *

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('outputs/improved_plate_detection.log'),
        logging.StreamHandler()
    ]
)

class ImprovedPlateDetector:
    def __init__(self):
        """Initialize the improved license plate detector using Fast-ALPR"""
        # Create detector with default models
        try:
            self.alpr = ALPR(
                detector_model="yolo-v9-t-384-license-plate-end2end",
                ocr_model="global-plates-mobile-vit-v2-model",
            )
            logging.info("Fast-ALPR initialized successfully")
        except Exception as e:
            logging.error(f"Error initializing Fast-ALPR: {str(e)}")
            raise
        
        # Create directory for improved detections
        os.makedirs(os.path.join('outputs', 'improved_plates'), exist_ok=True)
        
    def detect_plates_from_speeding_images(self, speed_data_path):
        """
        Process all speeding vehicle images and detect license plates
        
        Args:
            speed_data_path: Path to the speed data JSON file
        
        Returns:
            Dictionary mapping vehicle IDs to their detected plate info
        """
        # Load the speed data to identify speeding vehicles
        with open(speed_data_path, 'r') as f:
            speed_data = json.load(f)
        
        speeding_vehicle_ids = []
        improved_plate_results = {}
        
        # Identify speeding vehicles
        for vehicle_id, data in speed_data['vehicle_speeds'].items():
            if data['average_speed'] >= 80:  # Same threshold as in the original system
                speeding_vehicle_ids.append(vehicle_id)
        
        # Process each speeding vehicle's images
        for vehicle_id in speeding_vehicle_ids:
            logging.info(f"Processing license plate for speeding vehicle {vehicle_id}")
            
            # Look for vehicle images in the outputs/speeding directory
            image_pattern = f"vehicle_{vehicle_id}_*.jpg"
            vehicle_images = []
            
            for filename in os.listdir(os.path.join('outputs', 'speeding')):
                if filename.startswith(f"vehicle_{vehicle_id}_") and filename.endswith('.jpg'):
                    vehicle_images.append(os.path.join('outputs', 'speeding', filename))
            
            if not vehicle_images:
                logging.warning(f"No images found for vehicle {vehicle_id}")
                continue
            
            # Use the vehicle image with the highest speed (should be in the filename)
            vehicle_images.sort(key=lambda x: float(x.split('_')[-1].replace('kmh.jpg', '')), reverse=True)
            best_image_path = vehicle_images[0]
            
            # Process the image with Fast-ALPR
            try:
                # Load the image
                image = cv2.imread(best_image_path)
                if image is None:
                    logging.error(f"Could not read image: {best_image_path}")
                    continue
                
                # Convert BGR to RGB for Fast-ALPR
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                
                # Get plate detection results
                results = self.alpr.predict(image_rgb)
                logging.info(f"Fast-ALPR results: {results}")
                
                # Check if any plates were detected
                if results and len(results) > 0:
                    # Find the plate with highest confidence
                    best_plate = None
                    highest_confidence = 0
                    
                    for plate in results:
                        if plate.ocr and plate.ocr.confidence > highest_confidence:
                            best_plate = plate
                            highest_confidence = plate.ocr.confidence
                    
                    if best_plate and best_plate.ocr:
                        # Extract plate information
                        plate_text = best_plate.ocr.text
                        confidence = best_plate.ocr.confidence
                        
                        # Draw predictions on the image
                        annotated_image = self.alpr.draw_predictions(image_rgb)
                        # Convert back to BGR for OpenCV
                        annotated_image = cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR)
                        
                        # Save the annotated image
                        output_path = os.path.join('outputs', 'improved_plates', f'improved_plate_{vehicle_id}.jpg')
                        cv2.imwrite(output_path, annotated_image)
                        
                        # Store the results
                        improved_plate_results[vehicle_id] = {
                            'plate_text': plate_text,
                            'confidence': float(confidence),  # Ensure it's a float for JSON serialization
                            'image_path': output_path,
                            'speed': float(best_image_path.split('_')[-1].replace('kmh.jpg', ''))
                        }
                        
                        logging.info(f"Vehicle {vehicle_id}: Detected plate '{plate_text}' with confidence {confidence:.2f}")
                    else:
                        logging.warning(f"No valid plate detection for vehicle {vehicle_id}")
                else:
                    logging.warning(f"No license plate detected for vehicle {vehicle_id}")
            
            except Exception as e:
                logging.error(f"Error processing vehicle {vehicle_id}: {str(e)}")
                logging.exception("Exception details:")
        
        # Save the improved plate results to a JSON file
        output_json_path = os.path.join('outputs', 'improved_plates', 'improved_plate_data.json')
        with open(output_json_path, 'w') as f:
            json.dump(improved_plate_results, f, indent=4)
        
        logging.info(f"Improved plate detection completed. Results saved to {output_json_path}")
        return improved_plate_results
    
    def get_improved_plates_data(self):
        """
        Get the improved plate detection data if available
        
        Returns:
            Dictionary with the improved plate detection results or empty dict if not available
        """
        json_path = os.path.join('outputs', 'improved_plates', 'improved_plate_data.json')
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                return json.load(f)
        return {} 