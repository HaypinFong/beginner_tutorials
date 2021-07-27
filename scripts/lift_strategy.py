#!/usr/bin/env python
#-*- coding: utf-8 -*-
import threading
from redis_wraper import redis_wraper   #在redis_wraper类内写死Redis服务的host与port
import time

'''
20210623fhp 
def lift_strategy(request):
'''
class CRobotPost:
    '''
    某一placeID下的所有机器人的当前呼梯任务的记录
    该信息由后端从机器人mqtt+url存档或算法由url存档，同一机器人同一时刻只能有一个formAtoB的呼梯请求，重复呼梯则覆盖，
    '''
    def __init__(self,placeID='HotelMihua',robotID='A',status='goto',fromFloor=1,toFloor=3,cur_liftID=1,candidate_lifts=[1,2,3],allocate_lift=2,arriveTime =1624607499.0, ts=1624607499.0):
        '''
        cur_liftID: 机器人近场环境下"1,F,'goto'"初始化呼梯请求的自期望电梯号
        allocate_lift: 云端调度分配给机器人的电梯号
        ts: 机器人呼梯post上报的时间戳
        '''
        self._placeID = placeID
        self._robotID = robotID
        self._status = status       #'goto','wait_outside','inside_failed','inside','getout_failed','getout'
        self._fromFloor = fromFloor
        self._toFloor = toFloor
        self._cur_liftID = cur_liftID     #回报'goto'时是初选电梯，回报'inside'时是实际所在电梯(与_allocate_liftID相同则矣，也可能不同)
        self._allocate_liftID = allocate_lift #之所以由机器人回报服务器分配给它的电梯，起到服务器确认机器人收到服务器分配电梯的作用
        self._candidate_liftIDs = candidate_lifts
        self._arriveTime = arriveTime
        self._ts = ts      #只当"goto"状态且allocate_lift = -1时的ts才是_orderedTime呼梯时间戳

    def writeRobotPost(self):
        '''
        数据库接口，将placeID的robotID的当前任务写入数据库后面查询用到，
        该robotID乘梯任务完成后就不从数据库删除了，而是当机器人回报'getout'后覆盖数据库，不会查询已经'getout'的RobotStatus，其他状态可能用到
        '''
        return
objRobotPost = CRobotPost(placeID ='HotelMihua',robotID ='A', fromFloor =2, toFloor =9, cur_liftID =1, candidate_lifts =[1,2,3], \
    allocate_lift =-1, arriveTime = 1624607499.0,ts =1624607499.0)
class CFloorStatus:
    '''
    楼层的状态，算法数据结构
    '''
    def __init__(self,floorID,carrying_robotIDs = [],ordered_robotID2time = {'A':1624800783.270423}):
        '''
        floorID:楼层号
        status:楼层状态：载客01"carrying"|不可达02"unreachable"(包括该层故障)|被预订03"ordered"|空闲04"leisure"
        robotID[]:如果载客，记录robotID[]，如果该台电梯有排队，第二台机器人以后的回执可能需要传递前面已经等候的robotID[]列表，让后面机器人知道自己排队的序号
                或者被预订的robotID[]
        '''
        self._floorID = floorID
        # self._status = status     #该楼层分配给的机器人编号，每部电梯的某一楼层某时刻只会分配给一台机器人，那这台机器人自然只有'ordered'或'carrying'状态，但当该层同层接力两台机器人乘梯任务时，会出现'A'机器人'carrying'而'B'机器人'ordered'
                                #但如果后期考虑两台机器人，那两台机器人可能状态不一样，比如其中一台已经入梯，但另一台入梯失败停留在'ordered'状态；所以应该分成_ordered_robotID[]与_carrying_robotID[]
        self._ordered_robotID2time = ordered_robotID2time     #把该层预订给的机器人编号数组[]
        self._carrying_robotIDs = carrying_robotIDs   #在该层已经在电梯内的机器人编号数组[]
        # self._ordered_times = ordered_times         #设置status='ordered'预订状态时的时刻，其他status时该字段为空，一段楼层整体被预订，则这段楼层的每一层的_orderedTime都是同一个。
        '''
        当使用电梯心跳的当前层和上下行状态更新_futureFloors[]，即弹出passed楼层后，如果某部电梯的当前层_status='ordered'且_robotID=['A']，且当前层就是'A'机器人任务的出发楼层，就是说电梯已经到出发楼层了，但还未收到A机器人入梯后的post状态上报给改成'carrying'
        此时可能是：
        1、机器人已经放弃了这部电梯的这批楼层，期望电梯应该上报"1,False"然后调度函数func将ordered的2号电梯给自信释放，但并没有及时上报，那安全起见此时func不该擅自猜测是1情况而释放
        2、也可能是机器人已经进去了2号电梯(期望发出"2,True,'inside'"的post状态上报然后调度函数func将ordered的2号电梯的所有ordered的且_robotID[]中含有'A'的楼层标记为'carrying'，后面不参与分配)，但并没有及时上报
        3、当前调度函数func是被'C'机器人呼梯的post请求触发的，'A'机器人稍后就会post上报"2,True,'inside'"，彼时当前楼层不变，仍然有机会进行'ordered'——>'carrying'的状态变更
        此时调度函数func不能做出任何猜测

        当使用电梯心跳的当前层和上下行状态更新_futureFloors[]后，如果某部电梯的当前层_status='ordered'且_robotID=['A']，且当前层已经不是'A'机器人任务的出发楼层(如果是单向行程分配，那就是出发-目的楼层之间的某层；如果是双向行程分配，那可能是出发-目的楼层之外的某层)
        所以已经passed出发楼层的判据就是当前层已经不是'A'机器人的出发楼层(placeID的objPlaceLifts的_robotPosts['A']的_fromFloor)
        此时可能是：
        1、期待机器人从出发楼层入梯后就发"2,T,'inside'"的post报文的(inside的就是"分配"的2号电梯，可能是自主决策的，此时调度要把2号梯的这些楼层被动地_carrying_robotID[].append('A'),_orderedTime从_robotPosts填充(也不重要)；
                                                                                    也可能是调度分配的，此时自然把2号梯的这些楼层主动地_ordered_robotID2time[].remove('A'),_carrying_robotIDs[].append('A'),_ts
        '''
    def __str__(self):
        return str(self._floorID)+"-"+self._status
    def serialize(self):
        return str(self)
    # def unserialize(self,_str):
    #     content = _str.split('-')
    #     self._floorID = int(content[0])
    #     self._status = content[1]
    def moveFromOrdered2Carrying(self,robotID):
        restr = ''
        if self._ordered_robotID2time.has_key(robotID):
            self._ordered_robotID2time.pop(robotID)
            restr +='ALREADY_IN_ORDERED-'
        try:
            self._carrying_robotIDs.index(robotID)  #已经有robotID了
            restr +='ALREADY_IN_CARRYING'
            return restr
        except ValueError as e:     #没有
            self._carrying_robotIDs.append(robotID)
            restr +='APPEND_INTO_CARRYING'
            return restr
    def add2ordered(self,robotID,ts):
        if self._ordered_robotID2time.has_key(robotID):
            print('floor %d had order to robotID %s, will update ordered-time! !'%(self._floorID,robotID))
        self._ordered_robotID2time[robotID] = ts

