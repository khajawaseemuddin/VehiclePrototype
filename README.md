# Vehicle Detection System

A comprehensive system for detecting vehicles, recognizing license plates, and managing traffic violations. This system uses computer vision and machine learning to automate traffic monitoring and challan generation.

## Features

- Real-time vehicle detection
- License plate recognition
- Speed detection
- Automated challan generation
- QR code generation for challans
- Web interface for viewing violations
- Database management for traffic violations

## System Architecture

The system consists of several interconnected components:
- Vehicle Detection Module
- License Plate Recognition Module
- Speed Detection Module
- Challan Generation System
- Web Interface
- Database Management

## Prerequisites

- Python 3.13 or higher
- OpenCV
- PyTorch
- YOLOv8
- SQLite3
- Flask
- Other dependencies listed in `requirements.txt`

## Installation

1. Clone the repository:
```bash
git clone https://github.com/khajawaseemuddin/VehiclePrototype.git
cd VehiclePrototype
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Download required model weights:
- YOLOv8 model weights
- License plate detector weights

## Usage

1. Run the main system:
```bash
python run_system.py
```

2. Access the web interface:
- Open your browser and navigate to `http://localhost:5000`

3. For testing improved detection:
```bash
python test_improved_detection.py
```

## Project Structure

```
VehiclePrototype/
├── src/                    # Source code
│   ├── app.py             # Main application
│   ├── challan_system.py  # Challan generation
│   ├── templates/         # Web templates
│   └── ...
├── models/                # ML models
├── outputs/              # Generated outputs
├── static/              # Static files
├── templates/           # HTML templates
├── uploads/            # Upload directory
└── requirements.txt    # Project dependencies
```

## Configuration

The system can be configured through `config.py`. Key configurations include:
- Camera settings
- Detection thresholds
- Speed limits
- Database settings

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- YOLOv8 for object detection
- OpenCV for computer vision capabilities
- Flask for web interface
- All other open-source libraries used in this project 