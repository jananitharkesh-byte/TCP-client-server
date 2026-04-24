Secure File Transfer Protocol (RFMP) – TCP Client-Server System with RSA Key Exchange

Overview:
This project implements a TCP-based Remote File Management Protocol (RFMP) that allows a client to communicate with a server and perform file operations such as reading, writing, and directory management. The system was implemented using Python socket programming with multithreading on the server to support multiple client connections simultaneously.

The protocol also supports optional encrypted communication, where the client and server perform a setup phase to establish a secure session using RSA key exchange and encrypted file data transfer.

The project demonstrates key networking and cybersecurity concepts such as client-server architecture, protocol design, secure session setup, and encrypted communication.

Key Features

• Custom application-layer protocol (RFMP) for structured communication
• TCP client-server architecture
• Multithreaded server handling multiple connections
• Secure session negotiation using RSA
• Optional encrypted file transfer using AES or Caesar cipher
• Remote file operations such as reading, writing, and directory management
• Error handling with structured error codes

Protocol Design

The RFMP protocol follows a three-phase communication model:

1. Setup Phase

The client initiates communication by sending a start packet indicating the protocol version and whether encryption should be enabled.

Example packet:

(SS, RFMP, v1.0, 1)

If encryption is enabled, the server returns its RSA public key to allow the client to securely transmit a session key.

The session key is encrypted using RSA before being sent to the server.

2. Operation Phase

Once the setup phase completes, the client can issue commands to the server.

Supported operations include:

• Directory creation
• Directory navigation
• Listing files
• File deletion and renaming
• Reading files from the server
• Writing data to files on the server

Commands are transmitted using structured packets such as:

(CM, openRead, filename.txt)

File data is transferred using data packets.

3. Closing Phase

The client terminates the connection by sending a closing packet.

(End)

The server then closes the connection gracefully.

Encryption Modes

The protocol supports two optional encryption modes:

AES Encryption

File data can be encrypted using AES via the Fernet cryptographic library. The session key is exchanged securely using RSA encryption during the setup phase.

Caesar Cipher

A simple Caesar cipher option was implemented for demonstration of symmetric encryption logic.

Technologies Used

Python
Socket Programming
Multithreading
RSA Encryption (PyCryptodome)
Fernet AES Encryption (cryptography library)

Server Implementation

The server listens for incoming connections and creates a separate thread for each client to allow concurrent communication.

The server also:

• generates RSA keys for secure sessions
• decrypts the encrypted session key sent by the client
• processes file system commands
• encrypts or decrypts file data when required

Client Implementation

The client connects to the RFMP server and allows the user to choose between encrypted or plaintext communication modes.

The client handles:

• protocol setup and negotiation
• encryption algorithm selection
• sending commands to the server
• encrypting file data before transmission

C Client (Additional Implementation)

An additional client implementation was written in C using the Windows Winsock API to demonstrate interoperability with the RFMP server.

This client connects to the server, sends protocol packets, and retrieves file content from the remote server.

Example Workflow
Client connects to server
Client sends protocol start packet
Server responds with connection confirmation
Client optionally establishes encrypted session
Client sends commands for file operations
Server processes requests and returns responses
Skills Demonstrated

Network Programming
Custom Protocol Design
Socket Programming
Secure Session Establishment
Encryption Concepts
Multithreaded Server Architecture

Possible Improvements

• Implement TLS for stronger secure communication
• Add user authentication before file operations
• Implement access control for file permissions
• Add logging for security auditing
• Implement packet integrity verification

Learning Outcomes

This project helped develop practical understanding of:

• how network protocols operate
• how secure session establishment works
• how encryption is integrated into network communication
• how servers handle concurrent clients
