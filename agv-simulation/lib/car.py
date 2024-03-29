# -*- coding: utf-8 -*-
import math, time
import threading
from lib.connector import Connector
import lib.tool as Tool
import config.config as config


class Car():
    def __init__(self, name, position, target, sites, graph, speed):
        self.position = position  # [0,0]
        self.target = target  # [100,100]
        self.path = None
        self.willpath = None
        self.sites = sites
        self.graph = graph
        self.speed = speed  # 10
        self.status = '0'  # 0-空闲，1-完成任务，2-运行，3-红外防撞，4-空闲，5-暂停，6-货架举放中，7-充电，81-红外防撞，246-待机模式
        self.x_step = 0
        self.y_step = 0
        self.name = name
        self.id = 'ax001'
        self.con = Connector()
        self._init_path(target)


        '''
        self.sites = {
            '1':[100, 900],
            '2':[300, 900],
            '3':[300, 700],
            '4':[100, 700]
        }

        self.graph = {
            '1':['2','4'],
            '2':['1','3'],
            '3':['2','4'],
            '4':['1','3']
        }
        '''

    def get_near_site(self):
        for k, v in self.graph.items():
            if self.position == self.sites[k]:
                return [k]
            else:
                s1 = self.sites[k]
                for dst in v:
                    s2 = self.sites[dst]
                    # if Tool.three_point_online(s1,self.position,s2):
                    if Tool.three_point_like_line(s1, self.position, s2, 5):
                        return [k, dst]

    def compute_distance(self, position=None, nextp=None):
        # 计算当前点到下一站点的距离
        if position == None:
            position = self.position
        if nextp == None:
            nextp = self.sites[self.willpath[0]]
        x_dis = nextp[0] - position[0]
        y_dis = nextp[1] - position[1]
        distance = math.sqrt((x_dis ** 2) + (y_dis ** 2))
        if distance != 0:
            x_step = round(self.speed / distance, 8) * (x_dis)
            y_step = round(self.speed / distance, 8) * (y_dis)
        else:
            x_step = 0
            y_step = 0
        result = {'nextp': nextp, 'distance': distance, 'x_step': x_step, 'y_step': y_step}
        return result

    def compute_path_distance(self, position=None, path=None):
        # 计算当前坐标到路径终点的距离
        if position == None:
            position = self.position
        distance = 0
        tmps = position
        for pxy in path:
            x_dis = self.sites[pxy][0] - tmps[0]
            y_dis = self.sites[pxy][1] - tmps[1]
            distance = distance + (math.sqrt((x_dis ** 2) + (y_dis ** 2)))
            tmps = self.sites[pxy]
        return distance

    def _align_step(self):
        # 校准小车位置到站点
        if len(self.willpath) != 0:
            nextp = self.willpath[0]
            nextpxy = self.sites[nextp][:]
            if abs(self.position[0] - nextpxy[0]) <= abs(self.x_step) and abs(self.position[1] - nextpxy[1]) <= abs(
                    self.y_step):
                self.x_step = nextpxy[0] - self.position[0]
                self.y_step = nextpxy[1] - self.position[1]
                return nextpxy
            else:
                return None

    def change_target(self, target):
        # target_p = self._get_sites_key(target)
        if self.target == target:
            return self.path
        else:
            self.target = target
        re = self._init_path(target)
        return re

    def change_speed(self, speed):
        self.speed = float(speed)
        dist = self.compute_distance(self.position, self.willpath[0])
        self.x_step = dist['x_step']
        self.y_step = dist['y_step']
        self.set_car_msg('speed', str(self.speed))
        pass

    def _init_path(self, target):
        # 初始化路径：根据当前坐标+目的坐标，初始化行走路径，x_step,y_step
        target = self._get_sites_key(target)
        nearsites = self.get_near_site()
        spath = None
        # 待改进，暂没有运算路径间距离
        for near in nearsites:
            x = Tool.find_shartest_path(graph, near, target)
            distance = self.compute_path_distance(self.position, x)
            if not spath:
                spath = [x, distance]
            elif distance < spath[1]:
                spath = [x, distance]
        dist = self.compute_distance(self.position, self.sites[spath[0][0]])
        self.path = spath[0]
        self.willpath = self.path
        self.x_step = dist['x_step']
        self.y_step = dist['y_step']
        self.set_car_msg('target', str(self.target))
        self.set_car_msg('speed', str(self.speed))
        return self.path

    def switch_nextpoint(self):
        del (self.willpath[0])
        if len(self.willpath) != 0:
            nextp = self.compute_distance()
            self.x_step = nextp['x_step']
            self.y_step = nextp['y_step']
        else:
            self.x_step = 0
            self.y_step = 0

    def _get_sites_key(self, xy):
        for k, v in self.sites.items():
            if xy == v:
                return k

    def set_car_msg(self, key, value):
        # redis_key: self.name
        # key :target,speed,status
        return self.con.hset(self.name, key, value)

    def get_car_msg(self, key):
        # redis_key: self.name
        # key : name,target,speed,status
        return self.con.hget(self.name, key)

    def get_realtime_msg(self, key):
        # redis_key: rediskey
        # key: position
        # rediskey = self.name + '_' + time.strftime('%Y%m%d-%H%M%S')
        pass

    def set_realtime_msg(self, key, value=None):
        # key: name,status,osition,
        rediskey = self.name + '_' + time.strftime('%Y%m%d-%H%M%S')
        self.con.hset(rediskey, 'target', str(self.target))
        self.con.hset(rediskey, 'name', self.name)
        self.con.hset(rediskey, 'position', str(self.position))
        self.con.hset(rediskey, 'status', self.status)
        self.con.hset(rediskey, 'id', self.id)
        self.con.hset(rediskey, key, value)

    def run(self):
        self.set_car_msg('status', 2)  # 运行状态
        while (1):
            print('willpath:', self.willpath)
            Tool.set_car_position(self.name, str(self.position))

            target = self.get_car_msg('target')
            status = self.get_car_msg('status')
            speed = self.get_car_msg('speed')
            targetxy = Tool.convert_xystr_xylist(target)
            if targetxy != self.target:
                self.change_target(targetxy)
            elif speed != str(self.speed):
                self.change_speed(speed)
            else:
                self.set_car_msg('position', str(self.position))
                if len(self.willpath) == 0:  # 完成工作
                    self.finished_work()
                elif self.position == self.sites[self.willpath[0]]:  # 切换nextp
                    self.switch_nextpoint()
            self._align_step()
            self.position[0] = self.position[0] + self.x_step
            self.position[1] = self.position[1] + self.y_step
            time.sleep(1)

    def work(self):
        # 到指定点去完成任务
        while (1):
            print('willpath:', self.willpath)
            Tool.set_car_position(self.name, str(self.position))

            target = self.con.hget(self.name, 'target')
            status = self.con.hget(self.name, 'status')
            targetxy = Tool.convert_xystr_xylist(target)
            if targetxy != self.target:
                self.change_target(targetxy)
            else:
                self.con.hset(self.name, 'position', str(self.position))
                if len(self.willpath) == 0:
                    self.x_step = 0
                    self.y_step = 0
                elif self.position == self.sites[self.willpath[0]]:  # 切换nextp
                    self.switch_nextpoint()
            self._align_step()
            self.position[0] = self.position[0] + self.x_step
            self.position[1] = self.position[1] + self.y_step
            time.sleep(1)

    def finished_work(self):
        self.status = '1'
        self.speed = 0
        self.y_step = 0
        self.y_step = 0
        self.set_car_msg('speed', str(self.speed))
        self.set_car_msg('status', self.status)  # 运行状态

    def loop(self):
        # 两点之间循环来回
        pass


if __name__ == '__main__':
    graph = {
        '1': ['2', '4', '5'],
        '2': ['1', '3'],
        '3': ['2', '5'],
        '4': ['1', '5'],
        '5': ['3', '4', '1']
    }
    sites = {
        '1': [100, 900],
        '2': [300, 900],
        '3': [300, 700],
        '4': [100, 700],
        '5': [200, 500]
    }
    car = Car('car1', [100, 900], [300, 700], sites, graph, 10)
    car.run()
    '''
    cars = []
    for item in config.cars:
        id = item['name']
        start = item['poistion']
        target = item['target']
        sites = item['sites']
        graph = item['graph']
        speed = item['speed']
        car = Car(id,start,target,sites,graph,speed)
        #car.run()
        t=threading.Thread(target=car.run,args=())
        cars.append(t)
        t.start()
    for t in cars:
        t.join()
    '''
