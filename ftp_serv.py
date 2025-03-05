from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
from pyftpdlib.authorizers import DummyAuthorizer
from ftplib import FTP
import asyncio
from websockets.asyncio.client import connect
from Crypto.Cipher import DES
import json
from tqdm import tqdm

import sys
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import threading

from PyQt5.QtCore import Qt, QThread, pyqtSignal, Q_ARG
from PyQt5.QtWidgets import QApplication, QMainWindow, QLineEdit, QVBoxLayout, QWidget, QTextEdit, QDesktopWidget, QGraphicsObject
from PyQt5.QtGui import QCloseEvent, QFont
import io

from PyQt5.QtCore import QThread, QMetaObject, Qt

import os

from win32com.client import Dispatch

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import webbrowser
import toml

import docker_start
import get_token
import install_docker
import mock_server

class FtpUploadTracker(QThread):
    totalSize = 0
    progress_bar = None
    progress_output = None
    update_signal = pyqtSignal(str)  # Signal to update the text output
    
    def __init__(self, totalSize):
        super().__init__()
        self.totalSize = round(totalSize/1000000, 2)
        self.progress_output = io.StringIO()
        self.progress_output.truncate(0)
        self.progress_output.seek(0)
        self.progress_bar = tqdm(bar_format = '{desc}: {percentage:3.2f}%|{bar}| {n:.2f}/{total:.2f} [{elapsed}<{remaining}, {rate_fmt}]',
                                  total=self.totalSize, unit="MB",
                                  ncols=100,
                                  disable=False,
                                  ascii=False,
                                  file=self.progress_output)
        self.handle(0)

    def handle(self, block):
        self.progress_bar.update(1024/1000000)
        self.update_signal.emit(self.progress_output.getvalue())
        self.progress_output.seek(0)

class PrintTracker(QThread):
    totalSize = 0
    progress_bar = None
    progress_output = None
    update_signal = pyqtSignal(str)  # Signal to update the text output
    
    def __init__(self, totalSize):
        super().__init__()
        self.totalSize = totalSize
        self.progress_output = io.StringIO()
        self.progress_output.truncate(0)
        self.progress_output.seek(0)
        self.progress_bar = tqdm(bar_format = '{desc}: {percentage:3.2f}%|{bar}| {n:.2f}/{total:.2f} [{elapsed}<{remaining}, {rate_fmt}]',
                                  total=self.totalSize, unit="lines",
                                  ncols=100,
                                  disable=False,
                                  ascii=False,
                                  file=self.progress_output)
        
        self.handle(0)
        

    def handle(self, block):
        self.progress_bar.n = block
        self.progress_bar.refresh()
        self.update_signal.emit(self.progress_output.getvalue())
        self.progress_output.seek(0)
        self.progress_output.truncate(0)
        
        

class MyHandler(FTPHandler):

    def upload(self):
        loop = asyncio.new_event_loop()
        tasks = [
            loop.create_task(start_print2())
        ]
        loop.run_until_complete(asyncio.wait(tasks))
        loop.close()

    def on_connect(self):
        print("%s:%s connected" % (self.remote_ip, self.remote_port))

    uploadTracker = FtpUploadTracker

    def on_file_received(self, file):
        ftp = FTP(printer_ip)
        ftp.login()
        ftp.cwd('media/mmcblk0p3')
        listout = ftp.nlst()
        if listout.__len__() > 0:
            for i in range(listout.__len__()):
                print(listout[i])
                ftp.delete(listout[i])

        uploadTracker = FtpUploadTracker(int(os.path.getsize(file)))
        window.setSignal(uploadTracker.update_signal)
        window.show_window()
        ftp.storbinary(f'STOR {os.path.split(file)[1]}', open(file, 'rb'), 1024, uploadTracker.handle)

        window.hide_window()

        ftp.quit()
        os.remove(file)

        print("File received")
        #self.upload()


def on_incomplete_file_sent(self, file):
    # do something when a file is partially sent
    pass

def on_incomplete_file_received(self, file):
    # remove partially uploaded files
    import os
    os.remove(file)

