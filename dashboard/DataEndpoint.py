from datetime import datetime
from flask import jsonify
from threading import Thread
from abc import ABC, abstractmethod
import json
import hmac
import hashlib


class DataEndpoint(ABC):
    """
    Base class for API modules. Includes socket handling and shared functionality.
    """
    def __init__(self, temp_data_dir, secret_key):
        """
        Initializes the BaseAPI instance with a temporary data directory and a secret key.

        :param temp_data_dir: Path to the directory for temporary data storage.
        :param secret_key: Secret key for encryption or authentication.
        """
        from extensions import socketio
        self.socketio = socketio
        self.temp_data_dir = temp_data_dir
        self.secret_key = secret_key# Set up a Socket.IO server
        self.last_data = None  # Tracks the most recent data state
        self._start_socket_monitor()

    def _start_socket_monitor(self):
        """
        Starts a thread to monitor data changes and emits updates through the socket.
        """
        self.socketio.on('connect')(self._handle_connect)
        self.socketio.on('disconnect')(self._handle_disconnect)
        monitor_thread = Thread(target=self._monitor_updates, daemon=True)  # Run in background
        monitor_thread.start()

    def _handle_connect(self):
        """
        Handles a new client connection.
        """
        print('Client connected!')

    def _handle_disconnect(self):
        """
        Handles client disconnection.
        """
        print('Client disconnected!')

    def _monitor_updates(self):
        """
        Continuously monitors for data changes and emits updates through the socket.
        This method should be overridden in subclasses to implement specific monitoring logic.
        """
        while True:
            data = self.get_data()  # Fetch the latest data
            if data != self.last_data:  # Check if the data has changed
                self.last_data = data
                self.socketio.emit(self.get_endpoint_name() + '_update', data)  # Broadcast updates
            self.socketio.sleep(90)  # Check for updates every 90 seconds

    @abstractmethod
    def get_data(self):
        """
        Must be implemented by the subclass.
        Retrieves the current data for the API.
        """
        pass

    @abstractmethod
    def get_endpoint_name(self):
        """
        Must be implemented by the subclass.
        Returns the name of the endpoint for the API.
        """
        pass

    def fetch_data(self, last_update_time=None):
        """
        API endpoint to fetch the latest data.

        :param last_update_time: Timestamp of the last data retrieval, if applicable.
        :return: JSON response containing the endpoint data or an error message.
        """
        data = self.get_data()  # Retrieve current data
        # temp_data_file = os.path.join(self.temp_data_dir, f"{self.get_endpoint_name()}.json")

        # Load the last saved data if available
        # if os.path.exists(temp_data_file):
        #     last_data = self._read_dict_from_json(temp_data_file)
        # else:
        #     self._write_dict_to_json(data, temp_data_file)
        #
        # self._write_dict_to_json(data, temp_data_file)  # Update saved data

        # Return 304 if there is no new data
        # if data == self.last_data:
        #     return "No new data", 304

        self.last_data = data

        # Return updated data
        return jsonify({
            "endpoint": self.get_endpoint_name(),
            "last_update_time": datetime.now().timestamp(),
            "data": data
        }), 200

    def _write_dict_to_json(self, data, file_path, secret_key):
        """
        Writes a dictionary to a JSON file and signs it with a secret key.

        :param data: Dictionary to be written to the file.
        :param file_path: Path to the JSON file.
        :param secret_key: Secret key for signing the file.
        :return: Signature of the file.
        """
        # Write the JSON data to the file
        with open(file_path, 'w') as json_file:
            print(json_file)
            json.dump(data, json_file, indent=4)

        # Read the file and compute the signature
        with open(file_path, 'rb') as json_file:
            file_content = json_file.read()
            signature = hmac.new(secret_key.encode(), file_content, hashlib.sha256).hexdigest()

        # Save the signature in a separate file
        signature_path = file_path + ".sig"
        with open(signature_path, 'w') as sig_file:
            sig_file.write(signature)

        print(f"JSON file saved at: {file_path}")
        print(f"Signature saved at: {signature_path}")
        return signature

    def _read_dict_from_json(file_path, secret_key):
        """
        Reads a JSON file and validates its integrity using the HMAC signature.

        :param file_path: Path to the JSON file.
        :param secret_key: Secret key for verifying the file.
        :return: The dictionary from the JSON file if the signature is valid, otherwise raises an exception.
        """
        # Read the JSON file content
        with open(file_path, 'rb') as json_file:
            file_content = json_file.read()

        # Compute the expected signature
        expected_signature = hmac.new(secret_key.encode(), file_content, hashlib.sha256).hexdigest()

        # Read the actual signature from the .sig file
        signature_path = file_path + ".sig"
        try:
            with open(signature_path, 'r') as sig_file:
                actual_signature = sig_file.read().strip()
        except FileNotFoundError:
            raise Exception(f"Signature file not found: {signature_path}")

        # Validate the signature
        if not hmac.compare_digest(expected_signature, actual_signature):
            raise Exception("Signature verification failed! The file may have been tampered with.")

        # If valid, parse and return the JSON data
        with open(file_path, 'r') as json_file:
            data = json.load(json_file)

        print(f"File integrity verified: {file_path}")
        return data