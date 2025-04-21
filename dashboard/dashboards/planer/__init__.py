import importlib
import shutil

from flask import Blueprint, render_template, jsonify, current_app
import os
from dashboard.DataEndpoint import DataEndpoint

# Define a Blueprint for this dashboard1
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

    url_prefix = get_blueprint_url_prefix(blueprint)
    # Render the template and pass the data to it
    return render_template('dashboard1.html', url_prefix=url_prefix)


@blueprint.route('/api/<string:dataEndpoint>')
def api(dataEndpoint):
    """
    API endpoint that dynamically handles requests for all loaded data sources.

    :param dataEndpoint: The name of the data source module (e.g., 'external_api')
    :return: JSON response containing the requested data or an error message
    """
    # Get the fetch_data function for the requested data endpoint
    fetch_function = data_source_names.get(dataEndpoint)
    if not fetch_function:
        # Return a 404 error if the data endpoint is unknown
        return jsonify({"error": "Unknown data endpoint"}), 404

    # Call the fetch_data function and handle any errors
    try:
        data = fetch_function()
        return data
    except Exception as e:
        # Return a 500 error if the fetch_data function fails
        return jsonify({"error": str(e)}), 500

# Dictionary to hold dynamically loaded data source modules
data_source_names = {}

# Path to the data_sources folder
data_sources_path = os.path.join(os.path.dirname(__file__), 'data_sources')

# Dynamically load all modules in the data_sources folder
for filename in os.listdir(data_sources_path):
    if filename.endswith('.py') and filename != '__init__.py':  # Ignore __init__.py
        module_name = filename[:-3]  # Remove '.py' from the filename
        try:
            # Import the module
            module = importlib.import_module(f'dashboards.planer.data_sources.{module_name}')

            # Look for classes in the module that inherit from DataEndpoint
            attr = getattr(module, module_name)
            if isinstance(attr, type) and issubclass(attr, DataEndpoint) and attr is not DataEndpoint:
                # Instantiate the class
                instance = attr(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".temp_data"), "SecretKey")  # Hier können Sie ggf. Parameter an die Klasse übergeben
                # Register the fetch_data method
                data_source_names[instance.get_endpoint_name()] = instance.fetch_data
                print(f"Registered data endpoint: {instance.get_endpoint_name()}")

        except Exception as e:
            # Log any errors during the module loading process
            print(f"Error loading module {module_name}: {e}")


def get_blueprint_url_prefix(blueprint):
    """Return the url_prefix of a given blueprint"""
    for bp_name, bp in current_app.blueprints.items():
        if bp == blueprint:
            # Extract the url_prefix from the URL map
            return next((rule.rule for rule in current_app.url_map.iter_rules() if rule.endpoint.startswith(bp_name + '.api')), None).removesuffix('/<string:dataEndpoint>')
    return None