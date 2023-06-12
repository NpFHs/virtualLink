# Virtual Link
Remote Control Server  
  
### Description
This project is a remote control server written in Python. It allows you to control a remote computer using a graphical user interface (GUI). You can perform various operations on the remote computer such as executing commands, browsing files, transferring files, and managing power options.  
  
The server uses the Tkinter library for the GUI, the socket library for network communication, and the RSA encryption algorithm for secure communication between the client and the server.  
## host

### Features
* Execute commands on the remote computer  
* Browse and transfer files between the local and remote computer  
* View and control the remote desktop  
* Manage power options (shutdown, restart, log out) on the remote computer  

### Installation  
Clone the repository:  
```git clone https://github.com/example/remote-control-server.git```

Change to the project directory:  
```cd remote-control-server```

Install the required dependencies:  
```pip install -r requirements.txt```

### Usage  
* Start the server by running the host.py script:  
```python3 host.py```

The server will display its IP address and port number.  
  
Run the client application on the remote computer and enter the server's IP address and port number to connect to the server.  
  
The client will display a graphical user interface (GUI) with different tabs for remote desktop, file transfer, command prompt, and power management.  
  
Use the GUI to perform the desired operations on the remote computer.  
  
### Configuration  
The IP address and port number used by the server can be configured in the host.py file by modifying the IP and PORT variables.  

## Client 
### Prerequisites

* Python 3.x

* rsa library (can be installed via pip install rsa)

* pyscreenshot library (can be installed via * pip install pyscreenshot)

### Getting Started
1. Clone the VirtualLink repository to your local machine.

2. Navigate to the client directory in the cloned repository:

```cd virtualLink/client```

3. Install the required dependencies:
```pip install -r requirements.txt```
### Usage

To use the VirtualLink client, follow these steps:

1. Start the VirtualLink server on the host machine by following the instructions provided in the server documentation.

2. Run the VirtualLink client script:

```python3 client.py```

3. When prompted, enter the IP address and port of the VirtualLink server. Press Enter to use the default values (127.0.0.1 for the IP address and 8091 for the port).

4. The client will establish a connection with the server and perform an initial handshake to exchange system information and public keys.

### Customization

You can customize the behavior of the VirtualLink client by modifying the variables and code in the client.py file. Some possible customizations include:

* Changing the default values for IP address and port.

* Modifying the power commands to suit your operating system.

* Adjusting the buffer size and screenshot parameters for performance optimization.

Make sure to test and validate any modifications to ensure proper functionality.

### Troubleshooting

If you encounter any issues or errors while using the VirtualLink client, consider the following troubleshooting steps:

* Verify that the VirtualLink server is running and accessible from the client machine.

* Check the network connectivity between the client and server machines.

* Ensure that the required dependencies (rsa and pyscreenshot) are installed correctly.

* Review the error messages and logs for any clues on the cause of the issue.

If the problem persists, feel free to seek help by opening an issue in the VirtualLink repository.