def create_tray_icon():
    icon = pystray.Icon("test_icon", create_image(),
        menu=pystray.Menu(
            item('Open Folder', on_open_folder),
            pystray.Menu.SEPARATOR,
            item('Start', on_start),
            item('Pause', on_pause),
            item('Stop', on_stop),
            item('Status', on_status),
            pystray.Menu.SEPARATOR,
            item('Quit', on_quit)
            ))
    icon.run()

async def start_print2():
    async with connect("ws://" + printer_ip + ":18188") as websocket:
        ftp = FTP(printer_ip)
        ftp.login()
        ftp.cwd('media/mmcblk0p3') 
        listout = ftp.nlst()
        ftp.quit()
        if listout.__len__() > 0:
            dict2 = {'cmd':'START_PRINT', 'token':config['printer']['token'],'filename': listout[0]}
            out = json.dumps(dict2)
            await websocket.send(out)
            await websocket.recv()
        else:
            return 
    await asyncio.sleep(5)
    status = await get_status()
    num_lines = status['sliceLayerCount']
    printTracker = PrintTracker(int(num_lines))
    window.setSignal(printTracker.update_signal)
    window.show_window()
    while window.isHidden() == True:
        await asyncio.sleep(0.1)
    while status['printStatus'] == 'PRINT_PROCESSING' or status['printStatus'] == 'PRINT_PAUSED' or status['printStatus'] == 'PRINT_COMPLETING': 
        if window.isHidden():
            return
        printTracker.handle(int(status['curSliceLayer']))
        await asyncio.sleep(1)
        status = await get_status()

    window.hide_window()

async def get_status():
    async with connect("ws://" + printer_ip + ":18188") as websocket:
        dict1 ={'cmd':'GET_PRINT_STATUS', 'token':config['printer']['token']}
    
        out = json.dumps(dict1)
        print("sending status request")
        await websocket.send(out)
        message = await websocket.recv()
        print(message)
        received = json.loads(message)
        return received


def on_quit(icon, item):
    icon.stop()

def on_open_folder(icon, item):
    abs_path = os.path.abspath('./ftp')
    webbrowser.open(f'file://{abs_path}')

def on_status(icon, item):
    background_thread4 = threading.Thread(target=show_status_task, daemon=True)
    background_thread4.start()

def on_start(icon, item):
    background_thread3 = threading.Thread(target=start_print_task, daemon=True)
    background_thread3.start()

def show_status_task():
    loop = asyncio.new_event_loop()
    tasks = [
        loop.create_task(show_status())
    ]
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close() 

async def show_status():

    if window.isHidden() == False:
        return
    
    print("getting status")
    status = await asyncio.wait_for(get_status(), timeout=5)
    print("received status")
    print(status)
    if status['printStatus'] not in ['PRINT_PROCESSING', 'PRINT_PAUSED', 'PRINT_COMPLETING']:
        return
    num_lines = status['sliceLayerCount']
    print(num_lines)
    printTracker = PrintTracker(int(num_lines))
    window.setSignal(printTracker.update_signal)
    window.show_window()
    while window.isHidden() == True:
        await asyncio.sleep(0.1)
    while (status['printStatus'] == 'PRINT_PROCESSING' or status['printStatus'] == 'PRINT_PAUSED' or status['printStatus'] == 'PRINT_COMPLETING'): 
        if window.isHidden():
            return
        print(status['curSliceLayer'])
        printTracker.handle(int(status['curSliceLayer']))
        await asyncio.sleep(1)
        status = await get_status()

    window.hide_window()

def start_print_task():
    loop = asyncio.new_event_loop()
    tasks = [
        loop.create_task(start_print2())
    ]
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()    

def on_pause(icon, item):
    loop = asyncio.new_event_loop()
    tasks = [
        loop.create_task(pause_print())
    ]
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()

async def pause_print():
    async with connect("ws://" + printer_ip + ":18188") as websocket:
        dict1 ={'cmd':'PRINT_PAUSE', 'token':config['printer']['token']}
    
        out = json.dumps(dict1)
        print(out)
        await websocket.send(out)

def on_stop(icon, item):
    loop = asyncio.new_event_loop()
    tasks = [
        loop.create_task(stop_print())
    ]
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()

async def stop_print():
    async with connect("ws://" + printer_ip + ":18188") as websocket:
        dict1 ={'cmd':'PRINT_STOP', 'token':config['printer']['token']}
    
        out = json.dumps(dict1)
        print(out)
        await websocket.send(out)

