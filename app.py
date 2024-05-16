from flask import Flask, Response, render_template, jsonify, request, send_from_directory, make_response
import datetime
import requests
import cv2
import numpy as np
import os
import zipfile
import base64
import logging
from PIL import Image
from moviepy.editor import ImageSequenceClip

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

# Define constants for directories and frame rate
current_directory = os.path.dirname(os.path.abspath(__file__))
save_directory = os.path.join(current_directory, "saved_images")
FRAME_RATE = 1  # Default frame rate

# Ensure the save directory exists
if not os.path.exists(save_directory):
    os.makedirs(save_directory)

# Utility function to save an image
def save_image(img):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}.jpg"
    filepath = os.path.join(save_directory, filename)
    cv2.imwrite(filepath, img)
    logging.info(f"Saved image at {filepath}")

# Utility function to retrieve and decode an image
def retrieve_and_decode_image(image_url):
    try:
        response = requests.get(image_url)
        img_array = np.array(bytearray(response.content), dtype=np.uint8)
        img = cv2.imdecode(img_array, -1)
        return img
    except Exception as e:
        logging.error(f"Failed to retrieve image: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/snapshot')
def snapshot():
    ip_address = request.args.get('ip_address')
    image_url = f"http://{ip_address}/snapshot.jpg"
    
    img = retrieve_and_decode_image(image_url)

    if img is not None:
        _, buffer = cv2.imencode('.jpg', img)
        img_str = base64.b64encode(buffer).decode('utf-8')
        logging.info(f"Image data size: {len(img_str)}")

        # Existing logic for time-based filtering and saving can go here
        start_time_str = request.args.get('start_time')
        end_time_str = request.args.get('end_time')
        save_image_flag = True  # Initialize a flag to determine if the image should be saved
        
        if start_time_str or end_time_str:
            now = datetime.datetime.now()
            
            if start_time_str:
                start_time = datetime.datetime.fromisoformat(start_time_str)
                if now < start_time:
                    save_image_flag = False  # Don't save if the current time is before the start time
            
            if end_time_str:
                end_time = datetime.datetime.fromisoformat(end_time_str)
                if now > end_time:
                    save_image_flag = False  # Don't save if the current time is after the end time

        if save_image_flag:
            save_image(img)

        return jsonify({'status': 'success', 'image': img_str})
    else:
        return jsonify({'status': 'failure', 'error': 'Image not available'})

@app.route('/list_images')
def list_images():
    files = os.listdir(save_directory)
    return jsonify({'images': files})

@app.route('/download_images')
def download_images():
    zip_path = os.path.join(current_directory, 'saved_images.zip')
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:  # Use zipfile.ZIP_DEFLATED
        for root, dirs, files in os.walk(save_directory):
            for file in files:
                zipf.write(os.path.join(root, file), file)
    
    # Read the ZIP into memory
    with open(zip_path, 'rb') as f:
        zip_data = f.read()

    # Create a response with the ZIP data and appropriate headers for downloading
    response = make_response(zip_data)
    response.headers.set('Content-Type', 'application/zip')
    response.headers.set('Content-Disposition', 'attachment', filename='saved_images.zip')

    return response

@app.route('/saved_images/<filename>')
def serve_image(filename):
    return send_from_directory(save_directory, filename)

@app.route('/download_gif')
def download_gif():
    frame_rate = request.args.get('frame_rate', default=FRAME_RATE, type=int)
    frame_rate = max(1, min(frame_rate, 30))  # Limit frame rate between 1 and 30
    logging.info(f"Inside /download_gif with frame_rate = {frame_rate}")

    # Logic to gather image paths
    image_paths = [os.path.join(save_directory, filename) for filename in os.listdir(save_directory)]
    image_paths.sort()

    gif_path = os.path.join(save_directory, 'animated.gif')  # Full path
    clip = ImageSequenceClip(image_paths, fps=frame_rate)
    clip.write_gif(gif_path)

    # Read the GIF into memory
    with open(gif_path, 'rb') as f:
        gif_data = f.read()

    # Create a response with the GIF data and appropriate headers for downloading
    response = make_response(gif_data)
    response.headers.set('Content-Type', 'image/gif')
    response.headers.set('Content-Disposition', 'attachment', filename='animated.gif')

    return response

@app.route('/download_video')
def download_video():
    frame_rate = request.args.get('frame_rate', default=FRAME_RATE, type=int)
    frame_rate = max(1, min(frame_rate, 30))  # Limit frame rate between 1 and 30
    
    logging.info(f"Inside /download_video with frame_rate = {frame_rate}")

    # Logic to gather image paths
    image_paths = [os.path.join(save_directory, filename) for filename in os.listdir(save_directory)]
    image_paths.sort()

    # Initialize video writer
    frame = cv2.imread(image_paths[0])
    height, width, layers = frame.shape
    size = (width, height)
    video_path = os.path.join(current_directory, 'video.avi')  # Full path
    out = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*'DIVX'), frame_rate, size)

    # Write frames to video
    for image_path in image_paths:
        frame = cv2.imread(image_path)
        out.write(frame)

    out.release()

    if os.path.exists(video_path):
        logging.info(f"{video_path} exists, sending file.")
        return send_from_directory(current_directory, 'video.avi')
    else:
        logging.info(f"{video_path} does not exist.")
        return jsonify({'status': 'failure', 'error': 'Video could not be created'})

@app.route('/clear_images')
def clear_images():
    for filename in os.listdir(save_directory):
        file_path = os.path.join(save_directory, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            logging.error(f"Failed to delete {file_path}. Reason: {e}")
    return jsonify({'status': 'success'})

@app.route('/images/<filename>')
def serve_placeholder_image(filename):
    return send_from_directory('images', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
