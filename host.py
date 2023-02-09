import os.path
import time
import tkinter as tk
from tkinter import ttk
import socket
from threading import *

IP: str = "0.0.0.0"
PORT: int = 8091
BREAK = "<BREAK>"

pre_commands = []  # Storing the last commands the user enter.
current_command = 0  # Use to save the command location when the user press Up button.
browser_current_directory = "/"

files_list = []


# client_dist = "Unknown"


# TODO: add multiple clients support.


def shutdown(client_socket):
    command = f"power shutdown"
    client_socket.send(command.encode())
    print(command)


def restart(client_socket):
    command = f"power restart"
    client_socket.send(command.encode())
    print(command)


def log_out(client_socket):
    command = f"power log_out"
    client_socket.send(command.encode())
    print(command)


def get_resp(client_socket):
    msg_len = client_socket.recv(8)
    if msg_len.isdigit():
        resp = client_socket.recv(int(msg_len)).decode()  # TODO: add more than 1024 bit support.
    else:
        print("No length info!")
        client_socket.recv(16777216)  # TODO: find better way to clean garbage? No. - DONE.
        resp = "Error"

    try:
        msg_type = resp.split()[0]
    except IndexError:
        msg_type = "Error"
    msg = " ".join(resp.split(" ")[1:])

    return msg_type, msg


def execute_command(client_socket, cmd, msg_list):
    if cmd == "clear":
        msg_list.delete(0, tk.END)
    else:
        command = f"execute {cmd}"
        client_socket.send(command.encode())


def request_file(file_location, client_socket):
    client_socket.send(f"file {file_location}".encode())


def request_files_in_location(location, client_socket):
    client_socket.send(f"files_list {location}".encode())


def open_folder(browser, client_socket, file_location):
    global browser_current_directory

    file_iid = browser.selection()[0]
    file_values = browser.item(file_iid)["values"]
    file_type = file_values[0]
    file_name = file_values[1]
    print(f"file_name: {file_name}, file_type: {file_type}")
    if file_type == "DIR":
        browser_current_directory = f"{browser_current_directory}{file_name}/"
        request_files_in_location(browser_current_directory, client_socket)
        time.sleep(0.5)  # wait until the files list update
        browser.delete(*browser.get_children())  # clear the browser
        for file in files_list:
            browser.insert("", tk.END, values=file)
    elif file_type == "FILE":
        file_location.set(browser_current_directory + file_name)
    else:
        print("This is not a directory!")


def browser_go_back(browser, client_socket):
    global browser_current_directory

    if browser_current_directory.count("/") > 1:
        browser_current_directory = "/".join(browser_current_directory.split("/")[:-2]) + "/"  # update cwd
        request_files_in_location(browser_current_directory, client_socket)
        time.sleep(0.5)  # wait until the files list update
        browser.delete(*browser.get_children())
        for file in files_list:
            browser.insert("", tk.END, values=file)


def browse_files(win, client_socket):
    file_location = tk.StringVar()
    top = tk.Toplevel(win)
    top.title("File browser")
    top.geometry("800x500")

    columns = ("type", "name", "size")
    file_browser = ttk.Treeview(top, columns=columns)  # create the files browser
    file_browser["show"] = "headings"  # to avoid empty column in the beginning
    file_browser.heading("type", text="type")
    file_browser.heading("name", text="name")
    file_browser.heading("size", text="size")
    file_browser.bind("<Double-Button-1>", lambda event: open_folder(file_browser, client_socket, file_location))
    file_browser.bind("<Return>", lambda event: open_folder(file_browser, client_socket, file_location))
    back_button = ttk.Button(top, text="Back", command=lambda: browser_go_back(file_browser, client_socket))
    back_button.pack(side="top", anchor="nw", padx=10, pady=(10, 0))
    file_browser.pack(side=tk.TOP, padx=10, pady=10)
    request_files_in_location(browser_current_directory, client_socket)
    time.sleep(0.5)  # wait until the files list update
    file_browser.delete(*file_browser.get_children())

    for file in files_list:
        # tuple_file = tuple(file.split())  # unnecessary?
        file_browser.insert("", tk.END, values=file)
    get_file = ttk.Button(top, text="Get file",
                          command=lambda: [request_file(file_location.get(), client_socket),
                                           location_entry.delete(0, tk.END)])
    get_file.pack(side="bottom", fill="x", padx=10, pady=10)

    location_entry = ttk.Entry(top, textvariable=file_location)
    location_entry.bind("<Return>", lambda event: [request_file(file_location.get(), client_socket),
                                                   location_entry.delete(0, tk.END)])
    location_entry.pack(side="bottom", fill="x", padx=10, pady=5)


