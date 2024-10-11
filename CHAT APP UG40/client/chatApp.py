# Code by Group UG40:
# Nathan Dang (a1794954@adelaide.edu.au)
# Haydn Gaetdke (a1860571@adelaide.edu.au)
# Quoc Khanh Duong (a1872857@adelaide.edu.au)
# Dang Hoan Nguyen (a1830595@adelaide.edu.au)


from parseMessage import ParseOutMessage
from parseMessage import ParseInMessage
from rsaKeyGenerator import generate_key_pair
import os
import asyncio
import websockets
import requests
import json
import sys
import hashlib
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QLabel, QPushButton, QListWidget, QDialog, QFileDialog, QMessageBox
from PyQt5 import QtCore
from PyQt5.QtGui import QFont
import logging

# logging.basicConfig(level=logging.DEBUG)
ONLINE_USERS = []

CURRENT_MODE = "public_chat"
PARTICIPANTS = []


class UploadDialog(QDialog):
    global SERVER_ADDRESS
    def __init__(self):
        super(UploadDialog, self).__init__()

        self.setWindowTitle('File Upload')
        self.setGeometry(150, 150, 400, 300)
        layout = QVBoxLayout()
        self.file_label = QLabel('Choose a file to upload first', self)
        self.status_label = QLabel('', self)
        self.upload_btn = QPushButton('Browser', self)
        self.upload_btn.clicked.connect(self.click_to_upload)
        layout.addWidget(self.file_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.upload_btn)

        self.setLayout(layout)
    def click_to_upload(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select a File", "", 
                                                   "All Files ();;Text Files (.txt);;Images (*.png *.jpg *.jpeg)", 
                                                   options=QFileDialog.Options())
        if file_path:
            self.file_label.setText(f'Selected File: {file_path}')
            self.upload_file(file_path)

    def upload_file(self, file_path):
        api_url = f"http://{SERVER_ADDRESS}/api/upload"      
        files = {'file': open(file_path, 'rb')}
        try:
            response = requests.post(api_url, files=files)
            if response.status_code == 200:
                response_json = json.loads(response.text)
                file_url = response_json['body']['file_url']
                with open("./client_state.json", "r") as fin:
                    client_state = json.load(fin)
                if file_url not in client_state['file_urls']:
                    client_state['file_urls'].append(file_url)
                with open("./client_state.json", "w") as fout:
                    json.dump(client_state, fout, indent=4)
                self.status_label.setText("File uploaded successfully!")
            else:
                self.status_label.setText(f"Failed to upload file: {response.status_code}")

        except Exception as e:
            self.status_label.setText(f"Error: {e}")

        finally:
            files['file'].close()


class DownloadDialog(QDialog):
    global SERVER_ADDRESS
    def __init__(self):
        super(DownloadDialog, self).__init__()

        self.setWindowTitle('File Donwload')
        self.setGeometry(150, 150, 550, 600)
        
        layout = QVBoxLayout(self)
        self.filelist = QListWidget(self)
        with open("./client_state.json", "r") as fin:
            files = (json.load(fin))['file_urls']
            
        for file in files:
            self.filelist.addItem(file)
        self.filelist.itemClicked.connect(self.choose_file)    
        
        self.stored_loc_label = QLabel('Click Download first.', self)
        
        self.download_button = QPushButton("Download", self)
        self.download_button.clicked.connect(self.download_file)
        
        layout.addWidget(self.filelist)
        layout.addWidget(self.stored_loc_label)
        layout.addWidget(self.download_button)
        layout.setStretch(0, 1)
        
        self.expectedfile = ""

    def choose_file(self, item):
        file_url = item.text()
        self.expectedfile = file_url
        print(file_url)
    
    def download_file(self):
        response = requests.get(self.expectedfile, stream=True)
        response.raise_for_status()
        filename = self.expectedfile.replace("/", "\\").split("\\")[-1]
        if response.status_code == 200:
            with open(f"./download/{filename}", 'wb') as fout:
                for chunk in response.iter_content(chunk_size=8192):
                    fout.write(chunk)
            self.stored_loc_label.setText(f"Downloaded successfully. The file is at ./download/{filename}")
        else:
            self.stored_loc_label.setText(f"Unsuccessful download.")


