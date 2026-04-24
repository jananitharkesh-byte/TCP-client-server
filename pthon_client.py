import socket
import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from cryptography.fernet import Fernet

# ======== REPEATING KEY FUNCTION ========
def make_fernet_key(session_key):
    """
    Repeat short session key until 32 bytes,
    then base64-url encode it for Fernet.
    """
    if len(session_key) == 0:
        session_key = "a"

    repeated = (session_key * (32 // len(session_key) + 1))[:32]
    return base64.urlsafe_b64encode(repeated.encode())


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


# ========== CLIENT STARTS HERE ==========
HOST = "127.0.0.1"
PORT = 9000

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

print("Setup Complete - Connection Established YAY!")


# ======== START PACKET ========
print("\nSecurity Mode:")
print("0 = No Encryption")
print("1 = Encryption (AES or Caesar)")

sec = input("Choose security (0/1): ").strip()

start_packet = f"(SS, RFMP, v1.0, {sec})"
client.send(start_packet.encode())

server_reply = client.recv(8192).decode()
print("Server:", server_reply)


# ======== IF ENCRYPTION ENABLED ========
algorithm = None
fernet = None
caesar_shift = None

if sec == "1":

    # --------- Receive CC packet ---------
    cc_packet = server_reply

    if not cc_packet.startswith("(CC"):
        print("Invalid CC packet.")
        exit()

    # Extract public key
    if "," in cc_packet:
        server_pub = cc_packet.split(", ", 1)[1].rstrip(")")
    else:
        print("Server returned plaintext CC. Exiting.")
        exit()

    server_public_key = RSA.import_key(server_pub)
    cipher_rsa = PKCS1_OAEP.new(server_public_key)

    # --------- Choose Algorithm ---------
    print("\nChoose Algorithm:")
    print("AES or Caesar")
    algorithm = input("Algorithm: ").strip()

    # Session key chosen BY YOU:
    session_key = input("Enter session key (any string): ")

    # Encrypt the session key with server RSA public key
    encrypted_session = cipher_rsa.encrypt(session_key.encode())
    encrypted_b64 = base64.b64encode(encrypted_session).decode()

    # Send EC packet
    ec_packet = f"(EC, {algorithm}, {encrypted_b64}, user:clientPublicKey)"
    client.send(ec_packet.encode())

    # Receive SC
    print("Server:", client.recv(4096).decode())

    # Prepare AES or Caesar for FILE CONTENT ONLY
    if algorithm.lower() == "aes":
        fkey = make_fernet_key(session_key)
        fernet = Fernet(fkey)

    elif algorithm.lower() == "caesar":
        try:
            caesar_shift = int(session_key)
        except:
            caesar_shift = 3


# ======== OPERATION LOOP ========
def send_plain(packet):
    client.send(packet.encode())

def send_data_packet(data):
    """Encrypt ONLY file content"""
    if sec == "1":
        if algorithm.lower() == "aes":
            data = fernet.encrypt(data.encode()).decode()

        elif algorithm.lower() == "caesar":
            data = caesar_encrypt(data, caesar_shift)

    client.send(f"(DP, {data})".encode())


while True:
    print("\nChoose operation:")
    print("1. Prompt Command (mkdir, cd, ls, ren...)")
    print("2. Open File for Write")
    print("3. Open File for Read")
    print("4. Send File Data (DP)")
    print("5. Give Dobby a Sock (End)")

    choice = input("Choice: ").strip()

    if choice == "1":
        cmd = input("cmd> ")
        packet = f"(CM, prompt, {cmd})"
        send_plain(packet)
        print("Server:", client.recv(8192).decode())

    elif choice == "2":
        name = input("Filename: ")
        packet = f"(CM, openWrite, {name})"
        send_plain(packet)
        print("Server:", client.recv(4096).decode())

    elif choice == "3":
        name = input("Filename: ")
        packet = f"(CM, openRead, {name})"
        send_plain(packet)
        reply = client.recv(10000).decode()

        # decrypt ONLY file content inside reply
        if sec == "1":
            try:
                inner = reply.strip("()")[4:].strip()
                if algorithm.lower() == "aes":
                    inner = fernet.decrypt(inner.encode()).decode()
                elif algorithm.lower() == "caesar":
                    inner = caesar_decrypt(inner, caesar_shift)
                reply = f"(SC, {inner})"
            except:
                pass

        print("Server:", reply)

    elif choice == "4":
        data = input("Write data: ")
        send_data_packet(data)
        print("Server:", client.recv(4096).decode())

    elif choice == "5":
        send_plain("(End)")
        print("Server:", client.recv(4096).decode())
        break

    else:
        print("Invalid choice.")

client.close()
print("You have given Dobby a sock? .. Dobby is Free :D")