def main():
    root = tk.Tk()
    root.tk.call("source", "azure.tcl")
    root.tk.call("set_theme", "dark")
    root.title("Remote Control")
    root.geometry("800x610")
    tab_frame = ttk.Notebook()
    tab_frame.pack(side="top", fill="both", expand=True, padx=5, pady=5)
    client_dist = tk.StringVar(value="Unknown")
    client_name = tk.StringVar(value="Unknown")
    command = tk.StringVar(value="Enter a command")
    files = tk.StringVar()

    is_alive = True

    def receive():
        print("Start receiving")
        while is_alive:
            try:
                msg_type, msg = get_resp(client_socket)

                if msg_type == "sys_info":
                    if msg.split()[0] == "os":
                        client_dist.set("OS: " + " ".join(msg.split(" ")[1:]))
                    elif msg.split()[0] == "name":
                        client_name.set("Name: " + " ".join(msg.split(" ")[1:]))

                elif msg_type == "execute":
                    path = msg.split()[0]
                    output = " ".join(msg.split(" ")[1:]).splitlines()
                    for line in output:
                        msg_list.insert(tk.END, line)
                    msg_list.insert(tk.END, "")
                    msg_list.insert(tk.END, f"({client_name.get()}):{path}$ ")  # TODO: fix the client name
                    msg_list.see(tk.END)

                elif msg_type == "file":
                    if msg.split()[0] == "FileNotFound":
                        print("file not found!")
                    else:
                        file_name, file_size = msg.split(BREAK)

                        file_name = os.path.basename(file_name)
                        # file_size = int(file_size)
                        with open(file_name, "wb") as file:
                            while True:
                                msg_len = client_socket.recv(8)
                                if msg_len.isdigit():
                                    bytes_file = client_socket.recv(int(msg_len))
                                else:
                                    print("No length info!")
                                    client_socket.recv(16777216)
                                    bytes_file = "Error".encode()

                                if bytes_file == "file done".encode():  # TODO: find better way to stop the loop
                                    break
                                file.write(bytes_file)
                            files.set(f"{files.get()}\n{file_name}".strip("\n"))
                elif msg_type == "files_list":
                    files_in_directory = msg.split(BREAK)
                    files_in_directory.sort()
                    files_list.clear()
                    files_list.extend(files_in_directory)
                    print(files_list)
                else:
                    print(f"Wrong message type! (message: {msg_type})")
            except RuntimeError:
                break
            except OSError:
                break

    def command_up():
        global current_command
        if current_command > -len(pre_commands):
            current_command -= 1
            command.set(pre_commands[current_command])
        else:
            print("Can't go up anymore!")

        print(f"current_command: {current_command}, -len(pre_commands): {-len(pre_commands)}")

    def command_down():
        global current_command
        if -1 > current_command:
            current_command += 1
            command.set(pre_commands[current_command])
        else:
            print("Can't go down anymore!")
        print(f"current_command: {current_command}")

    def send_button():
        global current_command
        execute_command(client_socket, command_entry.get(), msg_list),
        pre_commands.append(command.get()),
        command_entry.delete(0, tk.END)
        current_command = 0

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((IP, PORT))
    server_socket.listen()
    client_socket, client_address = server_socket.accept()

    tabs = {}
    for tab in ("Remote Desktop", "File Transfer", "Command Prompt", "Power Management"):
        tabs[tab] = tk.Frame(tab_frame)
        tab_frame.add(tabs[tab], text=tab)

        # Add elements to the "Remote Desktop" tab
        if tab == "Remote Desktop":
            label = tk.Label(tabs[tab], text="Remote desktop view:")
            label.pack(side="top", fill="x", padx=10, pady=10)
            canvas = tk.Canvas(tabs[tab], width=400, height=300, bd=1)
            canvas.pack(side="top", fill="both", expand=True, padx=10, pady=10)

        # Add elements to the "File Transfer" tab
        elif tab == "File Transfer":
            label = ttk.Label(tabs[tab], text="Select a file to transfer:")
            label.pack(side="top", fill="x", padx=10, pady=10)
            file_button = ttk.Button(tabs[tab], text="Browse...", command=lambda: browse_files(root, client_socket))
            file_button.pack(side="top", fill="x", padx=10, pady=10)

            files_label = ttk.Label(tabs[tab], textvariable=files)
            files_label.pack(side="bottom", padx=10, pady=10, anchor="e")

        # TODO: support CLEAR command - DONE
        # TODO: autofill with TAB
        # TODO: scroll to the previous commands with Up arrow - DONE
        # TODO: export output to file option
        # TODO: support "long live" commands
        # TODO: return errors
        # TODO: scrollbar don't scrolling
        # Add elements to the "Command Prompt" tab
        elif tab == "Command Prompt":
            messages_frame = ttk.Frame(tabs[tab])
            scrollbar = ttk.Scrollbar(messages_frame)
            msg_list = tk.Listbox(messages_frame, yscrollcommand=scrollbar.set, width=100, height=25,
                                  selectbackground="#333333", highlightthickness=0, activestyle="none")
            scrollbar["command"] = msg_list.yview
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=15)
            msg_list.pack(side=tk.LEFT, fill=tk.BOTH, padx=10, pady=10)
            messages_frame.pack()

            # label = ttk.Label(tabs[tab], text="Enter a command:")
            # label.pack(side="top", fill="x", padx=10, pady=10)
            command_entry = ttk.Entry(tabs[tab], textvariable=command)
            command_entry.bind("<Up>", lambda event: command_up())
            command_entry.bind("<Down>", lambda event: command_down())
            command_entry.bind("<Return>", lambda event: send_button())
            command_entry.pack(side="top", fill="x", padx=10)
            execute_button = ttk.Button(tabs[tab], text="Execute", command=lambda: send_button())
            execute_button.pack(side="top", fill="x", padx=10, pady=10)

        # Add elements to the "Power Management" tab
        elif tab == "Power Management":
            shutdown_button = ttk.Button(tabs[tab], text="Shutdown", command=lambda: shutdown(client_socket))
            shutdown_button.pack(side="top", fill="x", padx=10, pady=10)
            restart_button = ttk.Button(tabs[tab], text="Restart", command=lambda: restart(client_socket))
            restart_button.pack(side="top", fill="x", padx=10, pady=10)
            logout_button = ttk.Button(tabs[tab], text="Log Out", command=lambda: log_out(client_socket))
            logout_button.pack(side="top", fill="x", padx=10, pady=10)

            ip_label = ttk.Label(tabs[tab], text=f"ip address: {client_address}")
            ip_label.pack(side="bottom", padx=10, pady=5)
            dist_label = ttk.Label(tabs[tab], textvariable=client_dist)
            dist_label.pack(side="bottom", padx=10, pady=5)
            name_label = ttk.Label(tabs[tab], textvariable=client_name)
            name_label.pack(side="bottom", padx=10, pady=5)
            panel_label = ttk.Label(tabs[tab], text="system information:")
            panel_label.pack(side="bottom", padx=10, pady=10)

    receive_thread = Thread(target=receive)
    receive_thread.start()
    root.mainloop()

    client_socket.send("exit 0".encode())
    is_alive = False
    server_socket.close()
    client_socket.close()


if __name__ == "__main__":
    main()
