import socket
import sys

HOST = ''
PORT = 11111

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(1)
        s.settimeout(1)  # 设置超时1秒
        print(f"服务器启动")
        
        try:
            while True:
                try:
                    conn, addr = s.accept()  # 每1秒超时一次
                except socket.timeout:
                    continue  # 超时后继续循环，以便检查 KeyboardInterrupt
                except KeyboardInterrupt:
                    raise  # 如果在 accept 内收到信号（很少发生），向上传递
                
                # 处理连接...
                with conn:
                    print(f"客户端 {addr} 已连接")
                    data = conn.recv(2048).decode()
                    print(f"收到: {data}")
                    conn.sendall(b'y')
                print("连接处理完毕")
                break
        except KeyboardInterrupt:
            sys.exit(0)

if __name__ == "__main__":
    main()