class PrivateChatDialog(QtWidgets.QDialog):
    def __init__(self, online_users, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Start Private Chat")
        self.setGeometry(300, 200, 400, 300)
        
        layout = QVBoxLayout(self)
        
        self.label = QLabel("Select users to chat with:", self)
        layout.addWidget(self.label)
        
        # List of online users with multi-selection mode
        self.user_list = QtWidgets.QListWidget(self)


        # Check if online_users is structured as expected
        with open('client_state.json', 'r') as file:
            chat_data = json.load(file)
            people = chat_data['NS']
            for person_id, person_data in people.items():
                if person_id != chat_data['fingerprint']:
                    self.user_list.addItem(person_data['name'])

        self.user_list.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)  # Allow multiple selections
        layout.addWidget(self.user_list)
        
        # Create button to start private chat
        self.create_button = QPushButton("Create", self)
        self.create_button.clicked.connect(self.create_chat)
        layout.addWidget(self.create_button)

    def create_chat(self):
        users = []
        selected_items = self.user_list.selectedItems()
        if selected_items:
            users = [item.text() for item in selected_items]  # Get a list of selected users
            # print(f"Creating private chat with: {', '.join(users)}")
            self.accept()  # Close the dialog
            self.result = users  # Return the list of selected users


class G40chatApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Group40chatApp")
        self.setGeometry(100, 100, 800, 600)
        
        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # Side menu (on the left)
        self.side_menu = QListWidget(self)
        self.side_menu.setSelectionMode(QListWidget.SingleSelection)
        
        self.side_menu_title = QLabel("Chats", self)
        self.side_menu_title.setStyleSheet("font-weight: bold; font-size: 16px;")
        
        # Add "Public Chat" at the start
        self.side_menu.addItem("Public Chat")
            
        self.side_menu.itemClicked.connect(self.change_chat)
        

        # Button to initiate new private chat
        self.private_chat_button = QPushButton("New Private Chat", self)
        self.private_chat_button.clicked.connect(self.open_private_chat_dialog)
        
        self.upload_button = QPushButton("Upload File", self)
        self.upload_button.clicked.connect(self.upload_modal_open)
        
        self.download_button = QPushButton("Download File", self)
        self.download_button.clicked.connect(self.download_modal_open)
        # self.upload_button.setFont(font)

        # Chat display (in the center)
        self.chat_display = QTextEdit(self)
        font_display_chat = QFont()
        font_display_chat.setPointSize(16)
        self.chat_display.setFont(font_display_chat)
        self.chat_display.setReadOnly(True)
        
        self.chat_display_title = QLabel("Public Chat", self)
        self.chat_display_title.setStyleSheet("font-weight: bold; font-size: 16px;")

        # Message input (bottom)
        self.message_input = QLineEdit(self)
        self.message_input.setFixedHeight(60)
        font_input = QFont()
        font_input.setPointSize(14)
        self.message_input.setFont(font_input)
        self.message_input.returnPressed.connect(self.send_message)
        
        self.send_button = QPushButton("Send", self)
        self.send_button.setFixedHeight(60)
        self.send_button.setFont(font_input)
        self.send_button.clicked.connect(self.send_message)

        # Side layout
        side_layout = QVBoxLayout()
        side_layout.addWidget(self.side_menu_title)
        side_layout.addWidget(self.private_chat_button)
        side_layout.addWidget(self.side_menu)
        side_layout.addWidget(self.upload_button)
        side_layout.addWidget(self.download_button)
        side_layout.setStretch(4, 1)
        main_layout.addLayout(side_layout)

        # Chat layout
        chat_layout = QVBoxLayout()
        chat_layout.addWidget(self.chat_display_title)
        chat_layout.addWidget(self.chat_display)
        
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)

        chat_layout.addLayout(input_layout)
        main_layout.addLayout(chat_layout)

        main_layout.setStretch(0, 1)
        main_layout.setStretch(1, 4)

        self.current_chat = "public_chat"
        self.current_mode = "public_chat"

        self.websocket_thread = WebsocketConnection(self)
        self.websocket_thread.start()

    def send_message(self):
        message = self.message_input.text()
        if message:
            self.websocket_thread.send_message(message)
            self.message_input.clear()

    def display_message(self, message):
        self.chat_display.append(message)
        
    def populate_client_list(self, client_list):
        online = []
        assert client_list['type'] == "client_list"
        assert len(client_list['servers']) > 0
        for server in client_list['servers']:
            for client in server['clients']:
                online.append(client)
                
        with open("client_state.json","r") as client_state_json:
                client_state = json.load(client_state_json)
                for fp in client_state['NS']:
                    if client_state['NS'][fp]['public_key'] in online:
                        name = client_state['NS'][fp]['name']
                        self.side_menu.addItem(name)
        print("Client list populated:", client_list)
        
    def update_client_list(self, updated_client_list, curr_client_list):
        new_list = []
        curr_list = []
        assert updated_client_list['type'] == "client_list"
        assert curr_client_list['type'] == "client_list"
        assert len(updated_client_list['servers']) > 0
        assert len(curr_client_list['servers']) > 0
        for server in updated_client_list['servers']:
            for client in server['clients']:
                new_list.append(client)
        for server in curr_client_list['servers']:
            for client in server['clients']:
                curr_list.append(client)
                
        new_users = set(new_list) - set(curr_list)
        removed_users = set(curr_list) - set(new_list)
        print(removed_users)
        with open("client_state.json","r") as client_state_json:
                client_state = json.load(client_state_json)
                for fp in client_state['NS']:
                    if client_state['NS'][fp]['public_key'] in new_users:
                        name = client_state['NS'][fp]['name']
                        self.side_menu.addItem(name)

        # Remove users who left the chat
                    if client_state['NS'][fp]['public_key'] in removed_users:
                        name = client_state['NS'][fp]['name']
            # Find and remove the corresponding item
                        items = self.side_menu.findItems(name, QtCore.Qt.MatchExactly)
                        if items:
                            for item in items:
                                self.side_menu.takeItem(self.side_menu.row(item))

        # Update the current user list to reflect the latest state
        print("Client list updated:", updated_client_list)


    def open_private_chat_dialog(self):
        dialog = PrivateChatDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            selected_users = dialog.result
                
            selected_users.sort()
            
            
            existing_chats = [self.side_menu.item(i).text().strip() for i in range(self.side_menu.count())]
            if selected_users:
                # Add the private chat with multiple users to the side menu
                chat_name = f"{', '.join(selected_users)}"
                if chat_name.strip() not in existing_chats:
                    self.side_menu.addItem(chat_name)
                    self.show_alert("Chat creted successfully", f"Private chat initiated with: {chat_name}.", "Info")
                else:
                    self.show_alert("Creation error", f"Private chat with {chat_name} already exists.", "Error")

                    
    def show_alert(self, title, message, type):
        self.alert = QMessageBox()
        self.alert.setWindowTitle(title)
        self.alert.setText(message)
        self.alert.setStandardButtons(QMessageBox.Ok)
        
    
        if type == "Info":
            self.alert.setIcon(QMessageBox.Information)
        elif type == "Error":
            self.alert.setIcon(QMessageBox.Warning)
        
        else:
            return
        
        # Auto close
        QtCore.QTimer.singleShot(5000, self.alert.close)

        self.alert.exec_()


    def change_chat(self, item):
        global PARTICIPANTS, CURRENT_MODE
        selected_chat = item.text()
        self.chat_display_title.setText(selected_chat)
        
        # print(CURRENT_MODE)
        
        if selected_chat == "Public Chat":
            self.current_chat = "public_chat"
            self.current_mode = "public_chat"
        elif "," not in selected_chat:
            self.current_mode = "chat"
            self.current_chat = [selected_chat]
        elif "," in selected_chat:
            self.current_mode = "chat"
            chat_list = selected_chat.split(",")
            self.current_chat = []
            for i in range(len(chat_list)):
                self.current_chat.append(chat_list[i].strip())
                
        with open("./client_state.json", "r") as client_state:
            client_state_data = json.load(client_state)
            
        PARTICIPANTS = []
        for fp in client_state_data['NS']:
            if client_state_data['NS'][fp]['name'] in self.current_chat:
                PARTICIPANTS.append(fp)
        
        
        CURRENT_MODE = self.current_mode
        
        print(f"Switched to {selected_chat}")


    def upload_modal_open(self):
        dialog = UploadDialog()
        dialog.exec_() 
        
    def download_modal_open(self):
        dialog = DownloadDialog()
        dialog.exec_() 

        

