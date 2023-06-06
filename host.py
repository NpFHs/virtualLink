import os.path
import struct
import time
import tkinter as tk
from tkinter import ttk
import socket
from threading import *
from tkinter import font
import rsa
import PIL
from PIL import Image, ImageTk
import shutil

IP: str = "0.0.0.0"
PORT: int = 8091
BREAK1 = "<BREAK1>"  # use to split between LEVEL1 data
BREAK2 = "<BREAK2>"  # use to split between LEVEL2 data
CLIENT_SCREEN_WIDTH = 750
pre_commands = []  # Storing the last commands the user enter.
current_command = 0  # Use to save the command location when the user press Up button.
current_directory = "/"
files_list = []
public_key, private_key = rsa.newkeys(2048)
client_public_key = None
current_file_in_files_list = 0  # indicate the current file location for tab_complete()
pre_command = ""  # save the original command for tab_complete()\
is_files_list_change = False  # mark when get new files list
is_screen_live = True
is_alive = True


# TODO: add multiple clients support. update: maybe not...


class UserInterface(ttk.Frame):
    def __init__(self, root):
        ttk.Frame.__init__(self)

        root.geometry("800x610")
        self.tab_frame = ttk.Notebook()
        self.tab_frame.pack(side="top", fill="both", expand=True, padx=5, pady=5)
        self.client_dist = tk.StringVar(value="Unknown")
        self.client_name = tk.StringVar(value="Unknown")
        self.client_name_with_name = tk.StringVar(value="Unknown")
        self.command = tk.StringVar(value="Enter a command")
        self.files = tk.StringVar()
        self.mono_font = font.Font(family="FreeMono")  # set the font to the msg_list

        self.client_address = "unknown"

        # flags that the buttons effect on
        self.restart_flag = False
        self.log_out_flag = False
        self.shutdown_flag = False
        self.execute_flag = False
        self.browser_flag = False
        self.stop_live_screen_flag = False
        self.reset_pre_commands_flag = False
        self.command_up_flag = False
        self.command_down_flag = False
        self.tab_complete_flag = False

        self.tabs = {}
        for tab in ("Remote Desktop", "File Transfer", "Command Prompt", "Power Management"):
            self.tabs[tab] = tk.Frame(self.tab_frame)
            self.tab_frame.add(self.tabs[tab], text=tab)

            # Add elements to the "Remote Desktop" tab
            if tab == "Remote Desktop":
                label = tk.Label(self.tabs[tab], text="Remote desktop view:")
                label.pack(side="top", fill="x", padx=10, pady=10)

                # create the started chart var
                start_screen = ImageTk.PhotoImage(
                    Image.open("./images/fullscreen.png").resize((CLIENT_SCREEN_WIDTH, CLIENT_SCREEN_WIDTH * 9 // 16)))

                self.screen_label = ttk.Label(self.tabs[tab], image=start_screen)
                # keep reference to the img, so it doesn't get prematurely garbage collected at the end of the function
                self.screen_label.image = start_screen
                self.screen_label.pack()

                self.get_screenshot_button = ttk.Button(self.tabs[tab], text="stop",
                                                        command=lambda: self.stop_live_screen())
                self.get_screenshot_button.pack(pady=20, padx=20, fill="y")

                # canvas = tk.Canvas(tabs[tab], width=400, height=300, bd=1)
                # canvas.pack(side="top", fill="both", expand=True, padx=10, pady=10)

            # Add elements to the "File Transfer" tab
            elif tab == "File Transfer":
                self.label = ttk.Label(self.tabs[tab], text="Select a file to transfer:")
                self.label.pack(side="top", fill="x", padx=10, pady=10)
                self.file_button = ttk.Button(self.tabs[tab], text="Browse...", command=lambda: self.browse_files())
                self.file_button.pack(side="top", fill="x", padx=10, pady=10)

                self.files_label = ttk.Label(self.tabs[tab], textvariable=self.files)
                self.files_label.pack(side="bottom", padx=10, pady=10, anchor="e")

            # TODO: export output to file option
            # TODO: support "long live" commands
            # TODO: return errors
            # TODO: add hebrew support in windows
            # Add elements to the "Command Prompt" tab
            elif tab == "Command Prompt":
                self.execute_button = ttk.Button(self.tabs[tab], text="Execute", command=lambda: self.send_button())
                self.execute_button.pack(side="bottom", fill="x", padx=10, pady=10)
                self.command_entry = ttk.Entry(self.tabs[tab], textvariable=self.command)
                self.command_entry.bind("<Up>", lambda event: self.command_up())
                self.command_entry.bind("<Down>", lambda event: self.command_down())
                self.command_entry.bind("<Return>", lambda event: self.send_button())
                self.command_entry.bind("<Tab>", lambda event: self.tab_complete())
                self.command_entry.bind("<Key>", lambda event: self.reset_pre_command())
                self.command_entry.pack(side="bottom", fill="x", padx=10)

                self.messages_frame = ttk.Frame(self.tabs[tab])
                self.scrollbar = ttk.Scrollbar(self.messages_frame)
                self.msg_list = tk.Listbox(self.messages_frame, yscrollcommand=self.scrollbar.set, width=100, height=25,
                                           selectbackground="#333333", highlightthickness=0, activestyle="none",
                                           font=self.mono_font)
                self.scrollbar["command"] = self.msg_list.yview
                self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=15)
                self.msg_list.pack(side=tk.LEFT, fill=tk.BOTH, padx=10, pady=10)
                self.messages_frame.pack()

            # Add elements to the "Power Management" tab
            elif tab == "Power Management":
                self.shutdown_button = ttk.Button(self.tabs[tab], text="Shutdown", command=lambda: self.shutdown())
                self.shutdown_button.pack(side="top", fill="x", padx=10, pady=10)
                self.restart_button = ttk.Button(self.tabs[tab], text="Restart", command=lambda: self.restart())
                self.restart_button.pack(side="top", fill="x", padx=10, pady=10)
                self.logout_button = ttk.Button(self.tabs[tab], text="Log Out", command=lambda: self.log_out())
                self.logout_button.pack(side="top", fill="x", padx=10, pady=10)

                self.ip_label = ttk.Label(self.tabs[tab], text=f"ip address: {self.client_address}")
                self.ip_label.pack(side="bottom", padx=10, pady=5)
                self.dist_label = ttk.Label(self.tabs[tab], textvariable=self.client_dist)
                self.dist_label.pack(side="bottom", padx=10, pady=5)
                self.name_label = ttk.Label(self.tabs[tab], textvariable=self.client_name_with_name)
                self.name_label.pack(side="bottom", padx=10, pady=5)
                self.panel_label = ttk.Label(self.tabs[tab], text="system information:")
                self.panel_label.pack(side="bottom", padx=10, pady=10)

    def set_client_address(self, client_address):
        self.client_address = client_address
        self.ip_label.configure(text=f"ip address: {self.client_address}")

    def send_button(self):
        self.execute_flag = True

    def restart(self):
        self.restart_flag = True

    def log_out(self):
        self.log_out_flag = True

    def shutdown(self):
        self.shutdown_flag = True

    def browse_files(self):
        self.browser_flag = True

    def stop_live_screen(self):
        self.stop_live_screen_flag = True

    def reset_pre_command(self):
        self.reset_pre_commands_flag = True

    def command_up(self):
        self.command_up_flag = True

    def command_down(self):
        self.command_down_flag = True

    def tab_complete(self):
        self.tab_complete_flag = True
        # disable focus change when tab pressed.
        return "break"


def encrypt(msg):
    try:
        enc_msg = rsa.encrypt(msg.encode(), client_public_key)  # NOQA
    except:
        print("Encryption error")
        enc_msg = b"error"
    return enc_msg


def decrypt(msg):
    # add except for case of failure in decryption.
    origin_msg = rsa.decrypt(msg, private_key)
    return origin_msg


def send_public_key(client_socket):
    pass


def shutdown(client_socket):
    command = f"power shutdown"
    client_socket.send(encrypt(command))
    print(command)


def restart(client_socket):
    """
    Sent restart command to the client.
    """
    command = f"power restart"
    client_socket.send(encrypt(command))
    print(command)


def log_out(client_socket):
    command = f"power log_out"
    client_socket.send(encrypt(command))
    print(command)


def get_resp(client_socket):
    msg_len = client_socket.recv(8)
    if msg_len.isdigit():
        enc_resp = client_socket.recv(int(msg_len))
        print(f"enc_resp: {enc_resp}")

        resp = enc_resp
    else:
        print("No length info!")

        # clean possible garbage
        client_socket.recv(16777216)
        resp = b"Error, no length info!"

    try:
        msg_type = resp.split()[0].decode()
    except IndexError:
        msg_type = "Error"
    msg = b" ".join(resp.split(b" ")[1:])

    return msg_type, msg


def execute_command(client_socket, ui):
    cmd = ui.command_entry.get()
    # avoid index error on empty command
    if cmd:
        if cmd == "clear":
            ui.msg_list.delete(0, tk.END)
        else:
            command = f"execute {cmd}"
            client_socket.send(encrypt(command))

        # keep the files list up to date
        if cmd.split()[0] == "cd":
            request_files_in_location(client_socket)


def request_file(file_location, client_socket):
    client_socket.send(encrypt(f"file {file_location}"))


def request_files_in_location(client_socket, location="CURRENT"):
    """
    Used to get list of files in given location.
    if not given, return list of the files in the client current directory.
    """
    client_socket.send(encrypt(f"files_list {location}"))


def open_folder(browser, client_socket, file_location):
    global current_directory
    global is_files_list_change

    try:
        file_iid = browser.selection()[0]  # get the iid of the selected file. E.g: file_idd: 'I006'.
        file_values = browser.item(file_iid)["values"]
        file_type = file_values[0]
        file_name = file_values[1]
        if file_type == "DIR":
            browser_previous_directory = current_directory
            current_directory = f"{current_directory}{file_name}/"
            request_files_in_location(current_directory, client_socket)
            # time.sleep(0.5)  # wait to the files list to update
            while not is_files_list_change:  # wait to the files list to change
                print(f"is_files_list_change: {is_files_list_change}")
                continue
            if "".join(files_list) == "PermissionError":
                current_directory = browser_previous_directory
            else:
                browser.delete(*browser.get_children())  # clear the browser
                for file in files_list:
                    tuple_file = file.split(BREAK2)  # split the file string to the browser columns
                    browser.insert("", tk.END, values=tuple_file)
            is_files_list_change = False
        elif file_type == "FILE":
            file_location.set(current_directory + file_name)
        else:
            print("The file is not a directory of readable file!")
    except IndexError:
        print("IndexError")


def browser_go_back(browser, client_socket):
    global current_directory

    if current_directory.count("/") > 1:
        current_directory = "/".join(current_directory.split("/")[:-2]) + "/"  # update cwd
        request_files_in_location(client_socket, current_directory)
        time.sleep(0.5)  # wait until the files list update
        browser.delete(*browser.get_children())
        for file in files_list:
            tuple_file = file.split(BREAK2)  # split the file string to the browser columns
            browser.insert("", tk.END, values=tuple_file)


def browse_files(win, client_socket):
    file_location = tk.StringVar()
    top = tk.Toplevel(win)
    top.title("File browser")
    top.geometry("350x500")
    current_path = tk.StringVar(value="/...")
    # the button and the entry before the browser, so when the user change the window size they will always be visible.
    get_file = ttk.Button(top, text="Get file",
                          command=lambda: [request_file(file_location.get(), client_socket),
                                           location_entry.delete(0, tk.END)])
    get_file.pack(side="bottom", fill="x", padx=10, pady=10)

    location_entry = ttk.Entry(top, textvariable=file_location)
    location_entry.bind("<Return>", lambda event: [request_file(file_location.get(), client_socket),
                                                   location_entry.delete(0, tk.END)])
    location_entry.pack(side="bottom", fill="x", padx=10, pady=5)

    columns = ("type", "name", "size")
    file_browser = ttk.Treeview(top, columns=columns)  # create the files browser
    file_browser["show"] = "headings"  # to avoid empty column in the beginning
    file_browser.heading("type", text="type")
    file_browser.column("type", width=40)
    file_browser.heading("name", text="name")
    file_browser.column("name", width=160)
    file_browser.heading("size", text="size")
    file_browser.column("size", width=80)
    file_browser.bind("<Double-Button-1>", lambda event: open_folder(file_browser, client_socket, file_location))
    file_browser.bind("<Return>", lambda event: open_folder(file_browser, client_socket, file_location))

    file_browser.pack(side="bottom", padx=10, pady=10, fill="both", expand=True)

    path_combobox = ttk.Combobox(top, textvariable=current_path)
    path_combobox.pack(side="right", anchor="ne", fill="x", expand=True, padx=10, pady=(10, 0))
    separator = ttk.Separator(top, orient="vertical")
    separator.pack(side="right", fill="y", pady=(14, 4))
    back_button = ttk.Button(top, text="<", width=1, command=lambda: browser_go_back(file_browser, client_socket))
    back_button.pack(side="right", anchor="nw", padx=10, pady=(10, 0))

    request_files_in_location(client_socket, current_directory)
    time.sleep(0.5)  # wait until the files list update TODO: it's ABSOLUTELY WRONG way to do it
    file_browser.delete(*file_browser.get_children())

    for file in files_list:
        tuple_file = file.split(BREAK2)  # split the file string to the browser columns
        file_browser.insert("", tk.END, values=tuple_file)


def receive_sys_info(msg, client_dist, client_name_with_name, client_name):
    if msg.split()[0] == "os":
        client_dist.set("OS: " + " ".join(msg.split(" ")[1:]))
    elif msg.split()[0] == "name":
        name = " ".join(msg.split(" ")[1:])
        client_name_with_name.set("Name: " + name)
        client_name.set(name)


def receive_execute(msg, msg_list, client_name):
    path = msg.split()[0]
    output = " ".join(msg.split(" ")[1:]).splitlines()
    for line in output:
        msg_list.insert(tk.END, line)
    msg_list.insert(tk.END, "")
    msg_list.insert(tk.END, f"({client_name.get()}):{path}$ ")
    msg_list.see(tk.END)


def receive_file(msg, client_socket, files):
    if msg.split()[0] == "FileNotFound":
        print("file not found!")
    else:
        file_name, file_size = msg.split(BREAK1)

        file_name = os.path.basename(file_name)
        # currently not needed.
        # file_size = int(file_size)
        with open(file_name, "wb") as file:
            while True:
                msg_len = client_socket.recv(8)
                if msg_len.isdigit():
                    bytes_file = client_socket.recv(int(msg_len))
                else:
                    print("No length info!")
                    # clean possible garbage
                    client_socket.recv(16777216)
                    bytes_file = "Error".encode()

                if bytes_file == "file done".encode():
                    break
                file.write(bytes_file)
            files.set(f"{files.get()}\n{file_name}".strip("\n"))


def receive_files_list(msg):
    global is_files_list_change
    files_in_directory = msg.split(BREAK1)
    files_in_directory.sort()
    files_list.clear()
    files_list.extend(files_in_directory)
    is_files_list_change = True
    print(f"is_files_list_change: {is_files_list_change}")


def receive_screenshot(live_screen_socket, msg="start"):
    if msg == "start":
        # # somehow "wb" mode append instead of re-write the file.
        # open("/home/noam/PycharmProjects/virtualLink/images/current_screen.png", "w").close()
        with open("/home/noam/PycharmProjects/virtualLink/images/current_screen.png", "wb") as current_screen:

            live_screen_socket.send("1".encode())
            while True:
                data_len = live_screen_socket.recv(8)
                # print(f"data_len: {data_len}")
                if data_len.isdigit():
                    time.sleep(0.01)
                    data = live_screen_socket.recv(int(data_len))
                    # print(f"len(data): {len(data)}")
                    # temp; without this lines something goes wrong (the program don't receive the hole screenshot part)
                    if len(data) != int(data_len):
                        # print(f"{len(data)}:{int(data_len)}")
                        pass
                    if data == b"screenshot done":
                        print("pre screen updated.")

                        # save the current screen for case of broken one in the next time
                        shutil.copyfile("./images/current_screen.png", "./images/pre_screen.png")
                        return None
                    current_screen.write(data)
                    live_screen_socket.send("1".encode())

                else:
                    print("wrong message format! (missing length data)")
                    # print(f"data_len: {data_len}")
                    # clean garbage
                    trash = live_screen_socket.recv(16777216)
                    print(f"len(trash): {len(trash)}")
                    # tell the client to re-send the image
                    live_screen_socket.send("2".encode())
                    # raise "LengthError"
                    break


        # remove broken file
        os.remove("/home/noam/PycharmProjects/virtualLink/images/current_screen.png")
        shutil.copyfile("/home/noam/PycharmProjects/virtualLink/images/pre_screen.png",
                        "/home/noam/PycharmProjects/virtualLink/images/current_screen.png")

    else:
        print("screenshot format not valid!")


def reset_pre_command():
    global current_file_in_files_list
    current_file_in_files_list = 0


def get_screenshot(live_screen_socket, screen_label):
    # hint the client to sent new screenshot
    receive_screenshot(live_screen_socket)
    update_screen(screen_label)


def update_screen(screen_label):
    try:
        current_screen = ImageTk.PhotoImage(
            Image.open("./images/current_screen.png").resize((CLIENT_SCREEN_WIDTH, CLIENT_SCREEN_WIDTH * 9 // 16)))
    except (SyntaxError, PIL.UnidentifiedImageError, OSError):
        try:
            current_screen = ImageTk.PhotoImage(
                Image.open("./images/pre_screen.png").resize((CLIENT_SCREEN_WIDTH, CLIENT_SCREEN_WIDTH * 9 // 16)))
        except (SyntaxError, PIL.UnidentifiedImageError, OSError):
            current_screen = ImageTk.PhotoImage(
                Image.open("./images/bad_image.png").resize((CLIENT_SCREEN_WIDTH, CLIENT_SCREEN_WIDTH * 9 // 16)))

    screen_label.configure(image=current_screen)
    screen_label.image = current_screen


def keep_client_screen_alive(live_screen_socket, screen_label):
    while is_screen_live:
        get_screenshot(live_screen_socket, screen_label)


def stop_live_screen():
    global is_screen_live
    is_screen_live = False


def command_up(ui):
    global current_command
    if current_command > -len(pre_commands):
        current_command -= 1
        ui.command.set(pre_commands[current_command])
    else:
        print("Can't go up anymore!")

    reset_pre_command()


def command_down(ui):
    global current_command
    if -1 > current_command:
        current_command += 1
        ui.command.set(pre_commands[current_command])
    else:
        print("Can't go down anymore!")

    reset_pre_command()


def tab_complete(ui):
    global current_file_in_files_list, pre_command

    # save the current command only at the first time tab pressed
    if current_file_in_files_list == 0:
        pre_command = ui.command.get()

    if current_file_in_files_list >= len(files_list):
        current_file_in_files_list = 0

    try:
        file_name = files_list[current_file_in_files_list].split(BREAK2)[1]
        ui.command.set(f"{pre_command} {file_name}")
        current_file_in_files_list += 1
        ui.command_entry.icursor(tk.END)
    except IndexError:
        pass


def send_button(client_socket, ui):
    global current_command, current_file_in_files_list
    execute_command(client_socket, ui)
    pre_commands.append(ui.command.get())
    ui.command_entry.delete(0, tk.END)
    current_command = 0

    # include in bind <Key>.
    # # reset the current file for tab_complete()
    # current_file_in_files_list = 0


def handle_ui_buttons(ui, client_socket):
    while is_alive:
        if ui.restart_flag:
            restart(client_socket)
            ui.restart_flag = False

        elif ui.log_out_flag:
            log_out(client_socket)
            ui.log_out_flag = False

        elif ui.shutdown_flag:
            shutdown(client_socket)
            ui.shutdown_flag = False

        elif ui.execute_flag:
            send_button(client_socket, ui)
            ui.execute_flag = False

        elif ui.browser_flag:
            browse_files(ui.root, client_socket)
            ui.browser_flag = False

        elif ui.stop_live_screen_flag:
            stop_live_screen()
            ui.stop_live_screen_flag = False

        elif ui.reset_pre_commands_flag:
            reset_pre_command()
            ui.reset_pre_commands_flag = False

        elif ui.command_up_flag:
            command_up(ui)
            ui.command_up_flag = False

        elif ui.command_down_flag:
            command_down(ui)
            ui.command_down_flag = False

        elif ui.tab_complete_flag:
            tab_complete(ui)
            ui.tab_complete_flag = False

        time.sleep(0.2)


def receive(client_socket, ui):
    global public_key, client_public_key
    print("Start receiving")
    while is_alive:
        try:
            msg_type, msg = get_resp(client_socket)

            print(f"type(msg): {type(msg)}")
            print(f"msg: {msg}")
            if msg_type == "sys_info":
                receive_sys_info(msg.decode(), ui.client_dist, ui.client_name_with_name, ui.client_name)

            elif msg_type == "execute":
                receive_execute(msg.decode(), ui.msg_list, ui.client_name)

            elif msg_type == "file":
                receive_file(msg.decode(), client_socket, ui.files)

            elif msg_type == "files_list":
                receive_files_list(msg.decode())

            elif msg_type == "public_key":
                client_public_key = rsa.key.PublicKey.load_pkcs1(msg, format="DER")
                # print(f"\ntype(client_public_key): {type(client_public_key)}\nclient_public_key: {client_public_key}\n")  # NOQA

            else:
                print(f"Wrong message type! (message: {msg_type})")
        except RuntimeError:
            break
        except OSError:
            break


def main():
    global is_screen_live, is_alive
    root = tk.Tk()
    root.tk.call("source", "azure.tcl")
    root.tk.call("set_theme", "dark")
    root.title("Remote Control")

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((IP, PORT))
    server_socket.listen()
    print("Listening...")

    client_socket, client_address = server_socket.accept()
    live_screen_socket, client_address = server_socket.accept()

    ui = UserInterface(root)
    ui.set_client_address(client_address)

    receive_thread = Thread(target=lambda: receive(client_socket, ui))
    receive_thread.start()
    ui_buttons_thread = Thread(target=lambda: handle_ui_buttons(ui, client_socket))
    ui_buttons_thread.start()
    client_live_screen = Thread(target=lambda: keep_client_screen_alive(live_screen_socket, ui.screen_label))
    client_live_screen.start()

    while True:
        if client_public_key != None:
            break
        time.sleep(0.1)

    # keep the files list updated
    request_files_in_location(client_socket)

    root.mainloop()

    client_socket.send(encrypt("exit 0"))
    is_alive = False
    is_screen_live = False
    server_socket.close()
    client_socket.close()


if __name__ == "__main__":
    main()