# def unserialize(_str):
#         content = _str.split('-')
#         _floorID = int(content[0])
#         _status = content[1]
#         return CFloorStatus(_floorID,_status)
LIFT_DIRECTION = {'Up':0x01, 'Down':0x02, 'Static':0x00}
LIFT_USABLE = {'Usable':0x01, 'Crash':0x00}
class CLiftStatus:
    '''
    电梯的心跳数据，后端数据库的数据结构
    from伟辽+伟辽的电梯心跳必须上传placeID和liftID信息
    curFloor:电梯当前所在楼层
    UpDown:电梯未来运行方向，2表示下行Down，0表示静止|未知(Static,不是停层)，1表示上行Up
    Usable:是否可用，停用00，可用01
    # lastFloor:电梯上一个所在楼层
    hangTime:在当前层停留时间，如果只是路过那就是0，如果是停留在该层那就30秒(是一个阈值)
    # SingleDouble:单双层，以及还有中间设备层不停的
    '''
    def __init__(self,placeID,liftID,curFloor,usable,upDown,hangTime,ts):
        self._placeID = placeID
        self._liftID = liftID
        self._curFloor = curFloor
        self._usable = usable
        self._upDown = upDown       #未来运行方向
        self._hangTime = hangTime
        self._ts = ts               #使用时间戳覆盖
        #"电梯的加速至均速时间+电梯均速"

def getLiftStatus(placeID, liftID):
    '''
    数据库接口，根据placeID和liftID查询某幢建筑某号电梯心跳给后端数据库的电梯状态
    '''
    objLiftStatus = CLiftStatus(placeID =placeID, liftID =liftID, curFloor =2, usable =1, upDown =2, hangTime =2.0)
    return objLiftStatus

class CPlaceConfig:
    '''
    数据库数据结构
    建筑配置参数，可用电梯序号列表[1,2,3]，以便禁用某部电梯，运维——>服务器数据库——>调度函数func
    1、根据CPlaceLifts实例的_createTime定时从数据库更新
    2、运维——>服务器数据库，运维——>服务器前端——>重新构造CPlaceLifts(placeID)并覆盖数据库
    '''
    def __init__(self,placeID='HotelMihua',liftIDs=[1,2,3]):
        self._placeID = placeID
        self._liftIDs = liftIDs
    
def getPlaceConfig(placeID):
    '''
    数据库接口，查询某幢placeID的可用电梯列表
    '''
    objPlaceConfig =CPlaceConfig(placeID =placeID, liftIDs =[1,2,3])
    return objPlaceConfig

class CLiftConfig:
    '''
    数据库数据结构
    电梯的配置，服务楼层
    运维——>服务器数据库，运维——>服务器前端——>重新构造CPlaceLifts(placeID)并覆盖数据库
    '''
    def __init__(self,placeID='HotelMihua',liftID=2,serveFloors=[1,3,5,7,9]):
        self._placeID = placeID
        self._liftID = liftID
        serveFloors = set(serveFloors)
        self._serveFloors = serveFloors.sort( (lambda x,y:-1 if x<y else 0 if x==y else 1) )
        self._span_time = {0:2.0, 1:2.0, 2:2.5, 3:3.0}  #_span_time[0]表示运维测量的某部电梯在使用环境下平均的停层时间，指电梯最初开门时刻到最终关门时刻期间人或机器人延迟关门或不干预的情况下平均的停层时间
                #举例：1楼关门————2楼开门————2楼关门————4楼开门，_span_time[1]表示电梯上|下行一个楼层高的用时，指电梯自前一层关门时刻到停在下一层开门时刻的用时，
                #           t(1)      t(0)      t(2)

def getLiftConfig(placeID, liftID):
    '''
    数据库接口，查询某幢placeID某号liftID电梯的服务楼层、运行速度
    '''
    objLiftConfig = CLiftConfig(placeID ='HotelMihua', liftID =2 serveFloors=[])
    return objLiftConfig

