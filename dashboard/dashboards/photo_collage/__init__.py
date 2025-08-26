import shutil
import os
import io
from random import random, randint

import qrcode
from flask import Blueprint, render_template, jsonify, send_file

# Define a Blueprint for the Party Collage dashboard
blueprint = Blueprint('photo_collage', __name__,
                      template_folder='templates',
                      static_folder='static')

# Optional: cleanup any temporary files (like you do in planer)
temp_data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '.temp_data')
if os.path.exists(temp_data_dir):
    shutil.rmtree(temp_data_dir)
os.mkdir(temp_data_dir)

# Dummy photos (replace with real storage later)


@blueprint.route('/')
def dashboard():
    return render_template('photo_collage.html')

@blueprint.route('/api/photos')
def api_photos():
    DUMMY_PHOTOS = []
    for i in range(randint(6, 30)):
        DUMMY_PHOTOS.append("https://picsum.photos/400?random=" + str(i))

    return jsonify(DUMMY_PHOTOS)

@blueprint.route('/qrcode')
def qr_code():
    # Generate QR code pointing to upload endpoint
    img = qrcode.make("http://localhost:5000/dashboard/0/upload")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")

@blueprint.route('/upload')
def upload_page():
    return render_template('photo_upload.html')
