from Class import *


class dir:
    up=point(0,1)
    down=point(0,-1)
    left=point(-1,0)
    right=point(1,0)

def route(obs_:list[point]) -> list[point]:
    obs:list[point]=[point(8-i.x,6-i.y) for i in obs_]# 坐标系翻折
    path:list[point]=[]
    reverse_tag=0 # 不翻转 9*7 1:翻转 7*9
    back_tag=0 # 返回路径 0:下左, 1:左下
    detor_tag:point=dir.up# 绕行方向
    corner_tag=0# 情况5，结束情况
    cross_tag=0# 1:已越过障碍
    obs_line:int=0# 障碍行
    cdir:point=dir.up# 当前方向
    cur:point=point(0,0)
    COL:int=9
    ROW:int=7
    def add(pt=None):
        if(pt is None):
            pt=point(cur.x,cur.y)
        if(reverse_tag):# 坐标系翻转
            pt.x,pt.y=pt.y,pt.x
        pt.x=8-pt.x# 坐标系翻折(起点坐标从(0,0)映射回(8,0))
        pt.y=6-pt.y
        path.append(pt)
        #print(pt)
    
    def rev(pt:point):
        return point(-pt.x,-pt.y)

    def bound(position=None,direction=None):
        nonlocal cur,cdir
        if(position is None):
            position = cur
        if(direction is None):
            direction = cdir
        _cur=position+direction
        if(_cur.x>=COL or _cur.x<0 or _cur.y>=ROW or _cur.y<0):
            return 1
        elif(_cur==obs[0] or _cur==obs[1] or _cur==obs[2]):
            return 2
        else:
            return 0

    def fly_back():
        nonlocal cur,cdir
        if(back_tag):   cdir=dir.left
        else:   cdir=dir.down
        while not bound():
            cur=cur+cdir;add()
        if(back_tag):   cdir=dir.down
        else:   cdir=dir.left
        while not bound():
            cur=cur+cdir;add()
            

    #初始化
    if(len(obs)!=3):return path
    if(obs[1].y==obs[2].y and obs[0].y==obs[1].y):
        reverse_tag=0
    else:
        reverse_tag=1# 翻转坐标系
        obs=[point(i.y,i.x) for i in obs]
        COL,ROW=ROW,COL
    obs.sort(key=lambda pt:pt.x)
    obs_line=obs[0].y
    if(obs[0].y==ROW-1):detor_tag=dir.down
    else: detor_tag=dir.up
    if(obs[2]==point(COL-1,ROW-1)):
        corner_tag=1
    if(obs[0].y==0 or obs[2].x==COL-1):
        back_tag=1
    elif(obs[0].y==ROW-1 or obs[0].x==0):
        back_tag=0
    else:
        back_tag=0
    cross_tag=0

    #状态机启动
    add()
    cdir=dir.right
    over_count=0
    while True:
        over_count+=1
        if(over_count>=3000):
            print("overflow!")
            break
        if(obs_line==cur.y and not cross_tag):#情况1,2,4
            while not bound():
                cur=cur+cdir;add()
            if(corner_tag):#4
                fly_back()
                break
            cur=cur+detor_tag;add()
            for i in range(3):
                cur=cur+cdir;add()
            if bound()==1:#2
                cdir=rev(cdir)
                cross_tag=1
            else:#1
                cur=cur+cdir;add()
                cur=cur+rev(detor_tag);add()
                cross_tag=1
        while not bound():# 情况0,3,5
            cur=cur+cdir;add()
        if(cur==point(COL-1,ROW-1)):#5
            fly_back()
            break
        if(bound(cur,dir.up)==2):#3
            cdir=rev(cdir)
            for i in range(3):
                cur=cur+cdir;add()
            cur=cur+dir.up;add()
            while not bound():
                cur=cur+cdir;add()
            cur=cur+dir.up;add()
            cdir=rev(cdir)
        else:#0
            cur=cur+dir.up;add()
            cdir=rev(cdir)
        
    return path

def main():
    _obs=[point(1,1),point(1,2),point(1,3)]
    Path=route(_obs)

if __name__ == "__main__":
    main()
