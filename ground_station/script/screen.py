import serial #导入模块
import time
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
        print(context)
    def print_end(self):
        self.ser.write(bytes.fromhex('ff ff ff'))

class Data:
    def __init__(self,xiang:int,hu:int,lang:int,hou:int,que:int):
        self.xiang=xiang
        self.hu=hu
        self.lang=lang
        self.hou=hou
        self.que=que

# ubuffer用于存放串口数据
ubuffer = bytearray()
FRAME_LENGTH:int=8

# 障碍坐标
obs:list[point]=[]
# 路径序列
path:list[point]=[]
# 动物数据
animal:list[list[Data]]=[]
total_animal:Data
# 与屏幕通信
post:Post
current_block:point=point(0,0)
# 与机载电脑通信
current_position:point=point(8,0)

def main():
    global total_animal,post,current_block,current_position,ubuffer
    init()
    while True:
        # 如果串口有数据，全部存放入ubuffer
        while post.ser.in_waiting:
            data = post.ser.read(post.ser.in_waiting)
            if data:
                ubuffer.extend(data)

        # 处理串口信息,当ubuffer的长度大于等于一帧的长度时
        if len(ubuffer) >= FRAME_LENGTH:
            # 判断帧头帧尾
            if (ubuffer[0] == 0x01 or ubuffer[0] == 0x02) and ubuffer[5] == 0xff and ubuffer[6] == 0xff and ubuffer[7] == 0xff:
                if(ubuffer[0] == 0x01):
                    x=int.from_bytes(ubuffer[1:2])
                    y=int.from_bytes(ubuffer[3:4])
                    obs.append(point(x,y))
                    #检测生成路径
                    if(len(obs)==3):
                        generate_path()

                elif(ubuffer[0] == 0x02):
                    x=int.from_bytes(ubuffer[1:2])
                    y=int.from_bytes(ubuffer[3:4])
                    current_block=point(x,y)
                # 删除1帧数据
                del ubuffer[:FRAME_LENGTH]
            else:
                # 删除最前面的1个数据
                del ubuffer[0]
        
        #绘制路径，绘制无人机位置，刷新文本信息
        draw()
        time.sleep(0.5)



def init():
    global post,animal,total_animal
    post=Post()
    for i in range(0,9):
        animal.append([])
        for j in range(0,7):
            animal[i].append(Data(0,0,0,0,0))
    total_animal=Data(0,0,0,0,0)

def generate_path():
    global path
    #生成路径
    if(len(obs)!=3):
        return -1
    ret = build_route(obs)
    path=[point(p.x,p.y) for p in ret]
    #发送路径给机载电脑
    pass

def draw():
    print("draw")
    post.write("ref s0")
    #刷新文本信息
    s1="A"+str(current_block.x+1)
    s2="B"+str(current_block.y+1)
    cur=animal[current_block.x][current_block.y]
    tot=total_animal
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
    #绘制无人机位置
    #绘制路径

if __name__=="__main__":
    main()
