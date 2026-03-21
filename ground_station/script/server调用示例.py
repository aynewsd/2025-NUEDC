# airborne_main.py
import time
import threading
from server import Server

# 假设我们有传感器数据获取函数（示例）
def get_current_position():
    # 实际应从飞控获取
    return (455.0, 365.0)  # 返回 (x, y) 浮点数

def get_cell_data(x, y):
    # 根据格子坐标获取动物数量，此处模拟随机数据
    import random
    return [random.randint(0,5) for _ in range(5)]  # [象,虎,狼,猴,孔雀]

# 路径接收回调
def on_path_received(path_list):
    """当地面站发送路径时调用"""
    print("收到新路径：", path_list)
    # 可以将路径转换为 point 对象列表（如果需要）
    # path_points = [point(p['x'], p['y']) for p in path_list]
    # 然后传给飞控执行任务...

def main():
    # 1. 创建 Server 实例，监听端口 8888
    server = Server(port=8888, path_callback=on_path_received)
    
    # 2. 启动服务器（在后台线程监听）
    server.start()
    print("机载服务器已启动，等待地面站连接...")
    x,y=get_current_position()
    # 3. 主循环：模拟周期发送数据
    try:
        while True:
            # 假设每秒发送一次更新
            time.sleep(1)
            
            # 获取当前位置
            #x, y = get_current_position()
            # 发送位置
            x-=10
            y-=10
            server.send_position(x, y)
            
            # 可选：发送所有格子的数据（或只发送变化的格子）
            # 例如遍历 9x7 网格
            for i in range(9):
                for j in range(7):
                    cell_data = get_cell_data(i, j)
                    server.send_cell(i, j, cell_data)
                    # 注意：如果格子数量多，可能产生大量消息，可合并或按需发送
    except KeyboardInterrupt:
        print("用户中断")
    finally:
        server.stop()

if __name__ == "__main__":
    main()