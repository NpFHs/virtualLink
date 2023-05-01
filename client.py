import socket
import os
import platform
import pyscreenshot as ImageGrab

BUFFER_SIZE = 4096
SYSTEM_TYPE = platform.system()
SYSTEM_NAME = os.popen("whoami").read().strip("\n")

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


def send_response(client_socket, msg_type, msg):
    # TODO: split long commands to many packets
    path = os.getcwd()

    if msg_type == "filepart":
        response = msg
        resp_len = str(len(response)).zfill(8).encode()
        resp = resp_len + response
        client_socket.send(resp)

    else:
        if msg_type == "sys_info":
            response = f"{msg_type} {msg}"
        elif msg_type == "file":
            response = f"{msg_type} {msg}"
        elif msg_type == "files_list":
            response = f"{msg_type} {msg}"
        else:
            response = f"{msg_type} {path} {msg}"
        resp_len = str(len(response.encode())).zfill(8)
        resp = resp_len + response
        client_socket.send(resp.encode())


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


def handle_server_response(command, client_socket):
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
        img = ImageGrab.grab()
        img.save("/home/noam/PycharmProjects/virtualLink/images/screen.png")

        send_response(client_socket, "screenshot", img)

    return "exit", 0


def send_basic_info(client_socket):
    send_response(client_socket, "sys_info", f"os {SYSTEM_TYPE}")
    send_response(client_socket, "sys_info", f"name {SYSTEM_NAME}")


def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((IP, PORT))
    print("Client connected")

    send_basic_info(client_socket)
    os.chdir("/")
    command = ""
    while command != "exit 0":
        command = client_socket.recv(1024).decode()
        if len(command.split()) >= 2:
            cmd_type, cmd = handle_server_response(command, client_socket)
        else:
            cmd_type = "Error"
            cmd = "Wrong format"
        send_response(client_socket, cmd_type, cmd)

    client_socket.close()


if __name__ == "__main__":
    main()
