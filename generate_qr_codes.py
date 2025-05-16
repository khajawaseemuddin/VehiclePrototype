import os
import json
import qrcode

def generate_all_qr_codes():
    """Generate QR codes for all challans pointing to the eChallan website"""
    print("Generating QR codes for all challans...")
    
    # Ensure output directory exists
    os.makedirs(os.path.join('outputs', 'challans'), exist_ok=True)
    
    # Load challan data
    challan_data_path = os.path.join('outputs', 'challans', 'challans.json')
    if not os.path.exists(challan_data_path):
        print(f"No challan data found at {challan_data_path}")
        return
    
    with open(challan_data_path, 'r') as f:
        challan_data = json.load(f)
    
    # Get unique vehicle IDs
    vehicle_ids = []
    for challan in challan_data.get('challans', []):
        vehicle_id = challan.get('vehicle_id')
        if vehicle_id and vehicle_id not in vehicle_ids:
            vehicle_ids.append(vehicle_id)
    
    print(f"Found {len(vehicle_ids)} unique vehicle IDs")
    
    # Create QR code for each vehicle ID
    for vehicle_id in vehicle_ids:
        qr_path = os.path.join('outputs', 'challans', f'qr_{vehicle_id}.png')
        
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
        qr_img.save(qr_path)
        print(f"Generated QR code for vehicle {vehicle_id} at {qr_path}")
    
    print(f"Successfully generated {len(vehicle_ids)} QR codes")

if __name__ == "__main__":
    generate_all_qr_codes() 