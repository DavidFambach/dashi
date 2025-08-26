from extensions import app, socketio
import importlib

from functools import partial

from data_sources.DataEndpoint import DataEndpoint
from flask import Blueprint, jsonify, redirect

import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

datasources = {}

import logging
import sys

# Configure root logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)

# Avoid adding multiple handlers if already configured
if not logger.hasHandlers():
    logger.addHandler(console_handler)


def load_datasources():
    data_source_dir = os.path.join(os.path.dirname(__file__), 'data_sources')
    for root, _, files in os.walk(data_source_dir):
        if '__init__.py' in files:
            module_path = os.path.relpath(root, os.path.dirname(__file__)).replace(os.path.sep, ".")

            module = importlib.import_module(module_path)
            for attr in dir(module):
                obj = getattr(module, attr)

                if isinstance(obj, type) and issubclass(obj, DataEndpoint) and obj != DataEndpoint:
                    # Instantiate the class
                    instance = obj(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".temp_data"),
                                   "SecretKey")  # Hier können Sie ggf. Parameter an die Klasse übergeben
                    # Register the fetch_data method
                    datasources[instance.get_endpoint_name()] = instance.fetch_data
                    endpoint_name = instance.get_endpoint_name()
                    print(f"Registered data endpoint: {endpoint_name}")

                    app.add_url_rule(
                        f"/api/{endpoint_name}",
                        endpoint=endpoint_name,
                        view_func=partial(route_handler, instance=instance),
                        methods=["GET"]
                    )


def route_handler(instance):
    """Behandelt die Routenanfragen."""
    return instance.fetch_data()


# load dashboards dynamically
def register_dashboards(app, dashboard_path='dashboards'):
    i = 0
    for dashboard_name in os.listdir(dashboard_path):
        if dashboard_name == "__pycache__":
            continue
        dashboard_folder = os.path.join(dashboard_path, dashboard_name)
        if os.path.isdir(dashboard_folder):
            try:
                # import dashboard blueprint
                print(f'{dashboard_path}.{dashboard_name}')
                module = __import__(f'{dashboard_path}.{dashboard_name}', fromlist=['blueprint'])
                app.register_blueprint(module.blueprint, url_prefix=f'/dashboard/{i}')
                print(f"Registered dashboard: {dashboard_name}")
                i += 1
            except ImportError as e:
                print(f"Failed to load {dashboard_name}: {e}")


@app.route('/')
def root():
    return redirect('/dashboard/0/', code=302)


load_datasources()
register_dashboards(app)

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", debug=True, use_reloader=False)
