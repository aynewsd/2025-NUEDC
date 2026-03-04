import serial #导入模块
class Post:
    def __init__(self) -> None:
        # 打开串口，并得到串口对象
        self.ser=serial.Serial(port="COM9",baudrate=115200,timeout=5)
        print("串口详情参数：", self.ser)
    def __delete__(self):
        self.ser.close()
        print("aaa")
    def write(self,context:str):
        result=self.ser.write(context.encode("utf-8"))
        self.print_end()
    def print_end(self):
        self.ser.write(bytes.fromhex('ff ff ff'))

def main():
    post=Post()
    print("bbb")

if __name__=="__main__":
    main()