class CLiftFloorsQueue:
    '''
    算法数据结构
    单台电梯的楼层队列deque
    '''
    def __init__(self,placeID,liftID,bInitFromDB=True):
        '''
        placeID:电梯所在的placeID
        
        serveFloors:电梯服务楼层列表，这个信息反映在地图中，某部电梯出现在地图的哪些层表示这部电梯服务的楼层列表
                     20210624：确定在云迹云的Redis数据库中会给出
        每一幢placeID的所有电梯的楼层队列deque在创建、更新后要存储到Redis数据库，调度函数首先从数据库读取楼层队列到内存，
        然后读取电梯心跳给云迹云Redis的curFloor、upDown、usable、hangTime更新内存楼层队列(弹出已经经过的楼层)。
        然后使用该楼层队列进行调度决策，决策后调度电梯的每层楼层的载客|预订|空闲状态进行更新，最后将每撞placeID的所有电梯
        的楼层队列deque更新到Redis数据库
        '''
        self._placeID = placeID     #二级字段
        self._liftID = liftID       #三级字段
        # self._liftInfo = CLiftStatus(curFloor,usable,upDown,hangTime) 
        self._curFloor = -1
        self._usable = -1
        self._upDown  = -1
        self._hangTime = -1.0
        self._serveFloors = []
        self._span_time = {}
        self._futureFloors = []
        if bInitFromDB:
            self.initFromDB()
       
    def initFromDB(self):
        objLiftStatus = getLiftStatus(placeID =self._placeID, liftID =self._liftID)
        self._curFloor = objLiftStatus._curFloor
        self._usable = objLiftStatus._usable
        self._upDown = objLiftStatus._upDown       #未来运行方向
        self._hangTime = objLiftStatus._hangTime
        objLiftConfig = getLiftConfig(placeID =self._placeID, liftID =self._liftID)
        serveFloors = set(objLiftConfig._serveFloors)
        self._serveFloors = serveFloors.sort( (lambda x,y:-1 if x<y else 0 if x==y else 1) )
        self._span_time = objLiftConfig._span_time
        self._futureFloors = []     #CFloorStatus，该部电梯预估的楼层队列，维护使始终从当前楼层开始，包含至少两个底层
        # self._futureFloors.append(CFloorStatus(self._curFloor,'leisure',[]))
        # 根据服务楼层列表+当前层+上下行状态填充楼层队列
        if self._usable == LIFT_USABLE['Usable'] and self._upDown ==LIFT_DIRECTION['Down']:
            self.appendDown(self._curFloor,True,2)
        elif self._usable ==LIFT_USABLE['Usable'] and self._upDown ==LIFT_DIRECTION['Up']:
            self.appendUp(self._curFloor,True,2)
        else:   #电梯不可用或静止状态，暂不能预估楼层列表，只填充当前层
            self._futureFloors.append(CFloorStatus(floorID=self._curFloor,carrying_robotIDs=[], ordered_robotID2time={}))
        return
    
    def updateLiftFloorQueue(self):
        '''
        从数据库获取最新的电梯状态CLiftStatus更新_futureFloors[]楼层队列，并检查延长_futureFloors[]楼层队列
        '''
        objLiftStatus = getLiftStatus(placeID =self._placeID, liftID =self._liftID)
        self._curFloor = objLiftStatus._curFloor
        self._usable = objLiftStatus._usable
        self._upDown = objLiftStatus._upDown       #未来运行方向
        self._hangTime = objLiftStatus._hangTime
        # for iFloor in self._futureFloors:
        #     if iFloor._floorID == self._curFloor and self._upDown == LIFT_DIRECTION['Static']:
        
        indexCurFloor = 0   #电梯当前层在递增的self._serveFloors[]中的下标
        try:
            indexCurFloor = self._serveFloors.index(self._curFloor)
        except ValueError as e:
            print('[Error---curFloor %d of lift %d at place %s not in serveFloors %s'%(self._curFloor, self._liftID, self._placeID, self._serveFloors))

        #检查电梯心跳状态异常(上下行状态与当前楼层冲突)
        if indexCurFloor == 0 and self._upDown == LIFT_DIRECTION['Down']:
            # 前提，只当电梯抵达某楼层的瞬间发布电梯心跳状态，此时如果在底层则要么上行要么停止，如果在顶层则要么下行要么停止，不可能在底层还下行(self._serveFloors[indexCurFloor-1]将下标越界！)
            print('[Error---curFloor %d of lift %d at place %s could not go-down within serveFloors %s'%(self._curFloor, self._liftID, self._placeID, self._serveFloors))
        elif indexCurFloor == len(self._serveFloors)-1 and self._upDown == LIFT_DIRECTION['Up']:
            print('[Error---curFloor %d of lift %d at place %s could not go-up within serveFloors %s'%(self._curFloor, self._liftID, self._placeID, self._serveFloors))
                  
        # indexFloor = 0        # 电梯当前层+上下行状态在self._futureFloors]]中的下标
        for iFloorindex in range( len(self._futureFloors)-1 ):
            if self._upDown == LIFT_DIRECTION['Down'] and self._futureFloors[iFloorindex] == self._curFloor and self._futureFloors[iFloorindex+1] == self._serveFloors[indexCurFloor-1] and iFloorindex!= 0:    #Down
                # 楼层队列过期，弹出self._futureFloors[0-(iFloorindex-1)]之前的CFloorStatus元素
                icount = iFloorindex
                while icount > 0:
                    self._futureFloors.pop(0)
                    icount -= 1
                break
            elif self._upDown == LIFT_DIRECTION['Up'] and self._futureFloors[iFloorindex] == self._curFloor and self._futureFloors[iFloorindex+1] == self._serveFloors[indexCurFloor+1] and iFloorindex!= 0:    #Up
                # 楼层队列过期，弹出self._futureFloors[0-(iFloorindex-1)]之前的CFloorStatus元素
                icount = iFloorindex
                while icount > 0:
                    self._futureFloors.pop(0)
                    icount -= 1
                break
        if self._upDown == LIFT_DIRECTION['Up'] or self._upDown == LIFT_DIRECTION['Down'] and len(self._futureFloors)==1:
            ''' 
            20210629：对由'Static'变化为'Up'或'Down'，如果在'Static'所在层_futureFloors[]=[1]收到电梯心跳的'Up'或'Down'
            ，或者由于延迟在'Up'或'Down'后的next层收到电梯心跳，_futureFloors[]只会有一层。清空楼层队列后填充self._curFloor
            '''
            index = 0
            while index <len(self._futureFloors):
                self._futureFloors.pop()
            self._futureFloors.append(CFloorStatus(self._curFloor,carrying_robotIDs=[],ordered_robotID2time={}))
        if self._upDown == LIFT_DIRECTION['Static'] or self._usable == LIFT_USABLE['Crash']:
            # 清空楼层队列后填充self._curFloor
            index = 0
            while index <len(self._futureFloors):
                self._futureFloors.pop()
            self._futureFloors.append(CFloorStatus(self._curFloor,carrying_robotIDs=[],ordered_robotID2time={}))
        '''
        该函数由调度函数lift_strategy(placeID)调用，修改完再由lift_strategy(placeID)调用writePlaceLifts(self)写数据库
        '''
        self.expandFutureFloors(2)


    def getBottomCount(self):
        '''
        计算并返回队列中底层出现次数
        '''
        iCountBottom = 0
        # try:
        #     iStart = 0
        #     while True:
        #         index = self._futureFloors.index(self._serveFloors[0],iStart)     //sb
        #         iCountBottom +=1
        #         iStart = index+1
        # except ValueError as e:     #下标越界或没找到
        #     pass
        for iFloor in self._futureFloors:
            if iFloor._floorID == self._serveFloors[0]:
                iCountBottom +=1
        return iCountBottom


    def expandFutureFloors(self,numBottom):
        '''
        20210627：清空_futureFloors[]中[0-len-1]区间的_carrying_liftIDs[]，因为使用电梯心跳更新_futureFloors[]发生在
        'inside'报文填充_carrying_liftIDs[]之前，如果出现有机器人在"未来"'inside'某电梯，那一定是那台电梯'inside'之后失联，
        且期间没有其他机器人发送任何post报文pop掉'inside'的楼层，也就是历史记录，需要清空_carrying_liftIDs[]。以及很久之前
        的_ordered_liftIDs[]，同理，如果之前分配给'A'机器人2号梯，但'A'之后失联，且，不论'A'是否成功进入2号梯，期间再也没有
        其他机器人发送任何post报文，那当之后执行lift_strategy()首先读取电梯心跳更新_futureFloors[]时，要检测一下[0-len-1]
        区间的_ordered_liftIDs[]对应_ordered_times[]很久之前的'A'，将其移除。
        对2号梯的[1-2-3,,,,,,,8,9,10]的_futureFloors[]，在1-2-3时刻首次为'A'分配[8,9,10]行程后，'A'失联，期间没有其他
        机器人发送任何post报文从而触发lift_strategy()读取电梯心跳更新2号梯_futureFloors[]。然后在未来某次lift_strategy()
        读取电梯心跳更新2号梯_futureFloors[]时碰巧又落在1-2-3时刻，此时_ordered_liftIDs[8,9,10]对应_ordered_times[]
        1、距离now()挺近时，便是正常分配出去的，且此时查询_robotPosts[]应该有相同机器人'A'相同时刻的'goto'或'wait_outside'
            且_allocate_liftID == 2。一定是先有_robotPosts[]中_ts = 1624541408.0，后有_ordered_liftIDs['A']及
            _ordered_times[1624541408.0]。
            如果给'A'分配电梯后失联，_robotPosts[]、_ordered_liftIDs[]、_ordered_times[]期间都没有更新，且下次post
            响应读取电梯心跳更新_futureFloors[]又定位到1-2-3时刻。可以根据此次post的时间戳检查_robotPosts[]与
            _ordered_times[]的时间戳，如果间隔
        20210627：解决，详见笔记，需要触发lift_strategy()的_robotPosts._ts对比_ordered_times[]中的时间，当间隔大于
            T(bottom-top)x2时确认是由于之前对应_ordered_robotID2time[]失联未回报'inside'与'getout'且至本次触发的
            _robotPosts._ts期间再没有任何机器人发出任何post报文形成的"僵尸"数据。
        '''
        # 检查_futureFloors[]中_serveFloors[0]底层个数，不足两个周期就补充
        if self._upDown == LIFT_DIRECTION['Static'] or self._usable == LIFT_USABLE['Crash']:
            return
        
        iCountBottom = self.getBottomCount()

        if iCountBottom >=numBottom:
            return
        else:
            '''
            补充两个含Bottom底层的周期
            如果self._futureFloors[]只含一层(当前层)那就按self._upDown补充，比如从'Static'或'Crash'恢复'Up'或'Down'
            如果self._futureFloors[]含两层以上，那就按最后两层()的趋势进行补充
                也有想法是在卡电梯_curFloor与_UpDown后每pop()掉前面passed的一个楼层就补充到_futureFloors[]尾后，但由于
                _futureFloors[]初始化时就没有(也没必要)严格按照整数倍周期进行初始化，所以不保证头尾衔接，还是按尾巴趋势续尾
            '''
            indexLast = len(self._futureFloors)-1
            if len(self._futureFloors) ==1 and self._upDown == LIFT_DIRECTION['Up']:
                # 'Static'——>'Up'
                self.appendUp(self._curFloor,False,numBottom-iCountBottom)
            elif len(self._futureFloors) ==1 and self._upDown == LIFT_DIRECTION['Down']:
                # 'Static'——>'Down'
                self.appendDown(self._curFloor,False,numBottom-iCountBottom)
            elif len(self._futureFloors) >1 and self._futureFloors[indexLast]-self._futureFloors[indexLast-1] >0:   #'Up'
                self.appendUp(self._futureFloors[indexLast],False,numBottom-iCountBottom)
            elif len(self._futureFloors) >1 and self._futureFloors[indexLast]-self._futureFloors[indexLast-1] <0:   #'Down'
                self.appendDown(self._futureFloors[indexLast],False,numBottom-iCountBottom)
            else:
                print('[Debug---Exception 346')

    def appendUp(self,lastFloor,bwithCurFloor,numBottom=2):
        # 剩余周期
        indexFloor = 0
        try:
            indexFloor = self._serveFloors.index(lastFloor)
        except ValueError as e:
            print('[Error---curFloor %d of lift %d at place %s not in serveFloors %s'%(self._curFloor, self._liftID, self._placeID, self._serveFloors))
            return
        iFloorindex = indexFloor+1
        if bwithCurFloor:
            iFloorindex = indexFloor
        while iFloorindex < len(self._serveFloors)-1: #(当前层+1)-(顶-1)
            self._futureFloors.append(CFloorStatus(self._serveFloors[iFloorindex],carrying_robotIDs=[],ordered_robotID2time={}))
            iFloorindex +=1
        for i in range(numBottom):      #顶-底+1-底-(顶-1)——顶-底+1-底-(顶-1)，楼层队列增加两个底，
            iFloorindex = len(self._serveFloors)-1

            try:
                if self._serveFloors.index(self._futureFloors[len(self._futureFloors)-1]) == len(self._serveFloors)-1:
                    # 不希望电梯在顶层还心跳了'Up'，但还是避免一下
                    iFloorindex = len(self._serveFloors)-1-1
            except:
                pass
            
            while iFloorindex>0:
                self._futureFloors.append(CFloorStatus(floorID=self._serveFloors[iFloorindex],carrying_robotIDs=[], ordered_robotID2time={}))
                iFloorindex-=1
            iFloorindex = 0
            while iFloorindex < len(self._serveFloors)-1:
                self._futureFloors.append(CFloorStatus(floorID=self._serveFloors[iFloorindex],carrying_robotIDs=[], ordered_robotID2time={}))
                iFloorindex+=1
    
    def appendDown(self,lastFloor,bwithCurFloor,numBottom=2):
        # 剩余周期
        indexFloor = 0
        try:
            indexFloor = self._serveFloors.index(lastFloor)
        except ValueError as e:
            print('[Error---curFloor %d of lift %d at place %s not in serveFloors %s'%(self._curFloor, self._liftID, self._placeID, self._serveFloors))
            return
        iFloorindex = indexFloor-1
        if bwithCurFloor:
            iFloorindex = indexFloor
        while iFloorindex > 0:  #(当前层-1)-(底+1)
            self._futureFloors.append(CFloorStatus(self._serveFloors[iFloorindex],carrying_robotIDs=[],ordered_robotID2time={}))
            iFloorindex -=1
        for i in range(numBottom):      #底-顶-(顶-1)-底+1——底-顶-(顶-1)-底+1，楼层队列增加两个底，后面调度决策函数首先更新完楼层队列后检查如果队列中少于两个底就接着队列尾检测尾巴方向统一填充两个底
            iFloorindex = 0

            try:
                if self._serveFloors.index(self._futureFloors[len(self._futureFloors)-1]) == 0:
                    # 不希望电梯在底层还心跳了'Down'，但还是避免一下
                    iFloorindex = 1
            except:
                pass

            while iFloorindex < len(self._serveFloors):
                self._futureFloors.append(CFloorStatus(floorID=self._serveFloors[iFloorindex],carrying_robotIDs=[], ordered_robotID2time={}))
                iFloorindex+=1
            iFloorindex = len(self._serveFloors)-2
            while iFloorindex > 0:   #每次填充的最后一层都不触底
                self._futureFloors.append(CFloorStatus(floorID=self._serveFloors[iFloorindex],carrying_robotIDs=[], ordered_robotID2time={}))
                iFloorindex-=1


    def searchSchedule(self,objRobotPost =objRobotPost):
        objOption = COption(liftID =self._liftID, upDown =self._upDown)
        index =0
        while index <len(self._futureFloors):
            if self._floorID == objRobotPost._toFloor <0:
                objOption._indexTo = index
                # Back倒找出发楼层
                indexBack = index
                while indexBack >=0:
                    if self._floorID == objRobotPost._fromFloor:
                        objOption._indexFrom = indexBack
                        break
                    indexBack -=1
                # 检查该档期是否可用：
                bClear = True
                if self._futureFloors[objOption._indexFrom]._carrying_robotIDs.__len__() ==1 \
                    and self._futureFloors[objOption._indexFrom]._ordered_robotID2time.__len__() ==0 or \
                    self._futureFloors[objOption._indexFrom]._carrying_robotIDs.__len__() ==0 \
                    and self._futureFloors[objOption._indexFrom]._ordered_robotID2time.__len__() <=1:
                    pass
                else:
                    bClear = False
                indexCheck = objOption._indexFrom+1
                while indexCheck <objOption._indexTo:
                    if self._futureFloors[indexCheck]._ordered_robotID2time.__len__()>0 or self._futureFloors[indexCheck]._carrying_robotIDs.__len__()>0:
                        bClear = False
                        break
                if self._futureFloors[objOption._indexTo]._carrying_robotIDs.__len__() ==0 \
                    and self._futureFloors[objOption._indexTo]._ordered_robotID2time.__len__() <=1:
                    pass
                else:
                    bClear = False
                '''
                检查电梯是否赶得上，暂时要求电梯最快赶到出发楼层时刻要晚于机器人抵达出发楼层时刻，对电梯可能慢点从而机器人也允许慢点的偏实际情形，严格情形要求机器人较早抵达出发楼层，
                偏实际情形是电梯会慢点，相应机器人也允许慢点。现能计算出电梯最快、理论最慢抵达出发楼层所用时间，统计可得实际抵达出发楼层所用时间是最快时间的1.3倍，也就是有平均
                意义上的电梯抵达出发楼层的平均用时，后面可以用该平均用时约束机器人抵达出发楼层的准确用时。电梯最快到达出发楼层时刻+实际会慢的时间 >= 机器人抵达出发楼层时刻
                '''
                stopFlooorSet = set([])
                indexStop = 1
                while indexStop < objOption._indexFrom:
                    if self._futureFloors[indexStop]._carrying_robotIDs.__len__() >0 and self._futureFloors[indexStop-1]._carrying_robotIDs.__len__() >0\
                        and self._futureFloors[indexStop+1]._carrying_robotIDs.__len__() <=0:
                        stopFlooorSet.add(indexStop)
                    if self._futureFloors[indexStop]._ordered_robotID2time.__len__() >0:
                        '''
                        只在行程衔接处会ordered给两个机器人，所以理论上只对_ordered_robotID2time第一个robotID考察边界停层
                        '''
                        for iRobotID in self._futureFloors[indexStop]._ordered_robotID2time.keys():
                            if not self._futureFloors[indexStop-1]._ordered_robotID2time.has_key(iRobotID) and self._futureFloors[indexStop+1]._ordered_robotID2time.has_key(iRobotID)\
                                or self._futureFloors[indexStop-1]._ordered_robotID2time.has_key(iRobotID) and not self._futureFloors[indexStop+1]._ordered_robotID2time.has_key(iRobotID):
                                stopFlooorSet.add(indexStop)
                            break
                # 剔除objOption._indexFrom的停层
                stopFlooorSet.remove(objOption._indexFrom)
                objOption._arriveTime = time.time()
                stopFloorList = list(stopFlooorSet)
                stopFloorList.sort( (lambda x,y:-1 if x<y else 0 if x==y else 1) ) 
                if self._hangTime >2.0:     # 当前层停层，就不add到stopFloorSet了
                    objOption._arriveTime +=self._span_time[0]
                iLastStopFloor = 0
                for iStopFloor in stopFloorList:
                    objOption._arriveTime +=self._span_time[0]
                    objOption._arriveTime +=self._span_time[iStopFloor-iLastStopFloor]
                    iLastStopFloor = iStopFloor
                objOption._arriveTime +=self._span_time[objOption._indexTo-iLastStopFloor]
                if objOption._arriveTime < objRobotPost._arriveTime:    #机器人赶不上最快的电梯
                    bClear = False


                if bClear:
                    # 计算Cost，档期内楼层队列换向至多一次
                    objOption._carrying_route = abs(objOption._indexTo - objOption._indexFrom)
                    objOption._pickup_route_max = abs(objOption._indexFrom - 0)
                    indexFirstFrom = -1
                    indexFind = 0
                    while indexFind <=objOption._indexFrom:
                        if self._futureFloors[indexFind]._floorID == objRobotPost._fromFloor:
                            indexFirstFrom = indexFind
                            break
                        indexFind +=1
                    if indexFirstFrom != objOption._indexFrom:  # 有换向
                        objOption._pickup_route_min = indexFirstFrom
                    else:
                        objOption._pickup_route_min = abs(objOption._indexFrom - 0)
                    objOption.computeCost()
                    return objOption
            index +=1
        return None

    def searchSchedule2(self,objRobotPost =objRobotPost):
        objOption = self.searchSchedule(objRobotPost)
        if not objOption:
            # 当前_futureFloors[]楼层队列没找到，延长队列继续找，矮子里拔将军，至少找一部电梯，当然档期越后越不可靠
            self.expandFutureFloors(self.getBottomCount()+2)
            objOption = self.searchSchedule(objRobotPost)
            if objOption:
                return objOption
            else:
                return None
    
    def releaseOrdered(self,objRobotPost =objRobotPost):
        '''
        入梯失败，将分配的楼层档期释放
        '''
        indexFromFloor = -1
        indexToFloor = -1
        index = -1
        for iFloor in self._futureFloors:
            index +=1
            if iFloor._floorID == objRobotPost._fromFloor and indexFromFloor <0:
                # 可能分配的[3,2,1,2,3,4]从3->4，也可能分配[3,4]从3->4，需要释放的是第一个from_floor到第一个to_Floor
                indexFromFloor = index
            if iFloor._floorID == objRobotPost._toFloor and indexToFloor <0:
                indexToFloor = index
                break
        if indexFromFloor >0 and indexToFloor >0 and indexFromFloor <indexToFloor:
            bOrdered = True
            index = indexFromFloor
            while index <=indexToFloor:
                if not self._futureFloors[index]._ordered_robotID2time.has_key(objRobotPost._robotID):
                    bOrdered = False
                    break
            if bOrdered:
                index = indexFromFloor
                while index <=indexToFloor:
                    self._futureFloors[index]._ordered_robotID2time.pop(objRobotPost._robotID)
                    index +=1
                return True
        return False


