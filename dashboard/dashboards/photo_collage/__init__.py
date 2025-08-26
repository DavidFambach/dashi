import shutil
import os
from random import randint

from flask import Blueprint, render_template, jsonify

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

@blueprint.route('/upload')
def upload_page():
    return render_template('photo_upload.html')
