import asyncio
import websockets
import json
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
import os
import threading

# Configuration
PRINTER_IP = "127.0.0.1"
FTP_PORT = 21
WEBSOCKET_PORT = 18188
FTP_DIRECTORY = './mock_ftp'
MMC_DIRECTORY = '/media/mmcblk0p3'

# Mock FTP Handler
class MockFTPHandler(FTPHandler):
    def on_connect(self):
        print(f"{self.remote_ip}:{self.remote_port} connected")

    def on_disconnect(self):
        print(f"{self.remote_ip}:{self.remote_port} disconnected")

    def on_login(self, username):
        print(f"{username} logged in")

    def on_logout(self, username):
        print(f"{username} logged out")

    def on_file_received(self, file):
        print(f"File received: {file}")

    def on_file_sent(self, file):
        print(f"File sent: {file}")

    def on_incomplete_file_received(self, file):
        print(f"Incomplete file received: {file}")
        os.remove(file)

    def on_incomplete_file_sent(self, file):
        print(f"Incomplete file sent: {file}")

# Global variable to track the printing status
printing_status = {
    'printStatus': 'IDLE',
    'sliceLayerCount': 0,
    'curSliceLayer': 0
}

# Event to control pausing and resuming
pause_event = asyncio.Event()
pause_event.set()  # Initially not paused

# Function to simulate the printing process
async def simulate_printing():
    global printing_status
    while printing_status['curSliceLayer'] < printing_status['sliceLayerCount']:
        await pause_event.wait()  # Wait if paused
        if printing_status['printStatus'] == 'PRINT_STOPPED':
            printing_status['curSliceLayer'] = 0
            print("Printing stopped.")
            return
        await asyncio.sleep(1)  # Simulate time taken to print each layer
        printing_status['curSliceLayer'] += 1
        print(f"Printing layer {printing_status['curSliceLayer']} of {printing_status['sliceLayerCount']}")
    printing_status['printStatus'] = 'PRINT_COMPLETING'
    printing_status['printStatus'] = 'PRINT_COMPLETED'
    print("Printing completed.")

# Mock WebSocket Server
async def mock_websocket_handler(websocket):
    global printing_status
    async for message in websocket:
        print(f"Received message: {message}")
        data = json.loads(message)
        response = {}

        if data['cmd'] == 'START_PRINT':
            printing_status = {
                'printStatus': 'PRINT_PROCESSING',
                'sliceLayerCount': 100,
                'curSliceLayer': 0
            }
            response = printing_status
            pause_event.set()  # Resume if paused
            asyncio.create_task(simulate_printing())
        elif data['cmd'] == 'GET_PRINT_STATUS':
            response = printing_status
        elif data['cmd'] == 'PRINT_PAUSE':
            printing_status['printStatus'] = 'PRINT_PAUSED'
            pause_event.clear()  # Pause the printing process
            response = {'status': 'paused'}
        elif data['cmd'] == 'PRINT_STOP':
            printing_status['printStatus'] = 'PRINT_STOPPED'
            pause_event.set()  # Ensure the printing process can stop
            response = {'status': 'IDLE'}
        if json.dumps(response) != "{}":
            await websocket.send(json.dumps(response))
            print(f"Sent response: {json.dumps(response)}")
        else:
            print("No response sent")

# Setup FTP Server
def setup_ftp_server():
    authorizer = DummyAuthorizer()
    authorizer.add_anonymous(homedir=FTP_DIRECTORY, perm='elradfmwMT')

    handler = MockFTPHandler
    handler.authorizer = authorizer

    server = FTPServer((PRINTER_IP, FTP_PORT), handler)
    return server

# Setup WebSocket Server
async def setup_websocket_server():
    async with websockets.serve(mock_websocket_handler, PRINTER_IP, WEBSOCKET_PORT):
        await asyncio.Future()  # Run forever

# Main function to start the mock servers
def main():
    if not os.path.exists(FTP_DIRECTORY):
        os.makedirs(FTP_DIRECTORY)

    if not os.path.exists(FTP_DIRECTORY + MMC_DIRECTORY):
        os.makedirs(FTP_DIRECTORY + MMC_DIRECTORY)

    ftp_server = setup_ftp_server()
    ftp_thread = threading.Thread(target=ftp_server.serve_forever, daemon=True)
    ftp_thread.start()

    print(f"Mock FTP server running on {PRINTER_IP}:{FTP_PORT}")
    print(f"Mock WebSocket server running on {PRINTER_IP}:{WEBSOCKET_PORT}")

    asyncio.run(setup_websocket_server())

if __name__ == "__main__":
    main()