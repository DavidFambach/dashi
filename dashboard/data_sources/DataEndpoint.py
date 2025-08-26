import logging
from datetime import datetime
from threading import Thread
from abc import ABC, abstractmethod
from flask import jsonify, request

print(logging.root.manager.loggerDict)

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
        self.client_info = {}
        self._start_socket_monitor()

    def _start_socket_monitor(self):
        """
        Starts a thread to monitor data changes and emits updates through the socket.
        """
        logging.info('Starting socket monitor...')
        self.socketio.on('connect')(self._handle_connect)
        self.socketio.on('disconnect')(self._handle_disconnect)
        monitor_thread = Thread(target=self._monitor_updates, daemon=True)  # Run in background
        monitor_thread.start()
        logging.info('Socket monitor started in a separate thread.')

    def _handle_connect(self):
        """
        Handles a new client connection.
        Logs details about the connected client.
        """
        client_sid = request.sid
        client_ip = request.remote_addr
        self.client_info[client_sid] = {'ip': client_ip}
        logging.info(f'Client connected! SID: {client_sid}, IP: {client_ip}')

    def _handle_disconnect(self):
        """
        Handles client disconnection.
        Logs details about the disconnected client.
        """
        client_sid = request.sid
        if client_sid in self.client_info:
            client_ip = self.client_info[client_sid]['ip']
            logging.info(f'Client disconnected! SID: {client_sid}, IP: {client_ip}')
            del self.client_info[client_sid]  # Clean up the stored info
        else:
            logging.warning(f'Client SID: {client_sid} not found during disconnect.')

    def _monitor_updates(self):
        """
        Continuously monitors for data changes and emits updates through the socket.
        This method should be overridden in subclasses to implement specific monitoring logic.
        """
        while True:
            data = self.get_data()  # Fetch the latest data
            if data != self.last_data:  # Check if the data has changed
                self.last_data = data
                self.socketio.emit(self.get_endpoint_name() + '_update', data)
                print(self.get_endpoint_name() + " updated")# Broadcast updates
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

    def fetch_data(self):
        """
        API endpoint to fetch the latest data.

        :param last_update_time: Timestamp of the last data retrieval, if applicable.
        :return: JSON response containing the endpoint data or an error message.
        """
        data = self.get_data()  # Retrieve current data
        self.last_data = data

        print(logging.root.manager.loggerDict)

        # Return updated data
        return jsonify({
            "endpoint": self.get_endpoint_name(),
            "last_update_time": datetime.now().timestamp(),
            "data": data
        }), 200