objLiftFloorsQueue =CLiftFloorsQueue(placeID ='HotelMihua', liftID =2, bInitFromDB =False)
class CPlaceLifts:
    '''
    算法数据结构
    某幢placeID下的所有电梯的楼层队列，存储在CPlaceLifts
    CPlaceLifts:                  #[CPlaceLifts]，一个记录
        _placeID            'HotelMihua001'
        _createTime         1624541408.730357，上次读取可用电梯列表，每部电梯服务楼层列表
        _liftFloorsQueues[]:        #CLiftFloorsQueue[]
            _liftID         1
            _curFloor       3
            _upDown         "Up"
            _usable         0|1
            _hangTime       2s
            _serveFloors[]:
                [1,3,5,7,9]
            _span_time      {0:2.0, 1:2.0, 2:2.5, 3:3.0}
            _latest_
            _futureFloors[]:        #CFloorStatus[]
                [{'_floorID':3,'_carrying_robotIDs':[],'_ordered_robotID':['A':1624541408.0],'arrive_time_estimate':[1268888.0]},   #'_ordered_times'记录该层被分配时刻的时间，后面更新该表的最后一步是检查如果_ordered_time过期，那就释放
                {'_floorID':5,'_carrying_robotIDs':[],'_ordered_robotID':['A':1624541408.0],'arrive_time_estimate':[1268888.0]},
                {'_floorID':7,'_carrying_robotIDs':[],'_ordered_robotID':['A':1624541408.0,'B':1624541410.0],'arrive_time_estimate':[1268888.0,1268888.0]},
                {'_floorID':9,'_carrying_robotIDs':[],'_ordered_robotID':['B':1624541410.0],'arrive_time_estimate':[1268888.0]},
                {'_floorID':7,'_carrying_robotIDs':[],'_ordered_robotID':[],'arrive_time_estimate':[1268888.0]},
                {'_floorID':5,'_carrying_robotIDs':[],'_ordered_robotID':[],'arrive_time_estimate':[1268888.0]},
                {'_floorID':3,'_carrying_robotIDs':[],'_ordered_robotID':[],'arrive_time_estimate':[1268888.0]},
                {'_floorID':1,'_carrying_robotIDs':[],'_ordered_robotID':[],'arrive_time_estimate':[1268888.0]},
                {'_floorID':3,'_carrying_robotIDs':[],'_ordered_robotID':[],'arrive_time_estimate':[1268888.0]},
                {'_floorID':5,'_carrying_robotIDs':[],'_ordered_robotID':[],'arrive_time_estimate':[1268888.0]},
                {'_floorID':7,'_carrying_robotIDs':[],'_ordered_robotID':[],'arrive_time_estimate':[1268888.0]},
                {'_floorID':9,'_carrying_robotIDs':[],'_ordered_robotID':[],'arrive_time_estimate':[1268888.0]}
                ]
        _robotPosts[]:              #CRobotPost[]
            _robotID        'A' 'HQTYCO1SZ202001050060004'
            _status         'inside'
            _fromFloor      3
            _toFloor        5
            _cur_liftID    1
            _candidate_liftIDs  [1,2,3]         #机器人前往的电梯厅的电梯编号列表，from地图
            _allocate_liftID  2               #分配的电梯编号，from _candidate_liftIDs[]
            _ts             1624541408.0    #收到机器人呼梯post报文的服务器系统时间，用于新替换旧机器人'A'的呼梯任务 

    '''
    def __init__(self,placeID="HotelMihua",liftFloorsQueues=[], robotPosts=[] ):
        '''
        查询数据库中该placeID的CPlaceLifts若不存在、已过期，则读取数据库电梯列表、电梯服务楼层、电梯状态、机器人post报文进行创建、更新
        根据某幢placeID，从数据库获取1、每撞placeID的可用电梯列表；2、每部电梯的服务楼层列表；3、每部电梯心跳的状态
        建立该幢placeID下的所有电梯的楼层队列CPlaceLifts
        该函数用在1、首次建立CPlaceLifts，2、CPlaceLifts实例的_createTime超过有效期后更新所有电梯的服务楼层列表并重新填充楼层队列

        每幢placeID的电梯序号(对应地图的电梯编号)列表
        CPlaceLifts:
            _placeID:
            _liftsID[]: [1,2,3,4]

        每部电梯的服务楼层列表
        CLiftServeFloors:
            _placeID
            _liftID
            _serveFloors[]:
                [1,3,5,7,9]
        
        每部电梯的心跳状态
        CLiftStatus:
            _placeID
            _liftID
            _curFloor
            _upDown
            _usable
            _hangTime
        
        
        LiftFloorsQueue = []
        1、从数据库查询placeID的电梯列表_liftsID[]
        for iLift in _liftsID[]:
            2、从数据库查询iLift号电梯的楼层服务列表CLiftServeFloors: _serveFloors
            3、从数据库查询iLift号电梯的心跳状态CLiftStatus: 
            LiftFloorsQueue[iLift] = CLiftFloorsQueue(placeID,liftID,curFloor,upDown,usable,hangTime,serveFloors)   #根据服务楼层列表+当前层+上下行状态填充楼层队列
        objCPlaceLifts = CPlaceLifts(placeID,LiftFloorsQueue,time.time())
        return objCPlaceLifts
        存数据库
        '''
        liftFloorsQueues.append(objLiftFloorsQueue)
        robotPosts.append(objRobotPost)
        self._placeID = placeID
        self._liftFloorsQueues = liftFloorsQueues        #CLiftFloorsQueue列表
        self._createTime = time.time()    #该幢placeID的所有电梯的楼层队列的构建时间，构建时需要从数据库中获取placeID-liftID的_serveFloors[]，
            #电梯的服务楼层列表配置可能改动，记录上次读取服务楼层列表时间，间隔一定时间后重新读取每部电梯的_serveFloors，并重生成_futureFloors[]
        self._robotPosts = robotPosts   #CRobotPost列表
    
    def updatePlaceLifts_FromLiftStatus(self):
        '''
        根据某幢placdID，从数据库获取每部电梯的心跳状态
        更新该幢placeID下的所有电梯的楼层队列CPlaceLifts
        该函数用在1、调度策略函数入口日常使用最新的所有电梯的心跳状态更新楼层队列

        每部电梯的心跳状态
        CLiftStatus:
            _curFloor
            _usable
            _upDown
            _hangTime  
                
        '''
        for iLiftFloorsQueue in self._liftFloorsQueues:
            '''1、从数据库查询iLiftFloorsQueue._liftID号电梯的心跳状态CLiftStatus实例objLiftStatus:_curFloor,_upDown
            填充到iLiftFloorsQueue._curFloor, iLiftFloorsQueue._usable, iLiftFloorsQueue._upDown, iLiftFloorsQueue._hangTime
            并使用_curFloor与_upDown维护_futureFloors'''
            iLiftFloorsQueue.updateLiftFloorQueue()
            
    def writePlaceLifts(self):
        '''
        写数据库
        '''
