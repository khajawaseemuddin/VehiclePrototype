from flask import Flask, render_template, jsonify, send_file, redirect, url_for, request
import json
import os
import glob
from improved_plate_detection import ImprovedPlateDetector
from challan_system import ChallanGenerator

app = Flask(__name__)

def get_detection_results():
    """Get speed detection results"""
    results_path = os.path.join('outputs', 'detections', 'detection_results.json')
    if os.path.exists(results_path):
        with open(results_path, 'r') as f:
            return json.load(f)
    return {
        'total_frames': 0,
        'total_vehicles': 0,
        'speeding_vehicles': 0,
        'speeding_vehicle_ids': []
    }

def get_plate_data():
    """Get license plate data for speeding vehicles"""
    # Get speed detection results first to know which vehicles were speeding
    results = get_detection_results()
    speeding_ids = results.get('speeding_vehicle_ids', [])
    
    # Process plate data only for speeding vehicles
    vehicle_details = {}
    
    # Read the speed data
    speed_data_path = os.path.join('outputs', 'speeding', 'speed_data.json')
    speed_data = {}
    if os.path.exists(speed_data_path):
        with open(speed_data_path, 'r') as f:
            speed_data = json.load(f)
            vehicle_speeds = speed_data.get('vehicle_speeds', {})
    
    # Read the plate detection results
    plate_results_path = os.path.join('outputs', 'plates', 'plate_detection_results.json')
    if os.path.exists(plate_results_path):
        with open(plate_results_path, 'r') as f:
            plate_data = json.load(f)
            all_vehicle_details = plate_data.get('vehicle_details', {})
            
            for vehicle_id in speeding_ids:
                str_vehicle_id = str(vehicle_id)
                # Get speed data for this vehicle
                vehicle_speed_data = vehicle_speeds.get(str_vehicle_id, {})
                avg_speed = float(vehicle_speed_data.get('average_speed', 0))
                
                if str_vehicle_id in all_vehicle_details:
                    # Get the plate detections for this vehicle
                    detections = all_vehicle_details[str_vehicle_id]
                    if detections:
                        # Use the detection with highest confidence
                        best_detection = max(detections, key=lambda x: x['confidence'])
                        vehicle_details[str_vehicle_id] = {
                            'plate_text': best_detection['plate_text'] or 'Unreadable',
                            'confidence': best_detection['confidence'],
                            'speed': avg_speed
                        }
                else:
                    vehicle_details[str_vehicle_id] = {
                        'plate_text': 'No plate detected',
                        'confidence': 0,
                        'speed': avg_speed
                    }
    
    return {
        'total_vehicles_processed': len(speeding_ids),
        'plates_detected': len(vehicle_details),
        'vehicle_details': vehicle_details
    }

def get_improved_plate_data():
    """Get improved license plate data for speeding vehicles"""
    # Try to load the improved plate data first
    improved_data_path = os.path.join('outputs', 'improved_plates', 'improved_plate_data.json')
    
    # If data doesn't exist yet, create it by running the detector
    if not os.path.exists(improved_data_path):
        speed_data_path = os.path.join('outputs', 'speeding', 'speed_data.json')
        if os.path.exists(speed_data_path):
            try:
                detector = ImprovedPlateDetector()
                detector.detect_plates_from_speeding_images(speed_data_path)
            except Exception as e:
                print(f"Error generating improved plate data: {str(e)}")
    
    # Now try to load the data (which may have just been created)
    if os.path.exists(improved_data_path):
        with open(improved_data_path, 'r') as f:
            return json.load(f)
    
    return {}  # Return empty dict if no data available

def get_challan_data():
    """Get all generated challans"""
    challan_data_path = os.path.join('outputs', 'challans', 'challans.json')
    if os.path.exists(challan_data_path):
        with open(challan_data_path, 'r') as f:
            return json.load(f)
    return {'challans': []}

@app.route('/')
def index():
    # Get detection results and plate data
    results = get_detection_results()
    plate_data = get_plate_data()
    improved_data = get_improved_plate_data()
    
    return render_template('index.html', results=results, plate_data=plate_data, improved_data=improved_data)

@app.route('/api/results')
def get_results():
    results = get_detection_results()
    plate_data = get_plate_data()
    
    return jsonify({
        'speed_results': results,
        'plate_data': plate_data
    })

@app.route('/api/plates')
def get_plates():
    return jsonify(get_plate_data())