# Thread for handling login behind
class WebsocketConnection(QtCore.QThread):
    global SERVER_ADDRESS
    message_received = QtCore.pyqtSignal(str)  
    populate_client_list = QtCore.pyqtSignal(dict)
    update_client_list = QtCore.pyqtSignal(dict, dict)
    

    def __init__(self, parent=None):
        super().__init__(parent)
        self.connected = False
        self.websocket = None
        self.loop = None

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.websocket_connect())


    async def websocket_connect(self):
        global ONLINE_USERS
        WS_SERVER = f"ws://{SERVER_ADDRESS}"
        try:
            async with websockets.connect(WS_SERVER) as websocket:                
                self.websocket = websocket
                self.connected = True
                print('-------------------')
                print('Connecting to')
                print(f"ws://{SERVER_ADDRESS}")
                print('-------------------')

                # Connection request to a server
                helloMessage = ParseOutMessage("", "signed_data", "hello", [], ONLINE_USERS)
                await self.websocket.send(helloMessage)
                response = await self.websocket.recv()

                # Request online clients in approachable servers
                requestClientList = ParseOutMessage("", "client_list_request", "", [], ONLINE_USERS)
                await self.websocket.send(requestClientList)
                response = await self.websocket.recv()
                parsed_response, response_type = ParseInMessage(response)
                if response_type == "client_list":
                    self.populate_client_list.emit(parsed_response)
                    ONLINE_USERS = parsed_response
                    print("Online Users:")
                    print(ONLINE_USERS)
                    print()
                
                
                # Continuously waiting for message from server
                while True:
                    try:
                        message = await websocket.recv()
                        msg, msg_type = ParseInMessage(message)
                        if msg_type == "client_list":
                            curr_client_list = ONLINE_USERS
                            self.update_client_list.emit(msg, curr_client_list)
                            
                            ONLINE_USERS = msg
                            print("Online Users:")
                            print(ONLINE_USERS)
                            print()
                            continue  
                        if (msg_type == "signed_data_chat" or \
                            msg_type == "signed_data_public_chat") \
                            and msg != False:
                            displye_msg = f"""
                            <div style='width:100%; margin: 5px;'>
                                <span style='font-size:14px;font-weight:bold;'>{msg['sender']}</span><br/>
                            
                                <span style='color:{msg['color']}; display: inline-block'>
                                    {msg['message']}
                                    
                                </span>
                            </div>
                            """
                            self.message_received.emit(displye_msg) 
                    except websockets.ConnectionClosedOK:
                        print('See you next time.')
                        break
                    except websockets.ConnectionClosedError as e:
                        print(f"Close Error: {e}")
                        break       
                    except Exception as e:
                        print(f"General Exception: {e}")  
        
        except Exception as e:
            print(f"WebSocket connection error: {e}")

    # A handler when the UI receive a send request
    # Assign the send functionality to another thread
    def send_message(self, message):
        global CURRENT_MODE, PARTICIPANTS
        parsedMessage = ParseOutMessage(message, "signed_data", CURRENT_MODE, PARTICIPANTS, ONLINE_USERS)
        asyncio.run_coroutine_threadsafe(self.websocket_send(parsedMessage), self.loop)
        
        attribution_text = ""
        
        with open ("./client_state.json", "r") as client_state:
                client_state_data = json.load(client_state)
        if CURRENT_MODE == "chat" and len(PARTICIPANTS) != 0:
            participant_names_list = []
            for fp in PARTICIPANTS[1:]:
                if fp in client_state_data['NS']:
                    participant_names_list.append(client_state_data['NS'][fp]['name'])
            participant_names_list = list(set(participant_names_list))
            if len(participant_names_list) == 0:
                participant_names_list = ['Yourself']
            attribution_text = "&gt;&gt; <span style='color:green'>[TO]</span> " + ", ".join(participant_names_list)
        elif CURRENT_MODE == "public_chat":
            attribution_text = "&gt;&gt; <span style='color:red'>[PUBLIC CHAT]</span> <span style='color:green'>[TO]</span> ALL"

        my_color = client_state_data['NS'][client_state_data['fingerprint']]['color']

        displye_msg = f"""
            <div style='width:100%; margin: 5px;'>
                <span style='font-size:14px;font-weight:bold;'>{attribution_text}</span><br/>
            
                <span style='color:{my_color}; display: inline-block'>
                    {message}
                    
                </span>
            </div>
            """
        if len(PARTICIPANTS) > 0:
            PARTICIPANTS.pop(0)
        self.message_received.emit(displye_msg) 
        

    async def websocket_send(self, message):
        if self.connected and self.websocket:
            await self.websocket.send(message) 

