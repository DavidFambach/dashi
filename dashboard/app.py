from extensions import app, socketio
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Determine base directory (where this script is located)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Add base directory to Python path to allow dynamic imports from 'dashboards' package
sys.path.insert(0, os.path.join(BASE_DIR, 'dashboards'))
sys.path.insert(0, os.path.dirname(BASE_DIR))

# load dashboards dynamically
def register_dashboards(app, dashboard_path='dashboards'):
    i = 0
    for dashboard_name in os.listdir(dashboard_path):
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

register_dashboards(app)

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", debug=False, allow_unsafe_werkzeug=True)

