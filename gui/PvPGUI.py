import tkinter as tk
from functools import partial
import threading
import socket
from tkinter import messagebox

import pygame

Ox = 20  # Số lượng ô theo trục X
Oy = 20  # Số lượng ô theo trục Y


class Window(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Play Gomoku!")
        self.Buts = {}
        self.current_player = "server"
        self.turn_locked = False
        self.ip_label = tk.Label(self, text="Host IP: ")
        self.ip_label.grid(row=0, column=1, padx=0)
        self.Threading_socket = Threading_socket(self, self.ip_label)
        # Initialize pygame window
        pygame.init()
        self.pygame_screen = pygame.display.set_mode((800, 600))
        print(self.Threading_socket.name)

    def showFrame(self, Ox, Oy):
        frame1 = tk.Frame(self)
        frame1.grid(row=0, column=0)
        frame2 = tk.Frame(self)
        frame2.grid(row=1, column=0)

        tk.Label(frame1, text="IP", pady=4).grid(row=0, column=1)
        inputIp = tk.Entry(frame1, width=20)  # Khung nhập địa chỉ ip
        inputIp.grid(row=0, column=2, padx=5)
        connectBT = tk.Button(frame1, text="Connect", width=10,
                              command=lambda: self.Threading_socket.clientAction(inputIp.get()))
        connectBT.grid(row=0, column=3, padx=3)

        makeHostBT = tk.Button(frame1, text="MakeHost", width=10,  # nút tạo host
                               command=lambda: self.start_server_thread())
        makeHostBT.grid(row=0, column=4, padx=30)
        # Draw pygame board
        for x in range(Ox):
            for y in range(Oy):
                self.Buts[x, y] = tk.Button(frame2, font=('arial', 15, 'bold'), height=1, width=2,
                                            borderwidth=2, command=partial(self.handleButton, x=x, y=y))
                self.Buts[x, y].grid(row=x, column=y)

    def start_server_thread(self):
        thread = threading.Thread(target=self.Threading_socket.serverAction, args=(self.ip_label,))
        thread.start()

    def handleButton(self, x, y):
        if self.Buts[x, y]['text'] == '':
            if not self.turn_locked:
            # print(self.Threading_socket.name)
                if self.current_player == self.Threading_socket.name:
                    # Chỉ cho phép đánh cờ nếu ô cờ trống và đến lượt của current_player
                    self.play_turn(x, y, self.Threading_socket.name)
                    self.turn_locked = True
                    # Chuyển lượt cho người chơi khác
                    # self.toggle_player_turn()
                    print("Lượt đánh : ", self.current_player)
                else:
                    print(self.current_player)
                    print(self.Threading_socket.name)
            else:
                print("Lượt đánh đã bị khóa.")
        else:
            pass

    def play_turn(self, x, y, player):
        tag = 'O' if player == "server" else 'X'
        self.Buts[x, y]['text'] = tag
        self.Threading_socket.sendData("{}|{}|{}|{}".format("hit", x, y, tag))
        if self.checkWin(x, y, tag, Ox, Oy):
            self.notification("Winner: ", player)
            self.newGame(Ox, Oy)

    def update_ui(self, x, y, player):
        self.Buts[x, y]['text'] = player
        if player == 'O':
            self.current_player = "client"
            winner = 'server'
        elif player == 'X':
            self.current_player = "server"
            winner = 'client'
        if self.checkWin(x, y, player, Ox, Oy):
            self.notification("Winner: ", winner)
            self.newGame(Ox, Oy)
        self.turn_locked = False

    def notification(self, title, msg):
        messagebox.showinfo(str(title), str(msg))

    def checkWin(self, x, y, XO, Ox, Oy):
        def checkDirection(dx, dy):
            count = 1
            i, j = x + dx, y + dy

            # Kiểm tra xem vị trí mới có nằm trong biên của bảng không
            while 0 <= i < Ox and 0 <= j < Oy and self.Buts[i, j]["text"] == XO:
                count += 1
                i += dx
                j += dy

            i, j = x - dx, y - dy
            while 0 <= i < Ox and 0 <= j < Oy and self.Buts[i, j]["text"] == XO:
                count += 1
                i -= dx
                j -= dy
            return count >= 5

        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]  # Hàng, cột, đường chéo phải, đường chéo trái

        # Kiểm tra từng hướng
        for dx, dy in directions:
            if checkDirection(dx, dy):
                return True
        return False

    def newGame(self, Ox, Oy):
        for x in range(Ox):
            for y in range(Oy):
                self.Buts[x, y]['text'] = ''


