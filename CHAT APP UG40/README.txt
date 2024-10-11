**************GROUP 40 CHAT APP*****************
		Team Members:

Nathan Dang (a1794954@adelaide.edu.au)
Haydn Gaetdke (a1860571@adelaide.edu.au)
Quoc Khanh Duong (a1872857@adelaide.edu.au)
Dang Hoan Nguyen (a1830595@adelaide.edu.au)

------------------------------------------------
PLEASE CONTACT ANY OF US VIA EMAIL IMMEDIATELY IN CASE YOU NEED ASSISTANCE. WE WILL TRY OUR BEST TO HELP

I. Dependencies
The required dependencies are listed in the requirements.txt file.

II. How to Run the Chat App
1. Install Dependencies
Run the following command to install the required libraries: pip install -r requirements.txt

2. Run the Server
- Open a PowerShell terminal and navigate to the server folder: cd server
- Run createFiles.py to create the necessary files: python createFiles.py
- Start the server by running: python server.py
- If the public-private key pair is not created automatically, run the following script to generate it: python rsaKeyGenerator.py

3. Run the Client
- Open another PowerShell terminal and navigate to the client folder: cd client
- Start the client by running: python chatApp.py
- This should generate the public-private key pair along with client_state.json and server_info.json. By default, server_info.json is configured to connect to localhost:8080.

III. How to Use the Chat App
1. Public Chat
- Select "Public Chat" from the left side menu.
- Enter your message in the text field at the bottom and press the Send button.
- The message will appear on everyone's screen with the public chat tag.
2. Private Chat
- Select a user from the left side menu (the names are randomly generated for each user).
- Enter your message in the text field at the bottom and press Send.
- The message will appear on your screen and the selected user's screen.
3. Group Chat
- Click "New Group Chat" on the top-left corner of the interface.
- Select the users you want to create a group with, then click Create.
- The group will appear in the left-hand menu.
- Select the group to start chatting.
- Enter your message and press Send. The message will be sent to all group members.

IV. How to Test Inter-Server Chat
- Modify the state["neighbours"] according to state.example.json.
- Modify the server_info.json if needed to connect to the correct server.
- Run two servers on two different computers.
- After connecting the servers, open the chat app on each client (ensure server_info.json is correctly configured).
- Follow the instructions above to send messages across servers.

V.How to Upload and Download Files
1. Upload a File
- Click the Upload File button at the bottom-right corner of the screen.
- Browse and select a file to upload. A "File uploaded successfully" message will appear if the upload was successful. If the upload fails, you'll see an error message: "Failed to upload file: [filename]".
2. Download a File
- Click the Download File button at the bottom-right corner of the screen. Choose from the list of URLs that of the file you wish to download, then click Download.
- A success message will appear: "Downloaded successfully. The file is at download/filename".

!!! Note: Only the person who uploaded the file will have the download URL. If someone else wants to download the file, they must get the URL from the uploader and manually enter it.

VI. Troubleshooting
- If the client isn't working, delete private_key.pem, public_key.pem, and client_state.json. Then, re-run chatApp.py.
- To connect to another server, update the server information according to the state.example.json file.
