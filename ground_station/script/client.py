import socket

SERVER_IP = "10.208.212.28" #服务器IP，当前为测试电脑IP，
PORT = 11111

# 要发送的数据（坐标或坐标链，可自定义格式）
# 示例：单个坐标 "(10,20)"，坐标链 "[(10,20),(30,40)]"
DATA = "(10,20)"   # 可根据需要修改

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SERVER_IP, PORT))
        print(f"已连接到服务器 {SERVER_IP}:{PORT}")

        # 发送数据
        s.sendall(DATA.encode())
        print(f"已发送数据: {DATA}")

        # 等待确认信号
        response = s.recv(2048).decode()
        if response == 'y':
            print("收到确认信号 'y'，传输完成")
        else:
            print(f"收到未知响应: {response}")

    print("客户端关闭")

if __name__ == "__main__":
    main()