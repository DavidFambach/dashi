import shutil
import os

from flask import Blueprint, render_template

# Define a Blueprint for the Party Collage dashboard
blueprint = Blueprint('photo_collage', __name__,
                      template_folder='templates',
                      static_folder='static')

# Optional: cleanup any temporary files (like you do in planer)
temp_data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '.temp_data')
if os.path.exists(temp_data_dir):
    shutil.rmtree(temp_data_dir)
os.mkdir(temp_data_dir)

@blueprint.route('/')
def dashboard():
    return render_template('photo_collage.html')
