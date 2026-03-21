import serial #导入模块
import time
import threading
from client import Client
import json
from route import route as build_route
from Class import *
class Post:
    def __init__(self) -> None:
        # 打开串口，并得到串口对象
        self.ser=serial.Serial(port="COM7",baudrate=9600,timeout=10)
        #print("串口详情参数：", self.ser)
    def __del__(self):
        self.ser.close()
    def write(self,context:str):
        result=self.ser.write(context.encode("utf-8"))
        self.print_end()
    def print_end(self):
        self.ser.write(bytes.fromhex('ff ff ff'))

# ubuffer用于存放串口数据
ubuffer = bytearray()
FRAME_LENGTH:int=9

# 障碍坐标
obs:list[point]=[]
# 路径序列
path:list[point]=[]
path_matrix:list[list[list[int]]]
txt_matrix:list[list[str]]
# 动物数据
animal:list[list[Data]]=[]
# 与屏幕通信
post:Post=None
current_block:point=point(0,0)# 当前选择查看信息的格子
# 与机载电脑通信
# 增加锁
data_lock = threading.Lock()
# 共享数据容器，方便传递给client
shared_data = {
    "position": [455.0, 365.0],  # 初始默认值
    "animal": None,  # 将在init中创建
    "total_animal": None
}
comm_client:Client
server_connected:bool=False
def main():
    global post,current_block,ubuffer
    init()
    while True:
        # 如果串口有数据，全部存放入ubuffer
        while post.ser.in_waiting:
            data = post.ser.read(post.ser.in_waiting)
            if data:
                ubuffer.extend(data)

        # 处理串口信息,当ubuffer的长度大于等于一帧的长度时
        while len(ubuffer) >= FRAME_LENGTH:
            # 判断帧头帧尾
            if ubuffer[0] == 0xAA and (ubuffer[1] == 0x01 or ubuffer[1] == 0x02) and ubuffer[6] == 0xff and ubuffer[7] == 0xff and ubuffer[8] == 0xff:
                if(ubuffer[1] == 0x01):
                    x:int=ubuffer[2]
                    y:int=ubuffer[4]
                    if(x>=9 or y>=7):
                        del ubuffer[0]
                        continue
                    obs.append(point(x,y))
                    #检测生成路径
                    if(len(obs)==3):
                        #print(obs)
                        generate_path()# 生成路径，显示路径，将路径发送给机载电脑
                        draw_path()

                elif(ubuffer[1] == 0x02):
                    x:int=ubuffer[2]
                    y:int=ubuffer[4]
                    if(x>=9 or y>=7):
                        del ubuffer[0]
                        continue
                    current_block=point(x,y)
                    #print("更新"+str(current_block))
                # 删除1帧数据
                #print(ubuffer)
                del ubuffer[:FRAME_LENGTH]
            else:
                # 删除最前面的1个数据
                del ubuffer[0]
        
        #绘制无人机位置，刷新文本信息
        draw()
        time.sleep(0.1)



def init():
    global post,animal,path_matrix,txt_matrix,comm_client
    post=Post()
    for i in range(0,9):
        animal.append([])
        for j in range(0,7):
            animal[i].append(Data(0,0,0,0,0))
    path_matrix = [[[] for _ in range(7)] for _ in range(9)]
    txt_matrix = [["" for _ in range(7)] for _ in range(9)]
    # 初始化串口后，立即清空缓冲区
    post.ser.reset_input_buffer()
    post.ser.reset_output_buffer()
    #post.write("page 1") 改为连接到server后page 1
     # 初始化共享数据
    shared_data["animal"] = animal
    shared_data["total_animal"] = Data(0,0,0,0,0)
    # 启动client（服务器IP和端口请根据实际情况填写）
    client = Client("127.0.0.1", 8888, shared_data, data_lock, on_connect=handle_client_connected)
    client.start()
    # 将client保存到全局或某个地方，以便发送路径
    comm_client = client

def generate_path():
    global path
    #生成路径
    if(len(obs)!=3):
        return -1
    path = build_route(obs)# 调用route方法输出路径
    for i in range(9):
        for j in range(7):
            if(point(i,j) in obs):
                continue
            path_matrix[i][j]=[idx for idx, element in enumerate(path) if element == point(i,j)]
    for i in range(9):
        for j in range(7):
            if(point(i,j) in obs):
                continue
            x=32+i*50
            y=52+j*50
            path_str = ','.join([str(num) for num in path_matrix[i][j]])
            #print(path_str)
            txt_matrix[i][j]="xstr {},{},40,40,1,0,0,0,0,3,\"{}\"".format(x,y,path_str)  # 示例:xstr 32,52,40,40,1,0,0,0,0,3,"1,12,7"
    #发送路径给机载电脑
    if comm_client:
        comm_client.send_path(path)

def draw():
    #post.write("ref s0")
    if(len(path)!=0):
        #绘制无人机位置
        draw_drone()

    #刷新文本信息
    draw_txt()
    

def draw_txt():
    with data_lock:
        cur = shared_data["animal"][current_block.x][current_block.y]
        tot = shared_data["total_animal"]
    s1="A"+str(current_block.x)
    s2="B"+str(6-current_block.y)
    #print(s1+s2)
    string="t0.txt=\"当前选定块:{}{}\r\n\
    象:{} 虎:{}\r\n\
    狼:{} 猴:{}\r\n\
    孔雀:{}\r\n\
总数:\r\n\
    象:{} 虎:{}\r\n\
    狼:{} 猴:{}\r\n\
    孔雀:{}\r\n\"".format(s1,s2,
                            cur.xiang,cur.hu,cur.lang,cur.hou,cur.que,
                            tot.xiang,tot.hu,tot.lang,tot.hou,tot.que)
    post.write(string)

def draw_drone():
    with data_lock:
        pos = shared_data["position"]
        # 如果距离上次位置有变化，更新屏幕
        string = "p1.x={}".format(int(pos[0]))
        post.write(string)
        string = "p1.y={}".format(int(pos[1]))
        post.write(string)

def draw_path():
    post.write("page 0")
    for i in range(9):
        for j in range(7):
            if(point(i,j) in obs):
                continue
            post.write(txt_matrix[i][j])
    post.write("page 1")
    post.write("ref t1")
    post.write("ref t2")
    post.write("ref t3")

def handle_client_connected():
    global server_connected
    if not server_connected:
        server_connected = True
        post.write("page 1")
    

if __name__=="__main__":
    main()
