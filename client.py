import socket
import os
import platform
import time
import rsa
import pyscreenshot as ImageGrab
from threading import *
from PIL import Image

BUFFER_SIZE = 4096
SYSTEM_TYPE = platform.system()
SYSTEM_NAME = os.popen("whoami").read().strip("\n")
public_key, private_key = rsa.newkeys(2048)
host_public_key = None
COMPRESSED_SCREENSHOT_WIDTH = 750
is_alive = True

if SYSTEM_TYPE == "Windows":
    screenshot_path = r"C:\images\screen.png"
    compressed_screenshot_path = r"C:\images\screen.png"
else:
    screenshot_path = "/home/noam/PycharmProjects/virtualLink/images/screen.jpg"
    compressed_screenshot_path = "/home/noam/PycharmProjects/virtualLink/images/screen.jpg"
    # screenshot_path = "images/screen.png"

try:
    PORT = int(input("Please enter the host PORT (8091): "))
except ValueError:
    PORT = 8091

IP = input("Please enter the host IP (127.0.0.1): ")

if IP == "" or len(IP.split(".")) != 4:
    IP = "127.0.0.1"

BREAK1 = "<BREAK1>"  # use to split between LEVEL1 data
BREAK2 = "<BREAK2>"  # use to split between LEVEL2 data

power_commands = {"shutdown": {"Windows": "shutdown /s /t 000",
                               "Linux": "shutdown now"},
                  "restart": {"Windows": "shutdown /r",
                              "Linux": "reboot"},
                  "log_out": {"Windows": "shutdown /l",
                              "Linux": "gnome-session-quit --no-prompt"}}


def encrypt(msg):
    enc_msg = rsa.encrypt(msg.encode(), host_public_key)
    return enc_msg


def decrypt(msg):
    # add except for case of failure in decryption.
    try:
        origin_msg = rsa.decrypt(msg, private_key)
    except rsa.pkcs1.DecryptionError:
        print("DecryptionError")
        origin_msg = b"Error"
    return origin_msg


def compress_img(image_name, new_size_ratio=0.9, quality=90, width=None, height=None, to_jpg=True):
    # load the image to memory
    img = Image.open(image_name)
    # get the original image size in bytes
    image_size = os.path.getsize(image_name)
    if new_size_ratio < 1.0:
        # if resizing ratio is below 1.0, then multiply width & height with this ratio to reduce image size
        img = img.resize((int(img.size[0] * new_size_ratio), int(img.size[1] * new_size_ratio)), Image.ANTIALIAS)
    elif width and height:
        # if width and height are set, resize with them instead
        img = img.resize((width, height), Image.ANTIALIAS)
    # split the filename and extension
    filename, ext = os.path.splitext(image_name)
    # make new filename appending _compressed to the original file name
    if to_jpg:
        # change the extension to JPEG
        new_filename = f"{filename}.jpg"
    else:
        # retain the same extension of the original image
        new_filename = f"{filename}{ext}"
    try:
        # save the image with the corresponding quality and optimize set to True
        img.save(new_filename, quality=quality, optimize=True)
    except OSError:
        # convert the image to RGB mode first
        img = img.convert("RGB")
        # save the image with the corresponding quality and optimize set to True
        img.save(new_filename, quality=quality, optimize=True)
    # get the new image size in bytes
    new_image_size = os.path.getsize(new_filename)
    # calculate the saving bytes
    saving_diff = new_image_size - image_size
    print(f"[+] Image size change: {saving_diff / image_size * 100:.2f}% of the original image size.")
    return new_filename


def send_response(client_socket, msg_type, msg):
    # TODO: split long commands to many packets
    path = os.getcwd()

    if msg_type == "filepart" or msg_type == "screenshot_part":
        response = msg
        resp_len = str(len(response)).zfill(8).encode()
        resp = resp_len + response
        client_socket.send(resp)

    else:
        if msg_type == "sys_info":
            response = f"{msg_type} {msg}".encode()
        elif msg_type == "file":
            response = f"{msg_type} {msg}".encode()
        elif msg_type == "files_list":
            response = f"{msg_type} {msg}".encode()
        elif msg_type == "screenshot":
            response = f"{msg_type} {msg}".encode()
        elif msg_type == "public_key":
            response = msg_type.encode() + b" " + msg
        else:
            response = f"{msg_type} {path} {msg}".encode()
        resp_len = str(len(response)).zfill(8).encode()
        resp = resp_len + response
        client_socket.send(resp)


