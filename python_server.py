import socket, threading
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import base64
import os
from cryptography.fernet import Fernet

HOST = "0.0.0.0"
PORT = 9000

# ====== ERROR CODES ======
ERROR_CODES = {
    "EE01": "Invalid Packet",       # Covers invalid start packets, unknown packets
    "EE02": "Invalid Security",     # Covers wrong security flags
    "EE03": "Command/File Error",   # Covers unsupported commands, file errors, mkdir/cd/ls/del failures
    "EE04": "No Open File"          # Specific for trying to write without an open file
}

def send_error(conn, code):
    """Send formatted error message using ERROR_CODES"""
    msg = ERROR_CODES.get(code, "Unknown Error")
    conn.send(f"({code}, {msg})".encode())

# ======== REPEATING-KEY FUNCTION ========
def make_fernet_key_from_session(session_key: str):
    if len(session_key) == 0:
        session_key = "a"  

    # Repeat until 32 bytes
    repeated = (session_key * (32 // len(session_key) + 1))[:32]

    # Base64-URL encode manually using python's base64
    return base64.urlsafe_b64encode(repeated.encode())


# ======== RSA KEY GENERATION ========
def rsa_keys():
    key = RSA.generate(2048)
    return key, key.publickey()

def decrypt_session_key(encrypted_key_b64, private_key):
    encrypted_key = base64.b64decode(encrypted_key_b64)
    cipher_rsa = PKCS1_OAEP.new(private_key)
    session_key = cipher_rsa.decrypt(encrypted_key)
    return session_key.decode()


# ======== CAESAR CIPHER ========
def caesar_encrypt(text, shift):
    shift = shift % 26
    out = ""
    for ch in text:
        if "a" <= ch <= "z":
            out += chr((ord(ch) - 97 + shift) % 26 + 97)
        elif "A" <= ch <= "Z":
            out += chr((ord(ch) - 65 + shift) % 26 + 65)
        else:
            out += ch
    return out

def caesar_decrypt(text, shift):
    return caesar_encrypt(text, -shift)


# ======== HANDLE CLIENT ========
def handle_client(conn, addr):
    print(f"Connected by {addr}")

    try:
        # ========== STARTUP PHASE  ==========
        start_packet = conn.recv(4096).decode().strip()
        print(f"Received: {start_packet}")

        parts = start_packet.strip("()").split(", ")
        if len(parts) != 4 or parts[0] != "SS":
            send_error(conn, "EE01")
            return

        protocol_name = parts[1]
        version = parts[2]
        security_flag = parts[3]

        print(f"Protocol={protocol_name}, Version={version}, Security={security_flag}")

        if security_flag == "1":
            print(f"[{addr}] Secured connection established ✅")
        else:
            print(f"[{addr}] Unsecured connection ⚠️")


        if security_flag == "0":
            conn.send(b"(CC)")
            algorithm = None
            session_key = None

        elif security_flag == "1":
            server_private, server_public = rsa_keys()
            public_pem = server_public.export_key().decode()
            conn.send(f"(CC, {public_pem})".encode())

            ec_packet = conn.recv(8192).decode().strip()
            print("Received EC:", ec_packet)

            ec_fields = ec_packet.strip("()").split(", ", 3)
            algorithm = ec_fields[1]
            encrypted_session_key_b64 = ec_fields[2]

            session_key = decrypt_session_key(encrypted_session_key_b64, server_private)
            print("Session Key decrypted:", session_key)

            conn.send(b"(SC, Setup Complete)")

        else:
            send_error(conn, "EE02")
            return

        print("Setup phase done.")

        # ========== OPERATION PHASE ==========
        fernet = None
        caesar_shift = None

        # AES setup
        if security_flag == "1" and algorithm.upper() == "AES":
            fernet_key = make_fernet_key_from_session(session_key)
            fernet = Fernet(fernet_key)

        # Caesar setup
        if security_flag == "1" and algorithm.lower() == "caesar":
            try:
                caesar_shift = int(session_key)
            except:
                caesar_shift = 3 

        open_file = None

        while True:

            packet = conn.recv(4096)
            if not packet:
                break

            packet = packet.decode().strip()
            print("Received:", packet)

            # ====== CLOSE PHASE ======
            if packet == "(End)":
                conn.send(b"(SC, Connection Closed)")
                break

            # ====== PROMPT COMMANDS (plaintext) ======
            if packet.startswith("(CM, prompt,"):
                cmd = packet.strip("()").split(", ", 2)[2]

                try:
                    if cmd.startswith("mkdir"):
                        os.mkdir(cmd.split(" ", 1)[1])
                        resp = "(SC, Folder Created)"

                    elif cmd.startswith("cd"):
                        os.chdir(cmd.split(" ", 1)[1])
                        resp = f"(SC, Path Changed: {os.getcwd()})"

                    elif cmd.startswith("ls"):
                        resp = f"(SC, {', '.join(os.listdir())})"

                    elif cmd.startswith("rmdir") or cmd.startswith("rd"):
                        os.rmdir(cmd.split(" ", 1)[1])
                        resp = "(SC, Folder Removed)"

                    elif cmd.startswith("del"):
                        os.remove(cmd.split(" ", 1)[1])
                        resp = "(SC, File Deleted)"

                    elif cmd.startswith("ren"):
                        old, new = cmd.split(" ")[1:]
                        os.rename(old, new)
                        resp = "(SC, Renamed Successfully)"

                    else:
                        resp = f"(EE, {ERROR_CODES['EE03']})"

                except Exception as e:
                    resp = f"(EE, {ERROR_CODES['EE03']}: {str(e)})"

                conn.send(resp.encode())
                continue

            # ====== OPEN FILE FOR WRITING ======1
            
            if packet.startswith("(CM, openWrite,"):
                try:
                    # Extract filename cleanly
                    filename = packet.strip("()").split(", ", 2)[2]

                    open_file = open(filename, "w")
                    resp = "(SC, File Opened for Writing)"
                except Exception as e:
                    resp = f"(EE, {ERROR_CODES['EE03']}: {str(e)})"

                conn.send(resp.encode())
                continue


            # ====== OPEN FILE FOR READING ======
            if packet.startswith("(CM, openRead,"):
                filename = packet.strip("()").split(", ")[2]
                try:
                    with open(filename, "r") as f:
                        content = f.read()

                    # encrypt only file content
                    if security_flag == "1" and algorithm.upper() == "AES":
                        content = fernet.encrypt(content.encode()).decode()
                    elif security_flag == "1" and algorithm.lower() == "caesar":
                        content = caesar_encrypt(content, caesar_shift)

                    resp = f"(SC, {content})"

                except Exception as e:
                    resp = f"(EE, {ERROR_CODES['EE03']}: {str(e)})"

                conn.send(resp.encode())
                continue

            # ====== WRITE DATA PACKET (DP) ======
            if packet.startswith("(DP,"):
                if open_file is None:
                    send_error(conn, "EE04")
                    continue

                _, data = packet.strip("()").split(", ", 1)

                # decrypt data ONLY if file content
                if security_flag == "1" and algorithm.upper() == "AES":
                    data = fernet.decrypt(data.encode()).decode()
                elif security_flag == "1" and algorithm.lower() == "caesar":
                    data = caesar_decrypt(data, caesar_shift)

                open_file.write(data + "\n")
                open_file.flush()

                conn.send(b"(SC, Data Written)")
                continue

            # UNKNOWN PACKET
            send_error(conn, "EE01")

        if open_file:
            open_file.close()

        conn.close()

    except Exception as e:
        print("Error:", e)
        conn.close()


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"RFMP Server listening on {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()

if __name__ == "__main__":
    start_server()