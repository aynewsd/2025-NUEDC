class point:
    def __init__(self,x:int,y:int) -> None:
        self.x=x
        self.y=y
    def __add__(self,other):
        return point(self.x+other.x,self.y+other.y)
    def __eq__(self,other):
        return self.x==other.x and self.y==other.y
    def __repr__(self):
        return f"Point(x={self.x}, y={self.y})"
    
class Data:
    def __init__(self,xiang:int,hu:int,lang:int,hou:int,que:int):
        self.xiang=xiang
        self.hu=hu
        self.lang=lang
        self.hou=hou
        self.que=que