@app.route('/api/improved_plates')
def get_improved_plates():
    """API endpoint to get improved plate detection data"""
    improved_data = get_improved_plate_data()
    
    # Format for consistent API response
    formatted_data = {
        'total_vehicles_processed': len(improved_data),
        'plates_detected': len(improved_data),
        'vehicle_details': improved_data
    }
    
    return jsonify(formatted_data)

@app.route('/plates/<vehicle_id>')
def get_plate_image(vehicle_id):
    # Try both formats of filenames
    patterns = [
        os.path.join('outputs', 'plates', f'plate_vehicle_{vehicle_id}_*.jpg'),
        os.path.join('outputs', 'plates', f'plate_vehicle_{vehicle_id}_*kmh.jpg')
    ]
    
    for pattern in patterns:
        plate_files = glob.glob(pattern)
        if plate_files:
            return send_file(plate_files[0], mimetype='image/jpeg')
    
    return '', 404

@app.route('/improved_plates/<vehicle_id>')
def get_improved_plate_image(vehicle_id):
    """Get the improved license plate detection image for a vehicle"""
    image_path = os.path.join('outputs', 'improved_plates', f'improved_plate_{vehicle_id}.jpg')
    if os.path.exists(image_path):
        return send_file(image_path, mimetype='image/jpeg')
    else:
        return '', 404

@app.route('/improved_plates')
def improved_plates_page():
    """Page to display the improved license plate detections"""
    results = get_detection_results()
    improved_data = get_improved_plate_data()
    return render_template('improved_plates.html', results=results, improved_data=improved_data)

@app.route('/api/challans')
def get_challans():
    """Get all generated challans"""
    return jsonify(get_challan_data())

@app.route('/get_challan/<vehicle_id>')
def get_challan_image(vehicle_id):
    """Get the challan image for a specific vehicle"""
    try:
        challan_path = os.path.join('outputs', 'challans', f'challan_{vehicle_id}.jpg')
        if os.path.exists(challan_path):
            return send_file(challan_path, mimetype='image/jpeg')
        else:
            return '', 404
    except Exception as e:
        return str(e), 500

@app.route('/get_qr/<vehicle_id>')
def get_qr_code(vehicle_id):
    """Get the QR code for a specific vehicle's challan"""
    try:
        import qrcode
        import io
        from io import BytesIO
        from base64 import b64encode
        from flask import send_file
        
        # Create a QR code pointing to the eChallan website
        url = "https://echallan.tspolice.gov.in/publicview/"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Save the QR code to a BytesIO object
        img_io = BytesIO()
        qr_img.save(img_io, 'PNG')
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/png')
    except Exception as e:
        print(f"Error serving QR code: {str(e)}")
        return str(e), 500

@app.route('/get_message/<vehicle_id>')
def get_challan_message(vehicle_id):
    """Get the digital message for a specific vehicle's challan"""
    try:
        message_path = os.path.join('outputs', 'challans', f'message_{vehicle_id}.txt')
        if os.path.exists(message_path):
            with open(message_path, 'r') as f:
                message = f.read()
            return message, 200, {'Content-Type': 'text/plain'}
        else:
            return 'No message found for this vehicle', 404
    except Exception as e:
        return str(e), 500

@app.route('/view_challan/<challan_id>/<vehicle_id>')
def view_challan(challan_id, vehicle_id):
    """Render the challan view page"""
    challan_data = get_challan_data()
    target_challan = None
    
    for challan in challan_data.get('challans', []):
        if challan.get('challan_id') == challan_id and challan.get('vehicle_id') == vehicle_id:
            target_challan = challan
            break
    
    if target_challan:
        return render_template('view_challan.html', challan=target_challan)
    else:
        return "Challan not found", 404

@app.route('/challans')
def challans_page():
    """Render the challans listing page"""
    return render_template('challans.html', challan_data=get_challan_data())

@app.route('/generate_challans', methods=['POST'])
def generate_specific_challan():
    """Generate a challan for a specific vehicle"""
    try:
        # Parse request data
        data = request.json
        vehicle_id = data.get('vehicle_id')
        
        if not vehicle_id:
            return jsonify({'error': 'Vehicle ID is required'}), 400
            
        # Initialize challan generator
        generator = ChallanGenerator()
        
        # Generate challan
        challan_id = generator.generate_challan(vehicle_id)
        
        if challan_id:
            return jsonify({
                'success': True, 
                'challan_id': challan_id,
                'message': f'Challan generated successfully for vehicle {vehicle_id}'
            })
        else:
            return jsonify({'error': 'Failed to generate challan'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 