if (not(os.path.isfile("private_key.pem") and os.path.isfile("public_key.pem"))):
    generate_key_pair()

if (not(os.path.isfile("client_state.json"))):
    with open("client_state.example.json", "r") as file:
        client_state = json.load(file)
    with open("client_state.json", "w") as file:
        json.dump(client_state, file, indent=4)

with open("client_state.json", "r") as file:
    client_state = json.load(file)
    if (client_state['fingerprint'] == ""):
        with open("public_key.pem", "r") as pub_f:
            pub_k = pub_f.read()
            client_state['fingerprint'] = hashlib.sha256(pub_k.encode()).hexdigest()
with open("client_state.json", "w") as file:
    json.dump(client_state, file, indent=4)

if (not(os.path.isfile("server_info.json"))):
    with open("server_info.example.json", "r") as file:
        server_info = json.load(file)
        server_info["master_server_counter"] = 0
        server_info["master_server_port"] = 8080
        server_info["master_server_ip"] = "localhost"
    with open("server_info.json", "w") as file:
        json.dump(server_info, file, indent=4)
        
with open("./server_info.json", 'r') as server_info:
    data = json.load(server_info)
    ip = data['master_server_ip']
    port = data['master_server_port']

SERVER_ADDRESS = f'{ip}:{port}'

app = QtWidgets.QApplication(sys.argv)
window = G40chatApp()
window.show()

window.websocket_thread.message_received.connect(window.display_message)
window.websocket_thread.populate_client_list.connect(window.populate_client_list)
window.websocket_thread.update_client_list.connect(window.update_client_list)


sys.exit(app.exec_())
