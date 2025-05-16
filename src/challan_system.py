import os
import json
from datetime import datetime
import logging
from config import *
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import argparse
import qrcode
import base64
from io import BytesIO

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('outputs/challan_generation.log'),
        logging.StreamHandler()
    ]
)

class ChallanGenerator:
    def __init__(self):
        # Create output directory
        os.makedirs(os.path.join(OUTPUT_DIR, "challans"), exist_ok=True)
        
        # Load data
        self.speed_data = self.load_speed_data()
        self.plate_data = self.load_plate_data()
        
    def load_speed_data(self):
        """Load speed data from JSON file"""
        try:
            with open(os.path.join(OUTPUT_DIR, 'speeding', 'speed_data.json'), 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading speed data: {str(e)}")
            return {'vehicle_speeds': {}}
            
    def load_plate_data(self):
        """Load plate data from JSON file"""
        try:
            with open(os.path.join(OUTPUT_DIR, 'plates', 'plate_data.json'), 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading plate data: {str(e)}")
            return {}
            
    def calculate_fine(self, speed):
        """Calculate fine based on speed with improved structure"""
        from config import BASE_SPEED_LIMIT, BASE_FINE
        
        if speed <= BASE_SPEED_LIMIT:
            return 0
            
        excess_speed = speed - BASE_SPEED_LIMIT
        if excess_speed <= 20:
            return BASE_FINE
        elif excess_speed <= 40:
            return BASE_FINE * 2
        elif excess_speed <= 60:
            return BASE_FINE * 4
        else:
            return BASE_FINE * 8
    
    def generate_qr_code(self, challan_id, vehicle_id):
        """Generate QR code for digital challan access"""
        try:
            # Create a QR code pointing to the eChallan website
            challan_url = "https://echallan.tspolice.gov.in/publicview/"
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(challan_url)
            qr.make(fit=True)
            
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Save QR code
            qr_path = os.path.join(OUTPUT_DIR, "challans", f"qr_{vehicle_id}.png")
            qr_img.save(qr_path)
            
            return qr_path
        except Exception as e:
            logging.error(f"Error generating QR code: {str(e)}")
            return None
    
    def generate_digital_challan_message(self, vehicle_id, plate_text, speed, fine_amount):
        """Generate the message text for the digital challan"""
        message = f"""
TRAFFIC CHALLAN NOTIFICATION

Vehicle Number: {plate_text}
Violation: Speed Limit Exceeded
Recorded Speed: {speed:.1f} km/h
Speed Limit: {BASE_SPEED_LIMIT} km/h
Fine Amount: Rs. {fine_amount}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Location: {LOCATION}

This is an automated message. Please visit our website or scan the QR code on your digital challan to view details and make payment.

Traffic Police Department
{AUTHORITY_NAME}
"""
        return message
            
    def generate_challan(self, vehicle_id):
        """Generate challan for a specific vehicle"""
        # Get vehicle data
        if vehicle_id not in self.speed_data['vehicle_speeds']:
            logging.error(f"Vehicle {vehicle_id} not found in speed data")
            return None
        
        # First check if we have improved plate data
        improved_plate_path = os.path.join(OUTPUT_DIR, 'improved_plates', 'improved_plate_data.json')
        improved_plate_data = {}
        
        if os.path.exists(improved_plate_path):
            try:
                with open(improved_plate_path, 'r') as f:
                    improved_plate_data = json.load(f)
            except Exception as e:
                logging.error(f"Error loading improved plate data: {str(e)}")
        
        vehicle_data = self.speed_data['vehicle_speeds'][vehicle_id]
        speed = vehicle_data['average_speed']
        
        # Get license plate information
        license_plate = "Unknown"
        confidence = 0
        
        # Try to get the license plate from improved detection first
        if vehicle_id in improved_plate_data:
            license_plate = improved_plate_data[vehicle_id]['plate_text']
            confidence = improved_plate_data[vehicle_id]['confidence']
            logging.info(f"Using improved license plate detection: {license_plate} with confidence {confidence:.2f}")
        # Fall back to original plate detection
        elif vehicle_id in self.plate_data:
            best_detection = max(self.plate_data[vehicle_id], key=lambda x: x['confidence'])
            license_plate = best_detection['plate_text'] or "Unreadable"
            confidence = best_detection['confidence']
            logging.info(f"Using original license plate detection: {license_plate} with confidence {confidence:.2f}")
        else:
            logging.warning(f"No license plate data found for vehicle {vehicle_id}")
            
        # Calculate fine amount
        fine_amount = self.calculate_fine(speed)
        
        # Generate challan ID
        challan_id = f"CH-{datetime.now().strftime('%Y%m%d')}-{vehicle_id}"
        
        # Create challan data
        challan_data = {
            "challan_id": challan_id,
            "vehicle_id": vehicle_id,
            "license_plate": license_plate,
            "date_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "location": LOCATION,
            "speed_detected": speed,
            "speed_limit": BASE_SPEED_LIMIT,
            "fine_amount": fine_amount,
            "authority_name": AUTHORITY_NAME,
            "authority_phone": AUTHORITY_PHONE,
            "payment_link": PAYMENT_LINK,
            "plate_confidence": confidence
        }
        
        # Generate QR code for digital access
        qr_path = self.generate_qr_code(challan_id, vehicle_id)
        
        # Create challan template
        template = Image.new('RGB', (800, 1200), 'white')
        draw = ImageDraw.Draw(template)
        
        # Load font
        try:
            title_font = ImageFont.truetype("arial.ttf", 24)
            header_font = ImageFont.truetype("arial.ttf", 20)
            text_font = ImageFont.truetype("arial.ttf", 16)
        except:
            title_font = ImageFont.load_default()
            header_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
        
        # Add header
        draw.text((50, 50), "TRAFFIC CHALLAN", fill='black', font=title_font)
        draw.text((50, 90), f"Challan ID: {challan_id}", fill='black', font=header_font)
        
        # Add vehicle details
        y_offset = 150
        details = [
            f"Vehicle ID: {vehicle_id}",
            f"License Plate: {license_plate}",
            f"Violation: Speed Limit Exceeded",
            f"Recorded Speed: {speed:.1f} km/h",
            f"Speed Limit: {BASE_SPEED_LIMIT} km/h",
            f"Fine Amount: Rs. {fine_amount}",
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Location: {LOCATION}"
        ]
        
        for detail in details:
            draw.text((50, y_offset), detail, fill='black', font=text_font)
            y_offset += 30
        
        # Add note about digital access
        y_offset += 20
        draw.text((50, y_offset), "Important Notice:", fill='black', font=header_font)
        y_offset += 40
        
        notice_text = (
            "This challan has been generated automatically by our traffic monitoring system. "
            "To view this challan digitally and for payment options, please scan the QR code below "
            "or visit our website and enter your vehicle number and challan ID."
        )
        
        # Wrap text to fit width
        import textwrap
        wrapped_text = textwrap.fill(notice_text, width=70)
        for line in wrapped_text.split('\n'):
            draw.text((50, y_offset), line, fill='black', font=text_font)
            y_offset += 25
            
        # Add plate image
        try:
            y_offset += 20
            # Use improved plate image if available
            if vehicle_id in improved_plate_data:
                plate_img_path = improved_plate_data[vehicle_id]['image_path']
                plate_img = Image.open(plate_img_path)
            else:
                plate_img_path = best_detection['plate_path']
                plate_img = Image.open(plate_img_path)
                
            plate_img = plate_img.resize((200, 100))
            template.paste(plate_img, (50, y_offset))
            y_offset += 120
        except Exception as e:
            logging.error(f"Error adding plate image: {str(e)}")
            # Continue even if plate image cannot be added
        
        # Add QR code
        try:
            if qr_path and os.path.exists(qr_path):
                qr_img = Image.open(qr_path)
                qr_img = qr_img.resize((200, 200))
                template.paste(qr_img, (550, y_offset - 200))
        except Exception as e:
            logging.error(f"Error adding QR code: {str(e)}")
        
        # Add footer
        y_offset += 50
        draw.text((50, y_offset), f"Traffic Police Department", fill='black', font=text_font)
        y_offset += 25
        draw.text((50, y_offset), f"{AUTHORITY_NAME}", fill='black', font=text_font)
        
        # Save challan
        challan_path = os.path.join(OUTPUT_DIR, "challans", f"challan_{vehicle_id}.jpg")
        template.save(challan_path)
        
        # Generate digital challan message
        digital_message = self.generate_digital_challan_message(
            vehicle_id, license_plate, speed, fine_amount
        )
        
        # Save digital message to file for later reference
        message_path = os.path.join(OUTPUT_DIR, "challans", f"message_{vehicle_id}.txt")
        with open(message_path, 'w') as f:
            f.write(digital_message)
        
        # Store challan data for web display
        self.save_challan_data(challan_id, vehicle_id, license_plate, speed, fine_amount)
        
        logging.info(f"Generated challan for vehicle {vehicle_id}")
        return challan_id
        
    def save_challan_data(self, challan_id, vehicle_id, plate_text, speed, fine_amount):
        """Save challan data to JSON for web access"""
        try:
            challan_data_path = os.path.join(OUTPUT_DIR, 'challans', 'challans.json')
            
            # Load existing data if available
            if os.path.exists(challan_data_path):
                with open(challan_data_path, 'r') as f:
                    all_challans = json.load(f)
            else:
                all_challans = {'challans': []}
                
            # Add new challan
            all_challans['challans'].append({
                'challan_id': challan_id,
                'vehicle_id': vehicle_id,
                'plate_text': plate_text,
                'speed': speed,
                'fine_amount': fine_amount,
                'issue_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'Pending',
                'challan_image': f"/get_challan/{vehicle_id}",
                'qr_code': f"/get_qr/{vehicle_id}"
            })
            
            # Save updated data
            with open(challan_data_path, 'w') as f:
                json.dump(all_challans, f, indent=4)
                
        except Exception as e:
            logging.error(f"Error saving challan data: {str(e)}")
            
    def generate_all_challans(self):
        """Generate challans for all speeding vehicles"""
        try:
            generated_ids = []
            # Get all vehicle IDs from speed data where speed exceeds limit
            for vehicle_id, data in self.speed_data.get('vehicle_speeds', {}).items():
                if data.get('average_speed', 0) >= BASE_SPEED_LIMIT:
                    challan_id = self.generate_challan(vehicle_id)
                    if challan_id:
                        generated_ids.append(challan_id)
                
            logging.info(f"Generated {len(generated_ids)} challans successfully")
            return generated_ids
            
        except Exception as e:
            logging.error(f"Error generating all challans: {str(e)}")
            return []
            
    def export_challan_data(self):
        """Export challan data to JSON file"""
        try:
            challan_data = {}
            for vehicle_id, data in self.plate_data.items():
                if data.get('plates'):
                    challan_data[vehicle_id] = {
                        'plate_text': data['plates'][0].get('plate_text', '') if data['plates'] else '',
                        'average_speed': data.get('average_speed', 0),
                        'fine_amount': self.calculate_fine(data.get('average_speed', 0)),
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                
            with open(os.path.join(OUTPUT_DIR, 'challans', 'challan_data.json'), 'w') as f:
                json.dump(challan_data, f, indent=4)
                
            logging.info("Exported challan data successfully")
            
        except Exception as e:
            logging.error(f"Error exporting challan data: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Challan Generation System')
    parser.add_argument('--vehicle-id', type=str, help='Specific vehicle ID to generate challan for')
    parser.add_argument('--all', action='store_true', help='Generate challans for all speeding vehicles')
    args = parser.parse_args()
    
    generator = ChallanGenerator()
    
    if args.vehicle_id:
        # Generate challan for specific vehicle
        vehicle_id = args.vehicle_id
        logging.info(f"Generating challan for vehicle ID: {vehicle_id}")
        challan_id = generator.generate_challan(vehicle_id)
        if challan_id:
            logging.info(f"Successfully generated challan {challan_id} for vehicle {vehicle_id}")
        else:
            logging.error(f"Failed to generate challan for vehicle {vehicle_id}")
    elif args.all or not args.vehicle_id:
        # Generate challans for all speeding vehicles
        logging.info("Generating challans for all speeding vehicles")
        generated_ids = generator.generate_all_challans()
        logging.info(f"Generated {len(generated_ids)} challans")
    
    logging.info("Challan generation completed!")

if __name__ == '__main__':
    main() 