def readPlaceLifts(placeID):
    '''
    根据placeID从数据库读，返回实例
    '''
    objPlaceLifts = CPlaceLifts(placeID="HotelMihua",liftsFloorsQueue=[],robotsPost=[])
    #根据placeID读数据库并赋值objPlaceLifts
    return objPlaceLifts




def lift_strategy(objRobotPost=objRobotPost):      #"1,F,'goto',[1,2,3],arrive_time=16000000.0"
    '''
    20210626:本调度函数对同一幢placeID的不管是"goto"呼梯请求还是"inside"状态回报都必须严格按照post的时间戳加入消息队列排队调用
    电梯决策接口，针对某placeID下的电梯、机器人
    电梯记录：
    引发决策的事件是最真实的，从数据库读取数据结构后首先执行由事件导致的更新，然后才从数据库的电梯信息、机器人信息更新数据结构

    机器人'A'的第一次"1,F,"goto",[1,2,3]"呼梯post报文的调度函数中已经决策出了2号电梯并返回给机器人2，2号电梯如果是[1,2,3]电梯列表的最优解那肯定是2好电梯_futureFloors[]队列的最优解
    机器人'A'的第二次"2,T,"goto",[1,2,3]"状态回报post报文的调度函数，考察[1,3]电梯各自的最优解对比2号电梯的最优解，如果优于2号电梯(比如1、3号电梯上次被其他机器人预订的楼层被释放了从而比2号电梯解更优)，那就返回给机器人1号电梯

    给与预订楼层的情况：1、如果电梯以最快速度到达出发楼层(当前楼层——>顶(底)层——>出发楼层或直接当前楼层——>出发楼层，中间不停层)的时刻晚于机器人抵达出发楼层[3][8]点位的时刻，也就是机器人能等到电梯
        ，那电梯慢点的话也能被机器人等到，可以allocate；如果早于机器人抵达出发楼层时刻，那电梯不应该等机器人，电梯只常规开关门3秒后离开，这是可能发生的，但仍要给allocate并呼梯，赶得上则已，赶不上
        就会在机器人下次"2,T,'goto',[1,2,3]"时(还在前往分配的2号电梯的路上)更新楼层状态后检查到，奥，我给你分配了2号电梯但并没有听你报告"2,T,'inside',[1,2,3]"(改电梯_futureFloors[]楼层
        状态)且此时2号电梯已经pass你机器人的出发楼层了，说明给你机器人分配的电梯你没坐上，那就释放2号电梯当前层以及后面给你机器人分配的楼层，重新给机器人查找[1,2,3]电梯的档期进行allocate；
    2、如果电梯以最慢的速度到达出发楼层(当前楼层——>层层停——>顶(底)层——>层层停——>出发楼层或当前楼层——>层层停——>出发楼层)的时刻早于机器人抵达出发楼层[3][8]点位的时刻，说明机器人太慢
        ，那电梯不能等机器人，不予以allocate，不呼梯；如果晚于机器人抵达出发楼层时刻，那机器人能等就等好了，可以allocate，但这是电梯最慢的情况，如果再快一点则电梯可能就比机器人更早
        到达出发楼层，此时赶得上则已，赶不上(电梯白白停层)就会在机器人下次"2,T,'goto',[1,2,3]"时(还在前往分配的2号电梯的路上)更新楼层状态后检查到，奥，我给你分配了2号电梯但并没有听你报告
        "2,T,'inside',[1,2,3]"(改电梯_futureFloors[]楼层状态)且此时2号电梯已经pass你机器人的出发楼层了，说明给你机器人分配的电梯你没坐上，那就释放2号电梯当前层以及后面给你机器人分配的楼层，
        重新给机器人查找[1,2,3]电梯的档期进行allocate；
    用电梯最快到达出发楼层的时间考察最够快的机器人，慢的机器人如果用最慢的电梯时间来考察如果比电梯最慢要快些从而给与点亮楼层，那可能电梯实际挺快到达出发楼层从而开门白等机器人还等不着。
    用电梯最快到达出发楼层的时间考察最够快的机器人，电梯实际上会慢，从而机器人一定会等到电梯。
    对两部电梯的_futureFloors[]队列，尽管是把所有楼层都列在其中，但电梯可能停在那些楼层，也可能经过那些楼层，当前时刻人为

    

    1、从数据库读取placeID的CPlaceLifts

    
    2、从数据库获取电梯心跳更新电梯楼层队列(销号)

    3、销完号后检查楼层队列的"底"层个数，不足则填充

    3.5、检查所有电梯的楼层队列中_ordered_robotID2time[]与本次objRobotPost._ts间隔大于T(bottom-top)x2的，判断为对应_ordered_robotID2time[]失联未报'inside'与'getout'
        触发lift_strategy()更新楼层队列，且至本次objRobotPost._ts期间未有任何机器人发出任何Post报文，致使本次post事件触发lift_strategy()后使用电梯心跳的
        _curFloor与_upDown卡_futureFloors[]卡在前次分配电梯后又失联的机器人在lift_strategy()中保存下的_futureFloors[]中对应'goto'及之后、'inside'之前
        ，从而检测到旧的_ordered_robotID2time[]及_ordered_times[]

    4、首先根据机器人post报文的"inside"状态对楼梯队列进行2-1：如果robotID存在于楼层队列的_ordered_robotID2time[]字典，那将该robotID从_ordered_robotID2time[]移到_carrying_robotID[]；
                                                  2-2：如果robotID不在楼层队列的_ordered_robotID2time[]字典，乱入的机器人，仍要将robotID填到_carrying_robotID[]；
        

    5、电梯决策，避开_ordered_robotID2time[]与_carrying_robotID2time[]

    6、分配电梯，补_ordered_robotID2time[]，后面该电梯该楼层_ordered_robotID2time[]不为空的就不再参与分配
    '''
    # 1
    objPlaceLifts = readPlaceLifts(placeID)
    
    time_span = 0.0
    for iLift in objPlaceLifts._liftFloorsQueues:
        # 2+3
        iLift.updateLiftFloorQueue()
        # 3.5
        bottomFloor = iLift._serveFloors[0]
        topFloor = iLift._serveFloors(len(iLift._serveFloors)-1)
        inFloor = -1        #Debug
        secondFloor = -1    #Debug 对6-3，可能6-10-3，可能6-5-3，也可能对6-5直接6-5
        outFloor = -1       #Debug
        robotIDs_offline = []#Debug
        floors_offline = []
        for iFloor in iLift._futureFloors:
            for robotID,ts in iFloor._ordered_robotID2time.items():
                time_span = objRobotPost._ts - ts
                if  time_span >= iLift._span_time(topFloor-bottomFloor)*2:  # 时间不好预估，暂时不弹出只警告
                    floors_offline.append(iFloor._floorID)
                    robotIDs_offline.append(robotID)
                    if inFloor < 0:
                        inFloor = iFloor._floorID           #记录
                    if inFloor > 0 and secondFloor < 0:
                        secondFloor = iFloor._floorID       #记录
                    outFloor = iFloor._floorID              #记录(可能与secondFloor同)
                    # iFloor._ordered_robotID2time.pop(robotID)
                    break
            formstr = "[Warning---check out liftID %d of placeID %s allocated floors:[%d-%d-%d] to robotID %s %fs ago, \
            and still not notified \"inside\" or \"getout\", confirm offline, will pop robotID %s from the _futureFloors[]! ! !]"
            print(formstr%(iLift._liftID,objPlaceLifts._placeID,inFloor,secondFloor,outFloor,robotIDs_offline,time_span,robotIDs_offline))
    
    # 4
    if objRobotPost._status == 'inside':
        for iLift in objPlaceLifts._liftFloorsQueues:
            if iLift._liftID == objRobotPost._cur_liftID:   #20210630：可能_cur_liftID与_allocate_liftID不同，那要把_allocate_liftID释放
                '''
                考虑到电梯心跳不及时的情况，这里楼层队列_futureFloors[0]可能不会刚好是objRobotPost._fromFloor，而是objRobotPost._fromFloor前后若干层，
                所以这里要在_futureFloors[]中查找objRobotPost._fromFloor
                在解决机器人提前入梯问题[6,7,8(提前入梯),9,10,9,8(计划入梯),7,6(计划出梯)]之前，对机器人post的'8,inside,6'，可能是计划入梯也可能是提前入梯
                ，此时carrying填充安全起见，保守起见从_futureFloors[]队列第一个出发楼层到第一个目的楼层都填充；一旦解决机器人提前入梯，就可以放心填充第一个目的
                楼层到反向第一个出发楼层
                提前入梯与计划入梯共同特征是_futureFloors[]中目的楼层之前至少一个出发楼层
                如果是出梯失败后的'inside'通知，那错过的、历史的目的楼层到未来的目的楼层之前就不会有出发楼层了，期待在出梯失败的目的楼层发'out_failed'通知，然后
                会将当前楼层(目的楼层)到下一个未来目的楼层填充占位。如果'out_failed'未上报，就需要之后的'inside'触发将楼层队列中第一个目的
                楼层之前的所有楼层填充占位
                '''
                
                indexFromFloor = -1
                indexToFloor = -1   # 总是要找到出发楼层和目的楼层
                index = -1
                # 首先判断是否是出梯失败后发布的'inside'，或者是机器人纯粹地乱入，_futureFloors[to_floor]及之前都是未经分配的
                for iFloor in iLift._futureFloors:
                    index +=1
                    if iFloor._floorID == objRobotPost._fromFloor:
                        indexFromFloor = index
                    if iFloor._floorID == objRobotPost._toFloor:
                        indexToFloor = index
                        if indexFromFloor <0 and not iLift._futureFloors[indexToFloor]._ordered_robotID2time.has_key(objRobotPost._robotID):
                            '''
                            _futureFloors[]在目的楼层之前没有出发楼层，只能换向后出梯，确认是'out_failed'出梯失败后上报的'inside'，期望'out_failed'的
                            目的楼层-目的楼层填充占位，这里保险起见再次补充操作一下
                            '''
                            index = 0
                            while index <=indexToFloor:
                                res = iLift._futureFloors[index].moveFromOrdered2Carrying(objRobotPost._robotID)
                                index +=1
                                if res.find('APPEND_INTO_CARRYING') >=0:
                                    prinstr = "[Warning---robotID %s in placeID %s report \"inside\" but find no from_floor in _futureFloors[] \
                                        before to_floor, so confirm there must was a \"out_failed\" before, and it\'s expected that former \
                                        \"out_failed\" report should had turned [to_floor to next to_floor] in _futureFloors[] to carrying \
                                        status, but there wasn\'t!!! LUCKLY THIS \"INSIDE\" REPORT WILL DO THIS FOR \"OUT_FAILED\"! ! ! !"
                                    print(prinstr%(objRobotPost._robotID,objPlaceLifts._placeID))
                            return 0
                        break
                
                indexFromFloor = -1
                indexFromFloorSecond = -1
                indexToFloor = -1
                index = -1
                bRobotMayInLiftEarly = True     # 机器人是否有可能提前入梯，配置参数！【【【【【【【【【【配置】】】】】】】】】】
                for iFloor in iLift._futureFloors:
                    index +=1
                    if bRobotWillInLiftEarly:
                        # Way1：机器人可能提前入梯：
                        if iFloor._floorID == objRobotPost._toFloor and indexFromFloor >0:
                            indexToFloor = index
                            break
                        if iFloor._floorID == objRobotPost._fromFloor and indexFromFloor <0:
                            indexFromFloor = index
                        if iFloor._floorID == objRobotPost._fromFloor and indexFromFloor >0 and indexFromFloorSecond <0:
                            indexFromFloorSecond = index
                    else:
                        # Way2：机器人不会提前入梯：
                        if iFloor._floorID == objRobotPost._toFloor:
                            indexToFloor = index
                            while index >=0:
                                if iLift._futureFloors[index]._floorID == objRobotPost._fromFloor:
                                    indexFromFloor == index
                                    indexFromFloorSecond = indexFromFloor
                                    break
                                index -=1
                            break
                bOrdered = True     #
                index = indexToFloor
                while index >= indexFromFloorSecond:
                    if not iLift._futureFloors[index]._ordered_robotID2time.has_key(objRobotPost._robotID):
                        bOrdered = False
                        break
                    index -=1
                if indexFromFloor >0 and indexToFloor >0 and indexFromFloor < indexToFloor and bOrdered:
                    index = indexFromFloor  # 若可能提前入梯，则保守地全部占位
                    while index <= indexToFloor:
                        # 入梯填充
                        iLift._futureFloors[index].moveFromOrdered2Carrying(objRobotPost._robotID)
                        index +=1
                    # return 0
                # break
            if objRobotPost._allocate_liftID != objRobotPost._cur_liftID and iLift._liftID == objRobotPost._allocate_liftID:
                '''
                墨菲定律，机器人入梯不是分配的电梯，上面把入梯占位了，此处把分配的电梯释放
                '''
                for iLift in objPlaceLifts._liftFloorsQueues:
                    if iLift._liftID == objRobotPost._allocate_liftID:
                        if iLift.releaseOrdered(objRobotPost=objRobotPost):
                            # return 0
                        break
        # print('[Debug---Exception 773')
        return 0
    elif objRobotPost._status == 'out_failed':
        for iLift in objPlaceLifts._liftFloorsQueues:
            if iLift._liftID == objRobotPost._cur_liftID:
                # 出梯失败，将_futureFloors[]中[当前楼层(目的楼层)到下一个目的楼层]标记占位
                indexFirstToFloor = -1
                indexSecondToFloor = -1
                index = -1
                for iFloor in iLift._futureFloors:
                    index +=1
                    if iFloor._floorID == objRobotPost._toFloor and indexFirstToFloor <0:
                        indexFirstToFloor = index
                    if iFloor._floorID == objRobotPost._toFloor and indexFirstToFloor >0 and indexSecondToFloor <0:
                        indexSecondToFloor = index
                        break
                if indexFirstToFloor < indexSecondToFloor and indexSecondToFloor - indexFirstToFloor <= (len(iLift._serveFloors) -1)*2:
                    index = indexFirstToFloor
                    while index <=indexSecondToFloor:
                        iLift._futureFloors[index].moveFromOrdered2Carrying(objRobotPost._robotID)
                        index +=1
                    return 0
                break
        print('[Debug---Exception 798')
        return 1
    elif objRobotPost._status == 'in_failed':
        for iLift in objPlaceLifts._liftFloorsQueues:
            if iLift._liftID == objRobotPost._cur_liftID:
                if iLift.releaseOrdered(objRobotPost=objRobotPost):
                    return 0
                break
            else:
                continue
        print('[Debug---Exception 833')
        return 1
    elif objRobotPost._status == 'goto-ask' and allocate_lift <0:
        # 分配电梯
        options = []
        for iLift in objPlaceLifts._liftFloorsQueues:
            try:
                objRobotPost._candidate_liftIDs.index(iLift._liftID)
            except:
                continue
            if iLift._usable == LIFT_USABLE['Usable'] and iLift._upDown == 'Up' or iLift._upDown == 'Down':
                objOption = iLift.searchSchedule2(objRobotPost=objRobotPost)
                if objOption:
                    options.append(objOption)
                else:
                    print("[Error---liftID %s of placeID %s searchSchedule for from %d to %d failed THOUGH EXPAND FUTUREFLOORS ! ! !"\
                        %(iLift._liftID,objRobotPost._placeID,objRobotPost._fromFloor,objRobotPost._toFloor))
                    continue    #放弃查找，考察下个电梯
            elif iLift._usable == LIFT_USABLE['Usable'] and iLift._upDown == 'Static':
                if objRobotPost._fromFloor > iLift._curFloor or objRobotPost._fromFloor == iLift._curFloor and objRobotPost._toFloor > iLift._curFloor:
                    # should 'Up'
                    static2upFloorsQueue = CLiftFloorsQueue(iLift._placeID,iLift._liftID,bInitFromDB=False)
                    static2upFloorsQueue._upDown = LIFT_DIRECTION['Up']
                    static2upFloorsQueue.appendUp(lastFloor =iLift._curFloor, bwithCurFloor =True, numBottom=2)
                    objOption = static2upFloorsQueue.searchSchedule2(objRobotPost=objRobotPost)
                    if objOption:
                        options.append(objOption)
                    else:
                        print("[Error---liftID %s of placeID %s searchSchedule for from %d to %d failed THOUGH EXPAND FUTUREFLOORS ! ! !"\
                            %(static2upFloorsQueue._liftID,objRobotPost._placeID,objRobotPost._fromFloor,objRobotPost._toFloor))
                        continue    #放弃查找，考察下个电梯
                elif objRobotPost._fromFloor < iLift._curFloor or objRobotPost._fromFloor == iLift._curFloor and objRobotPost._toFloor < iLift._curFloor:
                    # should 'Down'
                    static2upFloorsQueue = CLiftFloorsQueue(iLift._placeID,iLift._liftID,bInitFromDB=False)
                    static2upFloorsQueue._upDown = LIFT_DIRECTION['Down']
                    static2upFloorsQueue.appendDown(lastFloor =iLift._curFloor, bwithCurFloor =True, numBottom=2)
                    objOption = static2upFloorsQueue.searchSchedule2(objRobotPost=objRobotPost)
                    if objOption:
                        options.append(objOption)
                    else:
                        print("[Error---liftID %s of placeID %s searchSchedule for from %d to %d failed THOUGH EXPAND FUTUREFLOORS ! ! !"\
                            %(static2upFloorsQueue._liftID,objRobotPost._placeID,objRobotPost._fromFloor,objRobotPost._toFloor))
                        continue    #放弃查找，考察下个电梯
            elif iLift._usable == LIFT_USABLE['Crash']:
                print("[Debug---liftID %s of placeID %s Crashed, Notify the OPS please! ! !")
            else:
                print('[Debug---Exception 875')
                continue
        if len(options) <=0:
            print('[Error---find not one from all candidate lifts %s ! SOME THING ERROR ! ! ! !'%(objRobotPost._candidate_liftIDs,))
            return 1
        minCost = options[0]._cost
        optionMinCost = options[0]
        indexOption = 1
        while indexOption <len(options):
            if options[indexOption]._cost< minCost:
                optionMinCost = options[indexOption]
        # 填充最优电梯的_futureFloors[]
        for iLift in objPlaceLifts._liftFloorsQueues:
            if iLift._liftID == optionMinCost._liftID and iLift._upDown == LIFT_DIRECTION['Up'] or iLift._upDown == LIFT_DIRECTION['Down']:
                indexFloor = optionMinCost._indexFrom
                while indexFloor <=optionMinCost._indexTo:
                    iLift._futureFloors[indexFloor]._ordered_robotID2time[objRobotPost._robotID] = time.time()
            if iLift._liftID == optionMinCost._liftID and iLift._upDown == LIFT_DIRECTION['Static']:
                iLift._upDown = optionMinCost._upDown
                if iLift._upDown == LIFT_DIRECTION['Up']:
                    iLift.appendUp(lastFloor =iLift._curFloor, bwithCurFloor =True, numBottom=2)
                elif iLift._upDown == LIFT_DIRECTION['Down']:
                    iLift.appendDown(lastFloor =iLift._curFloor, bwithCurFloor =True, numBottom=2)
                
                indexFloor = optionMinCost._indexFrom
                while indexFloor <=optionMinCost._indexTo:
                    iLift._futureFloors[indexFloor]._ordered_robotID2time[objRobotPost._robotID] = time.time()
        return optionMinCost._liftID

    elif objRobotPost._status == 'goto-ask' and allocate_lift >0 and cur_liftID != allocate_lift:
        '''
        有分配电梯但是机器人不坐？收回allocate_lift电梯分配给该robotID的档期，然后重新分配电梯？
        '''
    elif objRobotPost._status == 'goto-ready':
        # 避免提前入梯
    else:
        print('[Error---unvalid \"_status\" %s field!'%(objRobotPost._status))
        return 1

class COption:
    '''
    描述策略选项的类
    选择liftID号电梯，'Up''Down'上下行状态(运行中电梯该字段是确定的，主要是对Static电梯判断出方向后记录)
    '''
    def __init__(self,liftID =2,upDown = 'Static2Up'):
        self._liftID = liftID
        self._upDown = upDown
        self._pickup_route_min = 0.0    # 至少的接机行程
        self._pickup_route_max = 0.0    # 最多的接机行程
        self._discount = 0.7            # 如果载客行程有换向，由于换向位置受人为影响，现对最多减最少接机行程差值乘一个折减系数，[0,1]之间的一个系数，可以从数据库读取
        self._cost = -1.0
        self._carrying_route = 0.0  
        self._indexFrom = -1
        self._indexTo = -1          # 存储候选的每部电梯的最优(接机行程+载客行程和最小)可用_futureFloors[]档期下标
        self._arriveTime = 1624607499.0
        
    def computeCost(self):
        self._cost = self._carrying_route + self._pickup_route_min + (self._pickup_route_max - self._pickup_route_min)*self._discount

if __name__ == '__main__':
    lift_strategy()