class Threading_socket():
    def __init__(self, gui, ip_label, conn=None):
        super().__init__()
        self.dataReceive = ""
        self.conn = conn
        self.gui = gui
        self.name = ""
        self.ip_label = ip_label

    def clientAction(self, inputIP):
        self.name = "client"
        print("client connect ...............")
        HOST = inputIP  # Cấu hình địa chỉ server
        PORT = 8000  # Cấu hình Port sử dụng

        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Cấu hình socket
        try:
            self.conn.connect((HOST, PORT))  # tiến hành kết nối đến server
        except ConnectionRefusedError:
            print("Connection refused. Server may not be available.")
            return
        self.gui.notification("Đã kết nối tới", str(HOST))
        if inputIP:  # Kiểm tra nếu ip_label được truyền vào
            self.ip_label.config(text=f"Host IP: {HOST}")  # Cập nhật địa chỉ IP lên nhãn
        t1 = threading.Thread(target=self.client)  # tạo luồng chạy client
        t1.start()

    def serverAction(self, ip_label=None):
        local_ip = get_local_ip()
        self.name = "server"
        HOST = local_ip  # Láy  lập địa chỉ
        print("Make host.........." + HOST)
        if ip_label:  # Kiểm tra nếu ip_label được truyền vào
            ip_label.config(text=f"Host IP: {HOST}")  # Cập nhật địa chỉ IP lên nhãn
        PORT = 8000  # Thiết lập port lắng nghe
        # cấu hình kết nối
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind((HOST, PORT))  # lắng nghe
            s.listen(2)  # thiết lập tối ta 2 kết nối đồng thời
            self.conn, addr = s.accept()  # chấp nhận kết nối và trả về thông số
            t2 = threading.Thread(target=self.server, args=(addr, s))
            t2.start()
        except Exception as e:
            print("Error:", e)
            if self.conn:
                self.conn.close()
            s.close()

    def server(self, addr, s):
        try:
            # in ra thông địa chỉ của client
            print('Connected by', addr)
            while True:
                # Đọc nội dung client gửi đến
                try:
                    self.dataReceive = self.conn.recv(1024).decode()
                    if self.dataReceive != "":
                        action = self.dataReceive.split("|")[0]
                        turn = self.dataReceive.split("|")[3]
                        print(action)
                        if action == "hit" and turn == "X":
                            x = int(self.dataReceive.split("|")[1])
                            y = int(self.dataReceive.split("|")[2])
                            self.gui.update_ui(x, y, turn)
                            # self.gui.handleButton(x, y)
                    self.dataReceive = ""
                except ConnectionResetError:
                    print("Connection to client reset.")
                    break
        finally:
            s.close()  # đóng socket

    def client(self):
        while True:
            try:
                self.dataReceive = self.conn.recv(1024).decode()  # Đọc dữ liệu server trả về
                if self.dataReceive != "":
                    action = self.dataReceive.split("|")[0]
                    turn = self.dataReceive.split("|")[3]
                    if action == "hit" and turn == "O":
                        x = int(self.dataReceive.split("|")[1])
                        y = int(self.dataReceive.split("|")[2])
                        self.gui.update_ui(x, y, turn)
                        # self.gui.handleButton(x, y)
                        print(action, turn, x, y)
                self.dataReceive = ""
            except ConnectionResetError:
                print("Connection to server reset.")
                break

    def sendData(self, data):
        # Gửi dữ liệu
        if self.conn:
            self.conn.sendall(str(data).encode())
            print(f"Sent data: {data}")
        else:
            print("Kết nối không được thiết lập.")


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('192.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP
