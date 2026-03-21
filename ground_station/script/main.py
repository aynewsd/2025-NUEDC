import serial
import threading
import time

from client import Client
from route import route as build_route
from Class import *


CONNECT_TIMEOUT = 120
SERIAL_PORT = "COM7"
SERVER_IP = "127.0.0.1"
SERVER_PORT = 8888


class Post:
    def __init__(self) -> None:
        self.ser = serial.Serial(port=SERIAL_PORT, baudrate=9600, timeout=10)
        self.lock = threading.Lock()

    def __del__(self):
        if hasattr(self, "ser") and self.ser:
            self.ser.close()

    def write(self, context: str):
        with self.lock:
            self.ser.write(context.encode("utf-8"))
            self.print_end()

    def print_end(self):
        self.ser.write(bytes.fromhex("ff ff ff"))


ubuffer = bytearray()
FRAME_LENGTH: int = 9

obs: list[point] = []
path: list[point] = []
path_matrix: list[list[list[int]]]
txt_matrix: list[list[str]]
animal: list[list[Data]] = []
post: Post = None
current_block: point = point(0, 0)
data_lock = threading.Lock()
shared_data = {
    "position": [455.0, 365.0],
    "animal": None,
    "total_animal": None,
}
comm_client: Client = None
server_connected: bool = False
page_switch_pending: bool = False
shutdown_requested: bool = False
shutdown_reason: str = ""


def request_shutdown(reason: str):
    global shutdown_requested, shutdown_reason, comm_client, post
    if shutdown_requested:
        return
    shutdown_requested = True
    shutdown_reason = reason
    print(reason)
    if comm_client:
        try:
            comm_client.stop()
        except Exception as e:
            print(f"client stop error: {e}")
    if post and getattr(post, "ser", None):
        try:
            if post.ser.is_open:
                post.ser.close()
        except Exception as e:
            print(f"serial close error: {e}")


def main():
    global current_block, page_switch_pending
    init()
    if shutdown_requested:
        raise SystemExit(1)

    while not shutdown_requested:
        try:
            if page_switch_pending and post and post.ser.is_open:
                post.write("page 1")
                page_switch_pending = False

            while post.ser.in_waiting:
                data = post.ser.read(post.ser.in_waiting)
                if data:
                    ubuffer.extend(data)

            while len(ubuffer) >= FRAME_LENGTH:
                if (
                    ubuffer[0] == 0xAA
                    and (ubuffer[1] == 0x01 or ubuffer[1] == 0x02)
                    and ubuffer[6] == 0xFF
                    and ubuffer[7] == 0xFF
                    and ubuffer[8] == 0xFF
                ):
                    if ubuffer[1] == 0x01:
                        x = ubuffer[2]
                        y = ubuffer[4]
                        if x >= 9 or y >= 7:
                            del ubuffer[0]
                            continue
                        obs.append(point(x, y))
                        if len(obs) == 3:
                            generate_path()
                            draw_path()
                    elif ubuffer[1] == 0x02:
                        x = ubuffer[2]
                        y = ubuffer[4]
                        if x >= 9 or y >= 7:
                            del ubuffer[0]
                            continue
                        current_block = point(x, y)
                    del ubuffer[:FRAME_LENGTH]
                else:
                    del ubuffer[0]

            draw()
            time.sleep(0.1)
        except serial.SerialException as e:
            request_shutdown(f"Serial runtime error on {SERIAL_PORT}: {e}")
        except Exception as e:
            request_shutdown(f"Main loop error: {e}")

    raise SystemExit(1)


def init():
    global post, animal, path_matrix, txt_matrix, comm_client
    try:
        post = Post()
    except serial.SerialException as e:
        request_shutdown(f"Serial open failed on {SERIAL_PORT}: {e}")
        return
    except Exception as e:
        request_shutdown(f"Unexpected serial init error: {e}")
        return

    for i in range(9):
        animal.append([])
        for j in range(7):
            animal[i].append(Data(0, 0, 0, 0, 0))
    path_matrix = [[[] for _ in range(7)] for _ in range(9)]
    txt_matrix = [["" for _ in range(7)] for _ in range(9)]

    post.ser.reset_input_buffer()
    post.ser.reset_output_buffer()

    shared_data["animal"] = animal
    shared_data["total_animal"] = Data(0, 0, 0, 0, 0)

    comm_client = Client(
        SERVER_IP,
        SERVER_PORT,
        shared_data,
        data_lock,
        on_connect=handle_client_connected,
        connect_timeout=CONNECT_TIMEOUT,
        on_connect_timeout=handle_client_connect_timeout,
    )
    comm_client.start()


def generate_path():
    global path
    if len(obs) != 3:
        return -1
    path = build_route(obs)
    for i in range(9):
        for j in range(7):
            if point(i, j) in obs:
                continue
            path_matrix[i][j] = [idx for idx, element in enumerate(path) if element == point(i, j)]
    for i in range(9):
        for j in range(7):
            if point(i, j) in obs:
                continue
            x = 32 + i * 50
            y = 52 + j * 50
            path_str = ",".join([str(num) for num in path_matrix[i][j]])
            txt_matrix[i][j] = 'xstr {},{},40,40,1,0,0,0,0,3,"{}"'.format(x, y, path_str)
    if comm_client:
        comm_client.send_path(path)


def draw():
    if len(path) != 0:
        draw_drone()
    draw_txt()


def draw_txt():
    with data_lock:
        cur = shared_data["animal"][current_block.x][current_block.y]
        tot = shared_data["total_animal"]
    s1 = "A" + str(current_block.x)
    s2 = "B" + str(6 - current_block.y)
    string = "t0.txt=\"当前选定块:{}{}\r\n\
    象:{} 虎:{}\r\n\
    狼:{} 猴:{}\r\n\
    孔雀:{}\r\n\
总数:\r\n\
    象:{} 虎:{}\r\n\
    狼:{} 猴:{}\r\n\
    孔雀:{}\r\n\"".format(
        s1,
        s2,
        cur.xiang,
        cur.hu,
        cur.lang,
        cur.hou,
        cur.que,
        tot.xiang,
        tot.hu,
        tot.lang,
        tot.hou,
        tot.que,
    )
    post.write(string)


def draw_drone():
    with data_lock:
        pos = shared_data["position"]
        post.write("p1.x={}".format(int(pos[0])))
        post.write("p1.y={}".format(int(pos[1])))


def draw_path():
    post.write("page 0")
    for i in range(9):
        for j in range(7):
            if point(i, j) in obs:
                continue
            post.write(txt_matrix[i][j])
    post.write("page 1")
    post.write("ref t1")
    post.write("ref t2")
    post.write("ref t3")


def handle_client_connected():
    global server_connected, page_switch_pending
    if not server_connected:
        server_connected = True
        page_switch_pending = True


def handle_client_connect_timeout():
    request_shutdown(f"Server connect timeout after {CONNECT_TIMEOUT}s")


if __name__ == "__main__":
    main()