def create_image():
    # Generate an image with Pillow
    width = 64
    height = 64
    image = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.rectangle(
        (0, 0, width, height), fill=(0, 128, 255)
    )
    return image

def background_task():

    

    authorizer = DummyAuthorizer()
    #authorizer.add_user('user', '12345', homedir='.', perm='elradfmwMT')
    authorizer.add_anonymous(homedir='./ftp',  perm='elradfmwMT')

    handler = MyHandler
    handler.authorizer = authorizer
    server = FTPServer(('127.0.0.1', 21), handler)
    server.serve_forever()


# Main Window Class
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Starting Print")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        # Create a QTextEdit widget for displaying progress
        QFont
        self.text_edit = QLineEdit(self)
        self.text_edit.setReadOnly(True)  # Make the text box read-only
        self.text_edit.setAlignment(Qt.AlignTop)  # Align text to top

        # Set the background color to black and the text color to white
        self.text_edit.setStyleSheet("background-color: black; color: white;")

        # Set the font to a monospaced font (like Consolas or Courier)
        font = QFont("Courier New", 10)
        self.text_edit.setFont(font)

        # Create a layout and add the QTextEdit widget
        layout = QVBoxLayout()
        layout.addWidget(self.text_edit)

        # Create a container widget for the layout
        container = QWidget()
        container.setLayout(layout)

        self.setCentralWidget(container)
        # Center the window on the screen

        container.setStyleSheet("background-color: black;")
        self.setStyleSheet("background-color: black;")

        # Start the progress thread
        #self.progress_thread = ProgressThread()
        #signal.connect(self.update_text)
        #self.progress_thread.start()

        # Flag to prevent repeated centering
        self.is_centered = False

    def closeEvent(self, event: QCloseEvent):
        event.ignore() # Ignores the close event, keeping the window open
        # Optionally, hide the window instead of closing
        self.hide()

    def setSignal(self, signal):
         signal.connect(self.update_text)

    def center_window(self):
        """Center the window on the screen."""
        # Get the desktop's available geometry (screen's size)
        screen_geom = QDesktopWidget().screenGeometry()

        # Get the window's geometry (current size and position)
        window_geom = self.frameGeometry()

        # Calculate the center position by subtracting half of the window's width and height from the screen's width and height
        center_pos = screen_geom.center() - window_geom.center()/3

        print(str(screen_geom))

        # Move the window to the calculated position
        self.move(center_pos)

    def update_text(self, text):
        """Updates the QTextEdit with the progress information."""
        
        print("updating text " + text)
        QMetaObject.invokeMethod(self.text_edit, "setText", Qt.QueuedConnection, Q_ARG(str, text))
        #self.text_edit.setText(text)  # Overwrite the text each time with new progress
        
        # Resize the window based on the text width
        #if self.has_ran == False:
        
      #      self.has_ran = True

        if not self.is_centered:
            self.adjust_window_size(text)
            print(text)
            self.center_window()
            self.is_centered = True  # Prevent further centering

    def show_window(self):
        # Call show() safely using invokeMethod to ensure it's done in the main thread
        QMetaObject.invokeMethod(self, "show", Qt.QueuedConnection)

    def hide_window(self):
        # Call show() safely using invokeMethod to ensure it's done in the main thread
        QMetaObject.invokeMethod(self, "hide", Qt.QueuedConnection)

    def adjust_window_size(self, text):
        """Adjust the window size based on the number of characters and the width of a single character."""
        # Get the font metrics of the text edit widget
        
        print("hello")
        
        font_metrics = self.text_edit.fontMetrics()

        # Calculate the width of a single character
        char_width = font_metrics.horizontalAdvance("M")  # 'M' is typically the widest character in monospace fonts

        # Calculate the height of a single line
        char_height = font_metrics.height()  # This is the height of a single line of text

        # Calculate the width based on the number of characters in the text
        text_width = char_width * len(text)  # Number of characters in the text * width of each character

        # Get the window frame margins to calculate padding
        frame_geom = self.frameGeometry()
        frame_width = frame_geom.width() - self.width()
        frame_height = frame_geom.height() - self.height()

        # Calculate the exact padding based on the window's current geometry
        padding_width = frame_width + 50  # Horizontal padding based on window's frame
        padding_height = frame_height + 50  # Vertical padding based on window's frame

        # Update the window width and height to ensure all content is visible
        window_width = text_width + padding_width  # Include horizontal padding
        window_height = char_height + padding_height  # Include vertical padding

        # Ensure the window size is reasonable and large enough to display the text
        self.resize(window_width, window_height)
        self.setFixedSize(window_width, window_height)  # Prevent user from resizing

