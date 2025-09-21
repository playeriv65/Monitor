# Monitor

## Project Overview

This project is for action and behavior monitoring, supporting fall detection, behavior recording, and remote access. It is based on YOLO pose estimation, OpenCV video processing, and Flask service, suitable for security, elderly care, and similar scenarios.

## Main Features
- Real-time camera action monitoring
- Fall detection and recording
- Image capture and storage
- WebSocket real-time result push
- Web API for querying and downloading records

## Requirements
- Python 3.8+
- opencv-python
- ultralytics
- flask
- flask_sock

## Quick Start
1. Install dependencies:
	```bash
	pip install -r requirements.txt
	```
2. Run the main program:
	```bash
	python main.py
	```
3. Access the service:
	- WebSocket: ws://localhost:8088/connect
	- Query records: POST http://localhost:8088/checkall
	- Download image: http://localhost:8088/download/<filename>

## Directory Structure
- main.py: Main entry, process scheduling
- examiner.py: Action recognition and fall detection
- recorder.py: Image and record saving
- server.py: Web service and API
- config.py: Parameter configuration
- picture/: Image storage directory
- fall_record.json: Fall records

## Notes
- Supports multi-process concurrency; camera, service, and recorder can be switched independently
- See config.py for configuration
- YOLO model file should be placed in the root directory
