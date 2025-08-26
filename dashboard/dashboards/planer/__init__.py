import importlib
import shutil

from flask import Blueprint, render_template, jsonify, current_app
import os
from data_sources.DataEndpoint import DataEndpoint

# Define a Blueprint for this dashboard
blueprint = Blueprint('planer', __name__,
                      template_folder='templates',
                      static_folder='static')

# Remove the temporary data
temp_data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '.temp_data')
if os.path.exists(temp_data_dir):
    shutil.rmtree(temp_data_dir)
os.mkdir(temp_data_dir)

@blueprint.route('/')
def dashboard():

    # url_prefix = get_blueprint_url_prefix(blueprint)
    # Render the template and pass the data to it
    return render_template('dashboard.html', url_prefix="dashboard/0")


def get_blueprint_url_prefix(blueprint):
    """Return the url_prefix of a given blueprint"""
    for bp_name, bp in current_app.blueprints.items():
        if bp == blueprint:
            # Extract the url_prefix from the URL map
            return next((rule.rule for rule in current_app.url_map.iter_rules() if rule.endpoint.startswith(bp_name + '.api')), None).removesuffix('/<string:dataEndpoint>')
    return None