def background_task2():
    create_tray_icon()
    os._exit(0)  

def createLink():
    # Define FTP details
    ftp_url = "ftp://127.0.0.1"  # Replace with actual FTP details
    network_location_name = "halot mage s"

    # Network Shortcuts path (This is where Windows stores Network Locations)
    network_shortcuts_path = os.path.join(os.getenv('APPDATA'), "Microsoft\\Windows\\Network Shortcuts")

    # Ensure the folder exists
    os.makedirs(network_shortcuts_path, exist_ok=True)

    # Define the full shortcut path
    shortcut_path = os.path.join(network_shortcuts_path, f"{network_location_name}.lnk")

    # Create a Windows Shell Shortcut
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortcut(shortcut_path)
    shortcut.TargetPath = ftp_url
    shortcut.Save()

    print(f"FTP Network Location '{network_location_name}' added successfully!")

class FileCreatedHandler(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback

    def on_created(self, event):
        if not event.is_directory:
            self.callback(event.src_path)

def file_added_callback(file_path):
    ftp = FTP(printer_ip)
    ftp.login()
    ftp.cwd('media/mmcblk0p3')
    listout = ftp.nlst()
    if listout.__len__() > 0:
        for i in range(listout.__len__()):
            print(listout[i])
            ftp.delete(listout[i])

    uploadTracker = FtpUploadTracker(int(os.path.getsize(file_path)))
    window.setSignal(uploadTracker.update_signal)
    window.show_window()
    ftp.storbinary(f'STOR {os.path.split(file_path)[1]}', open(file_path, 'rb'), 1024, uploadTracker.handle)

    window.hide_window()

    ftp.quit()
    os.remove(file_path)

    print("File received")

def start_watching(directory_to_watch):
    event_handler = FileCreatedHandler(file_added_callback)
    observer = Observer()
    observer.schedule(event_handler, directory_to_watch, recursive=False)
    observer.start()

def background_task3():
    mock_server.main()

def checkConfigFile():
    if not os.path.exists("config.toml"):
        config = """[printer]
ip = "127.0.0.1"
auto_start = false
password = "0"
token = ""

[ftp_server]
enable = false
create_shortcut_on_start = true
network_location_name = "halot mage s"

[watchdog]
enable = true

[mock_server]
enable = true
"""
        with open("config.toml", "w") as f:
            f.write(config)

def main():

    checkConfigFile()

    global config
    config = toml.load("config.toml")
    
    """
    global token
    token = ""

    if(config['printer']['token'] == ""):
        token = get_token.get_token()
        config['printer']['token'] = token
        with open("config.toml", "w") as f:
            toml.dump(config, f)
    """
    #check every time
    global token
    token = ""

    token = get_token.get_token(config['printer']['password'])
    config['printer']['token'] = token
    with open("config.toml", "w") as f:
        toml.dump(config, f)

    global printer_ip
    printer_ip = config['printer']['ip']

    #check to see if FTP share has been created
    if not os.path.exists('./ftp'):
        os.makedirs('./ftp')

    if config['watchdog']['enable'] == True:
        directory_to_watch = './ftp' # Replace with the directory you want to watch
        start_watching(directory_to_watch)
    elif config['ftp_server']['enable'] == False:
        sys.exit(0)
    
    if config['ftp_server']['enable'] == True:
        background_thread = threading.Thread(target=background_task, daemon=True)
        background_thread.start()

    if config['mock_server']['enable'] == True:
        background_thread3 = threading.Thread(target=background_task3, daemon=True)
        background_thread3.start()

    background_thread2 = threading.Thread(target=background_task2, daemon=True)
    background_thread2.start()

    app = QApplication(sys.argv)
    global window
    window = MainWindow()
    window.resize(0, 0)
    window.hide()
    sys.exit(app.exec_())
    

if __name__ == "__main__":
    main()