def convert_file_size(size):
    unit = "bytes"
    if size // 1000 == 0:
        return f"{size} {unit}"
    elif size // 1000000 == 0:
        unit = "kB"
        converted_size = round(size / 1000, 2)
        return f"{converted_size} {unit}"
    elif size // 1000000000 == 0:
        unit = "MB"
        converted_size = round(size / 1000000, 2)
        return f"{converted_size} {unit}"
    elif size // 1000000000000 == 0:
        unit = "GB"
        converted_size = round(size / 1000000000, 2)
        return f"{converted_size} {unit}"
    else:
        print(f"size: {size}")
        print(size // 1000000000000)
        unit = "TB"
        converted_size = round(size / 1000000000000, 2)
        return f"{converted_size} {unit}"


def take_screenshot(path):
    """
    take a screenshot and save it to given path.
    """
    img = ImageGrab.grab()
    img.save(path)


def send_screenshot(live_screen_socket, path):
    with open(path, "rb") as img:
        while True:
            print("waiting to send next screenshot part")
            status_code = live_screen_socket.recv(1024).decode()
            print("next screenshot part sent ;)")

            if status_code == "1":
                data = img.read(BUFFER_SIZE)
                if len(data) == 0:
                    print("screenshot sent!")
                    # send the "screenshot done" msg.
                    send_response(live_screen_socket, "screenshot", "done")

                    break
                send_response(live_screen_socket, "screenshot_part", data)
            else:
                print(status_code + ", Error")
                break


def handle_screenshot(live_screen_socket):
    take_screenshot(screenshot_path)
    compress_img(screenshot_path, quality=50, width=COMPRESSED_SCREENSHOT_WIDTH, new_size_ratio=0.3)
    send_screenshot(live_screen_socket, compressed_screenshot_path)
    return "screenshot", "done"


def handle_server_response(command, client_socket, live_screen_socket):
    cmd_type = command.split()[0]
    cmd = " ".join(command.split()[1:])

    if cmd_type == "power":
        try:
            print(f"cmd: {cmd}, system_type: {SYSTEM_TYPE}")
            power_command = power_commands[cmd][SYSTEM_TYPE]
            os.system(power_command)
        except KeyError:
            return "power", "KeyError"
        return "power", "done"

    elif cmd_type == "execute":
        if cmd.split()[0] == "cd":
            try:
                os.chdir(cmd.split()[1])
                output = os.getcwd()
            except FileNotFoundError:
                output = "No such file or directory!"
            except IndexError:
                os.chdir(os.path.expanduser("~"))
                output = os.getcwd()
        else:
            try:
                output = os.popen(cmd).read()
            except UnicodeDecodeError:
                output = "Unreadable response!"
        return "execute", output

    elif cmd_type == "file":
        file_name = cmd
        try:
            file_size = os.path.getsize(file_name)
            send_response(client_socket, "file", f"{file_name}{BREAK1}{file_size}")

            with open(file_name, "rb") as file:
                while True:
                    bytes_read = file.read(BUFFER_SIZE)
                    if len(bytes_read) == 0:
                        break
                    send_response(client_socket, "filepart", bytes_read)
            print("done")
            return "file", "done"
        except FileNotFoundError:
            print("file not found")
            return "file", "FileNotFound"
        except IsADirectoryError:
            print("is a directory!")
            return "file", "IsADirectory"
        except PermissionError:  # program stop receiving when get permission error
            print("PermissionError")
            return "file", "PermissionError"

    elif cmd_type == "files_list":
        if cmd == "CURRENT":
            if SYSTEM_TYPE == "Linux":
                files_location = os.getcwd() + "/"
            else:
                files_location = os.getcwd() + "\\"
        else:
            files_location = cmd
        try:
            files_list = os.listdir(files_location)
            counter = 0
            for file in files_list:
                file_path = f"{files_location}{file}"
                if os.path.isdir(file_path):
                    files_list[counter] = f"DIR{BREAK2}{files_list[counter]}"
                    try:
                        sum_files = len(os.listdir(file_path))  # count the number of the files in the directory
                        files_list[counter] = files_list[counter] + BREAK2 + str(sum_files) + " Items"
                    except PermissionError:
                        print("can't view this file")
                        files_list[counter] = files_list[counter] + BREAK2 + "---"

                else:
                    # add size parameter to the file to be shown in the browser
                    file_size = os.path.getsize(f"{files_location}{file}")
                    files_list[counter] = f"FILE{BREAK2}{files_list[counter]}{BREAK2}{convert_file_size(file_size)}"

                counter += 1

            files = BREAK1.join(files_list)
            return "files_list", files
        except FileNotFoundError:
            print("FileNotFoundError")
        except PermissionError:
            return "files_list", "PermissionError"

    elif cmd_type == "screenshot":
        return handle_screenshot(live_screen_socket)

    return "exit", 0


def send_basic_info(client_socket):
    send_response(client_socket, "sys_info", f"os {SYSTEM_TYPE}")
    send_response(client_socket, "sys_info", f"name {SYSTEM_NAME}")


def send_public_key(client_socket):
    print(public_key.save_pkcs1(format="DER"))
    send_response(client_socket, "public_key", public_key.save_pkcs1(format="DER"))


def keep_sending_screenshots(live_screen_socket):
    while is_alive:
        # wait until the host get the screenshot
        msg_type, msg = handle_screenshot(live_screen_socket)
        # # send the "screenshot done" msg.
        # send_response(live_screen_socket, msg_type, msg)


def main():
    global is_alive

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((IP, PORT))
    print("Client connected")

    live_screen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    live_screen_socket.connect((IP, PORT))
    print("Live screen connected")

    live_screen = Thread(target=lambda: keep_sending_screenshots(live_screen_socket))
    live_screen.start()

    send_public_key(client_socket)
    send_basic_info(client_socket)

    os.chdir("/")
    command = ""
    while command != "exit 0":
        command = decrypt(client_socket.recv(1024)).decode()
        print(f"command: {command}")
        if len(command.split()) >= 2:
            cmd_type, cmd = handle_server_response(command, client_socket, live_screen_socket)
        else:
            cmd_type = "Error"
            cmd = "Wrong format"
        send_response(client_socket, cmd_type, cmd)

    is_alive = False
    client_socket.close()


if __name__ == "__main__":
    main()
