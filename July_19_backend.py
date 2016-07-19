import copy
import math

class SearchNode:
    """
    # SPECIFIC EDITS FOR THIS SEARCH TYPE
    # LOCATED IN (inPath)
    #
    """
    def __init__(self, action, state, parent, actionCost):
        self.state = state
        self.action = action
        self.parent = parent
        if self.parent:
            self.cost = self.parent.cost + actionCost
        else:
            self.cost = actionCost

    def path(self):
        if self.parent == None:
            return [(self.action, self.state)]
        else:
            return self.parent.path() + [(self.action, self.state)]

    def inPath(self, s):
        for idx,thing in enumerate(s[0]):
            if thing.qDist != self.state[0][idx].qDist:
                if self.parent == None:
                    return False
                else:
                    return self.parent.inPath(s)
        return True

    def currentDist(self):
        return tuple([ tuple([x.qDist[y.name] for x in self.state[0]]) for y in self.state[1]])

class Stack:
    def __init__(self):
        self.data = []
    def push(self, item):
        self.data.append(item)
    def pop(self):
        return self.data.pop()
    def isEmpty(self):
        return self.data is []

class Queue:
    def __init__(self):
        self.data = []
    def push(self, item):
        self.data.append(item)
    def pop(self):
        return self.data.pop(0)
    def isEmpty(self):
        return self.data is []

class PQ:
    def __init__(self):
        self.data = []
    def push(self, item, cost):
        self.data.append((cost, item))
    def pop(self):
        index = self.data.index(min(self.data, key = lambda (c, x): c))
        return self.data.pop(index)[1] # just return the data item
    def isEmpty(self):
        return self.data is []

def CostSearch(initialState, goalTest, actions, successor, heuristic):
    winner = [[],[]]
    startNode = SearchNode(None, initialState, None, 0)
    if goalTest(initialState):
        return startNode.path()
    agenda = PQ()
    agenda.push(startNode,0)
    expanded = {}
#    while not agenda.isEmpty():
    thing = range(0,200000,100)
    for i in range(200000):
        n = agenda.pop() 
        if not n.currentDist() in expanded:
            expanded[n.currentDist()] = True
            if i in thing:
                print 'we are iteration', i
            if goalTest(n.state):
                print'WE MADE IT'
                for x in n.state[0]:
                    winner[0].append( (x.columnIndex, x.vesselRow, sum( x.qDist.itervalues() )) )
                for x in n.state[1]:
                    winner[1].append( (x.rowIndex, tuple(x.physicalPortsVisited)) )
                print 'total cost is', n.cost
                return winner
            for  a in actions(n.state):
                (newS, cost) = successor(n.state, a)
                newN = SearchNode(a, newS, n, cost)
                if not newN.currentDist() in expanded:
                    agenda.push(newN, newN.cost + heuristic(newS))

    return None


class Vessel(object):
    """Represents a Vessel.
    Args:
        vesQty (float): Capacity for cargo in kilotons.
        maxDraft (float): Maximum draft in meters.
        name (str): Name.

        inUse (float): amount of vesQty already assigned
        numPorts (int): number of ports delivering to, important for addPortRate


        note!!! subtract addPortRate from excel comboRate!!!
    """
    def __init__(self, vesQty, maxDraft, laycanDates, name, wcRate, ecRate, comboRate, addPortRate, maxPorts):
        self.vesQty = vesQty
        self.maxDraft = maxDraft
        self.name = name
        self.wcRate = wcRate
        self.ecRate = ecRate
        self.comboRate = comboRate
        self.addPortRate = addPortRate
        self.maxPorts = maxPorts
        self.laycanDates = laycanDates

        self.rowIndex = 0
        self.inUse = 0
        self.ec = 0
        self.wc = 0
        self.currentCost = 0
        self.clientDist = {}
        self.fullClientDist = {}
        self.physicalPortsVisited = []
        self.firstPortArrivalDates = []
        self.secondPortArrivalDates = []
        self.visitable = {}
        self.clientsVisited = []

        self.firstPortDict = {}
        self.secondPortDict = {}

    def isFull(self):
        if self.inUse == self.vesQty:
            return True
        else:
            return False

    def currentDraft(self, clientName):
        if not len(self.clientDist):
            return self.maxDraft
        else:
            previouslyDischarged = 0
            for client in self.clientsVisited:
                if client == clientName:
                    break
                previouslyDischarged += self.clientDist[client]
            return (.2+.8*(self.vesQty-previouslyDischarged)/self.vesQty)*self.maxDraft

    def canVisit(self, client):
        ''' Currently only testing for travelTime '''
        if (self.ec + self.wc) == 2 and (not client.qDist[self.name]):
            oldClient = self.physicalPortsVisited[1]
            if (self.clientsVisited[0], self.clientsVisited[1], client.name) in self.visitable:
                return self.visitable[(self.clientsVisited[0], self.clientsVisited[1], client.name)]
            #print 'testing', (self.clientsVisited[0], self.clientsVisited[1], client.name)
            for leaveSecondPort in self.secondPortDict[(self.clientsVisited[0], self.clientsVisited[1])]:
                if leaveSecondPort + client.travelTime(oldClient,True) + self.inUse/9.6 <= client.arrivalWindow[1] +0.5:
                    if '_' in client.dischargePort.name:
                        #+1,-1
                        if leaveSecondPort + client.travelTime(oldClient,True) + self.inUse/9.6 >= client.arrivalWindow[0] - 0.5:
                            self.visitable[(self.clientsVisited[0], self.clientsVisited[1], client.name)] = True
                            return True
                        else:
                            continue
                    self.visitable[(self.clientsVisited[0], self.clientsVisited[1], client.name)] = True
                    return True
            #print 'poop'
            self.visitable[(self.clientsVisited[0], self.clientsVisited[1], client.name)] = False  
            return False

        if not (self.ec + self.wc):
            if (client.name) in self.visitable:
                return self.visitable[(client.name)]
            self.firstPortArrivalDates = []
            for laycan in range(self.laycanDates[0],self.laycanDates[1]+1):
                if laycan + client.travelTime(client) + self.vesQty/9.6 <= client.arrivalWindow[1] + 0.5 and (
                laycan + client.travelTime(client) + self.vesQty/9.6 >= client.arrivalWindow[0] - 0.5):
                    self.firstPortArrivalDates.append(laycan + client.travelTime(client) + self.vesQty/9.6)
            if len(self.firstPortArrivalDates):
                self.visitable[(client.name)] = True
                self.firstPortDict[(client.name)] = self.firstPortArrivalDates
                # if self.name == 'CHEMROAD DITA':
                #     print self.firstPortArrivalDates
                #     print 'yes', (client.name)
                return True
            else:
                self.visitable[(client.name)] = False  
                return False

        #and (laycan + client.travelTime(client) + 2 >= client.arrivalWindow[0]) 

        if (self.ec + self.wc) == 1 and (not client.qDist[self.name]):
            oldClient = self.physicalPortsVisited[0]
            self.secondPortArrivalDates = []
            if (self.clientsVisited[0],client.name) in self.visitable:
                return self.visitable[(self.clientsVisited[0],client.name)]
            for leaveFirstPort in self.firstPortDict[(self.clientsVisited[0])]:
                if leaveFirstPort + client.travelTime(oldClient,True) + self.inUse/9.6 <= client.arrivalWindow[1] + 0.5 and (
                    leaveFirstPort + client.travelTime(oldClient,True) + self.inUse/9.6 >= client.arrivalWindow[0] - 0.5):
                    self.secondPortArrivalDates.append(leaveFirstPort + 1 + client.travelTime(oldClient,True))
            if len(self.secondPortArrivalDates):
                self.visitable[(self.clientsVisited[0],client.name)] = True
                self.secondPortDict[(self.clientsVisited[0],client.name)] = self.secondPortArrivalDates
                # if self.name == 'CHEMROAD DITA' and self.clientsVisited[0] == 'ZIL_1':
                #     print self.secondPortArrivalDates
                #     print (self.clientsVisited[0],client.name)
                return True
            else:
                #print 'poop'
                self.visitable[(self.clientsVisited[0],client.name)] = False    
                return False

        return True

class Client(object):
    """Represents a Client.
    Args:
        dischargePort (Port): port used by the Client
        qty (float): amount of solution demanded by the Client
        name (str): Name.

        qDist (dictionary): saves which vessels will deliver to this client
    """
    def __init__(self, dischargePort, qty, name, arrivalWindow, columnIndex, newMin = False, newMax = False):
        self.dischargePort = dischargePort
        self.qty = qty
        self.name = name
        self.arrivalWindow = arrivalWindow
        self.columnIndex = columnIndex
        if newMin:
            self.newMin = newMin
        else:
            self.newMin = int(math.floor(.95*qty))
        if newMax:
            self.newMax = newMax
        else:
            self.newMax = int(math.ceil(1.05*qty))
        
        self.vesselRow = 0
        self.qDist = {}
        self.timeTable = {}

    def isFull(self):
        if sum( self.qDist.itervalues() ) == self.newMax:
            return True
        else:
            return False

    def isAcceptable(self):
        if sum( self.qDist.itervalues() ) >= self.newMin:
            return True
        else:
            return False

    def travelTime(self, client, discharge = False):
        if discharge:
            return self.timeTable[client]
        if client.dischargePort.name == self.dischargePort.name:
            return self.timeTable['Morocco']
        return self.timeTable[client.dischargePort.name]

class Port(object):
    """Represents a discharge Port.
    Args:
        draft (float): Minimum of available "maximum drafts" in meters.
        name (str): Name.
        freightRate (float): Cost per unit cargo
        addPortRate (float): Cost per additional port visited
    """
    def __init__(self, draft, name, coast):
        self.draft = draft
        self.name = name
        self.coast = coast

        self.qDist= {}

def get_arrangements(vessels, clients, ports):
    """Get posssible arrangements of vessels to discharge ports such that all clients are satisfied.
    ##### OLD #### Currently only accounts for draft in ports, and quantity desired by clients.
    Currently adding cost features.

    Args:
        vessels (list<Vessel): Charted vessels available.
        clients (list<Client>): Clients, their desired quantities, and port specfications.
        ports (list<Port>): Ports available.
    
    final answer will be a list of clients, when u search each vessel in dictionary, it will return the
    quantity that vessel will hold
    """

    for client in clients:
        for vessel in vessels:
            client.qDist[vessel.name]=0

    initialState = (clients,vessels)

    def goalTest(someState):
        for x in someState[1]:
            if not x.isFull():
                return False
        for x in someState[0]:
            if not x.isAcceptable():
                return False
        return True

    def actionslist(someState):
        """
        #an example of action that can be taken
        #(client index, vessel index, increase amount)
        """
        thingWeWant = []
        lastResort = []
        vesselspace = [ [],[] ]
        portQtyleft = [ [],[] ]
        granularity = [ '','' ]

        for idx2,vessel in enumerate(someState[1]):
            if not vessel.isFull():
                latestTing = []
                for idx1,client in enumerate(someState[0]):
                    # if vessel.name == 'CHEMROAD DITA' and vessel.ec + vessel.wc == 2:
                    #     print vessel.name, client.name
                    if vessel.currentDraft(client.name) > client.dischargePort.draft or client.isFull() or (
                        client.qDist[vessel.name]==0 and (client.dischargePort.name in vessel.physicalPortsVisited or (
                        vessel.vesQty-vessel.inUse < client.newMin) or sum(client.qDist.itervalues()) or client.newMax - sum(
                        client.qDist.itervalues()) < 7 or vessel.maxPorts == vessel.ec + vessel.wc )) or (
                        client.dischargePort.coast == 'WC' and not vessel.wcRate) or (
                        client.dischargePort.coast == 'EC' and not vessel.ecRate):
                        continue
                    elif client.dischargePort.coast == 'EC':
                        if not client.qDist[vessel.name] and vessel.wc and not vessel.comboRate:
                            continue
                    else: #client.dischargePort.coast == 'WC'
                        if not client.qDist[vessel.name] and vessel.ec and not vessel.comboRate:
                            continue
                    if not vessel.canVisit(client):
                        #print 'we\'re onto something'
                        continue
                    if vessel.inUse ==0 and sum(client.qDist.itervalues()) == 0 and (
                        client.newMin <= vessel.vesQty <= client.newMax):
                        thingWeWant.append( (idx1,idx2, vessel.vesQty ) )
                        latestTing.append( (idx1,idx2, vessel.vesQty ) )
                    elif len(vessel.fullClientDist) == vessel.maxPorts - 1 or (
                        client.qDist[vessel.name] and vessel.vesQty-vessel.inUse < 7 and len(
                        vessel.fullClientDist) == vessel.ec + vessel.wc -1):
                        if client.newMax - sum(client.qDist.itervalues()) < vessel.vesQty-vessel.inUse:
                            continue
                        else:
                            latestTing.append( (idx1,idx2, vessel.vesQty-vessel.inUse ) )
                            thingWeWant.append( (idx1,idx2, vessel.vesQty-vessel.inUse ) )
                    elif client.qDist[vessel.name]==0:
                        thingWeWant.append( (idx1,idx2, client.newMin ))
                        latestTing.append( (idx1,idx2, client.newMin ))
                    else:
                        lastResort.append( (idx1,idx2, 1) )
                        latestTing.append( (idx1,idx2, 1) )
                if len(latestTing) ==1:
                    #print 'where we at tho'
                    return latestTing
        if len(thingWeWant):
            return thingWeWant
        else:
            return lastResort

    def successorfunction(someState, selectedAction):
        """
        #someState is (list of clients, list of vessels)
        #selectedAction is (particular client index, particular vessel index, +1 or -1)
        #update the amount in client dictionary
        #update the amount in vessel.inUse
        """
        newState = copy.deepcopy(someState)
        "Determine old cost"
        oldCost = someState[1][selectedAction[1]].currentCost
        "Increase numPorts if appropriate"
        if newState[0][selectedAction[0]].qDist[newState[1][selectedAction[1]].name] == 0:
            newState[1][selectedAction[1]].clientsVisited.append(newState[0][selectedAction[0]].name)
            newState[1][selectedAction[1]].physicalPortsVisited.append(newState[0][selectedAction[0]].dischargePort.name)
            newState[1][selectedAction[1]].clientDist[newState[0][selectedAction[0]].name] = selectedAction[2]
            if newState[0][selectedAction[0]].dischargePort.coast == 'WC':
                newState[1][selectedAction[1]].wc += 1
            else:
                newState[1][selectedAction[1]].ec += 1
            newState[0][selectedAction[0]].vesselRow = newState[1][selectedAction[1]].rowIndex
        else:
            newState[1][selectedAction[1]].clientDist[newState[0][selectedAction[0]].name] += selectedAction[2]
        "Update quantities"
        newState[0][selectedAction[0]].qDist[newState[1][selectedAction[1]].name]+=selectedAction[2]
        newState[1][selectedAction[1]].inUse+=selectedAction[2]
        if newState[0][selectedAction[0]].isFull():
            for vessel in newState[1]:
                if newState[0][selectedAction[0]].name in vessel.clientDist:
                    vessel.fullClientDist[newState[0][selectedAction[0]].name] = True
        y = newState[1][selectedAction[1]]
        "Determine new cost"
        if y.ec:
            if y.wc:
                rateWeUsing = y.comboRate
            else:
                rateWeUsing = y.ecRate
        else:
            rateWeUsing = y.wcRate
        newCost = y.inUse * (rateWeUsing + y.addPortRate * (y.ec + y.wc-1))
        y.currentCost = newCost
        return (newState, newCost-oldCost)

    def heuristicfunction(someState):
        unitsLeft = 0
        costLeft = 0
        wcVes = [ [y.wcRate, y.vesQty-y.inUse, y.clientDist, y ] for y in someState[1] if y.wcRate ]
        wcVes.sort(key=lambda student: student[0])
        ecVes = [ [y.ecRate, y.vesQty-y.inUse, y.clientDist, y ] for y in someState[1] if y.ecRate ]
        ecVes.sort(key=lambda student: student[0])

        sortedVesOne = [ [min(y.wcRate,y.ecRate), y.vesQty-y.inUse, y ] for y in someState[1] if y.wcRate and y.ecRate ]
        sortedVesTwo = [ [max(y.wcRate,y.ecRate), y.vesQty-y.inUse, y ] for y in someState[1] if not (y.wcRate and y.ecRate) ]
        sortedVes = sortedVesOne + sortedVesTwo
        sortedVes.sort(key=lambda student: student[0])

        p = sortedVes[0][0]

        b = [ x for x in someState[0] ]
        b.sort(key=lambda student: student.dischargePort.draft)

        counter = []
        alertThing = []
        for idx, x in enumerate(someState[0]):
            if not x.isAcceptable():
                counter.append(idx)

        for idx, y in enumerate(someState[1]):
            if not y.isFull():
                alertThing.append(idx)

        '''assigning vessels to ports such that minimum client demands met'''
        for x in b:
            if not x.isAcceptable():
                if x.dischargePort.coast == 'WC':
                    a = wcVes
                else: #x.dischargePort.coast == 'EC'
                    a = ecVes
                unitsNeeded = x.newMin - sum( x.qDist.itervalues() )
                unitsAvailable = 0
                for idx, (rate, space, clientDist, y) in enumerate(a):
                    if space==0 or (x.qDist[y.name]==0 and (x.dischargePort.name in y.physicalPortsVisited or (
                        y.maxPorts == y.ec + y.wc) or sum(x.qDist.itervalues()) or y.vesQty-y.inUse < 7 or  x.newMax - sum(
                        x.qDist.itervalues())< 7)) or (x.dischargePort.coast == 'WC' and not y.wcRate) or (
                        x.dischargePort.coast == 'EC' and not y.ecRate) or (y.currentDraft(x.name) > x.dischargePort.draft):
                        continue
                    if not y.canVisit(x):
                        #print 'blip2'
                        continue
                    if len(y.fullClientDist) == y.maxPorts - 1 or (x.qDist[y.name] and space < 7 and len(y.fullClientDist) == y.ec + y.wc -1):
                        if x.newMax - sum(x.qDist.itervalues()) < space:
                            if x.qDist[y.name]:
                                print 'blam'
                                return sortedVes[-1][0]*sum(y.vesQty for y in someState[1])**2
                            else:
                                continue
                        elif x.qDist[y.name]: #been there before
                            unitsAvailable+= space
                            a[idx][1] = 0
                            print a[idx][1], y.vesQty-y.inUse
                        else:
                            unitsAvailable+= space
                    else:
                        unitsAvailable+= space

                if unitsNeeded > unitsAvailable:
                    return sortedVes[-1][0]*sum(y.vesQty for y in someState[1])**2

        b = [ [x.newMax-sum(x.qDist.itervalues()), x] for x in someState[0] ]
        b.sort(key=lambda student: student[1].dischargePort.draft)

        '''account for space for those who need it'''
        for idx1, (rate, space1, y) in enumerate(sortedVes):
            if space1:
                unitsNeeded = space1
                if unitsNeeded >= 7 and y.maxPorts != y.ec + y.wc:
                    continue
                unitsAvailable = 0
                for idx, (space,x) in enumerate(b):
                    if space and x.name in y.clientDist:
                        unitsAvailable += space
                        if len(y.fullClientDist) == y.maxPorts - 1 or (unitsNeeded < 7 and len(y.fullClientDist) == y.ec + y.wc -1):
                            if unitsNeeded > space:
                                print 'blam2'
                                return ecVes[-1][0]*sum(y.vesQty for y in someState[1])**2
                            else:
                                if y.wcRate:
                                    if y.ec:
                                        rateWeUsing = y.comboRate
                                    else:
                                        rateWeUsing = y.wcRate
                                else: #x.dischargePort.coast == 'EC'
                                    if y.wc:
                                        rateWeUsing = y.comboRate
                                    else:
                                        rateWeUsing = y.ecRate
                                costLeft += unitsNeeded*(rateWeUsing+y.addPortRate*( y.ec + y.wc-1))
                                b[idx][0] -= unitsNeeded
                                sortedVes[idx1][1] = 0
                if unitsNeeded > unitsAvailable:
                    print 'blam3'
                    return ecVes[-1][0]*sum(y.vesQty for y in someState[1])**2
        '''give space for the others'''
        for idx1, (rate, space1, y) in enumerate(sortedVes):
            unitsNeeded = space1
            if unitsNeeded >= 7 and y.maxPorts != y.ec + y.wc:
                unitsAvailable = 0
                for idx, (space,x) in enumerate(b):
                    if space==0 or (x.qDist[y.name]==0 and (space < 7 or sum(x.qDist.itervalues()) or (
                        x.dischargePort.name in y.physicalPortsVisited))) or (y.currentDraft(x.name) > x.dischargePort.draft) or (
                        x.dischargePort.coast == 'WC' and not y.wcRate) or (x.dischargePort.coast == 'EC' and not y.ecRate):
                        continue
                    # if not y.canVisit(x):
                    #     #print 'blip1'
                    #    continue
                    else:
                        unitsAvailable += space
                if unitsNeeded > unitsAvailable:
                    #print 'bloop3'
                    return ecVes[-1][0]*sum(y.vesQty for y in someState[1])**2

        for idx1, (rate, space1, y) in enumerate(sortedVes):
            thingy = 0
            for idx, (space,x) in enumerate(b):
                if space==0 or space1 ==0 or (x.qDist[y.name]==0 and (x.dischargePort.name in y.physicalPortsVisited or (
                    y.maxPorts == y.ec + y.wc) or space < 7 or space1< 7 or sum(x.qDist.itervalues()) )) or (
                    x.dischargePort.coast == 'WC' and not y.wcRate) or (
                    x.dischargePort.coast == 'EC' and not y.ecRate) or (y.currentDraft(x.name) > x.dischargePort.draft):
                    continue
                # if not y.canVisit(x):
                #     #print 'bloooop'
                #     continue
                else:
                    thingy +=1
                    saveVes = idx1
                    saveClient = idx

            if thingy == 1:
                addThing = 0
                #print 'this matters'
                if b[saveClient][0] < sortedVes[saveVes][1]:
                    #print 'oh boy'
                    return ecVes[-1][0]*sum(y.vesQty for y in someState[1])**2
                if y.wcRate:
                    if y.ec:
                        rateWeUsing = y.comboRate
                    else:
                        rateWeUsing = y.wcRate
                else: #x.dischargePort.coast == 'EC'
                    if y.wc:
                        rateWeUsing = y.comboRate
                    else:
                        rateWeUsing = y.ecRate
                if not b[saveClient][1].qDist[y.name]:
                    addThing = 1

                costLeft += space1*(rateWeUsing+y.addPortRate*max(y.ec + y.wc-1 + addThing,0))
                b[saveClient][0] -= sortedVes[saveVes][1]
                sortedVes[saveVes][1]  = 0    
                

        '''assigning the rest of empty vessels to available open ports such that there is no deadweight'''

        # if len(counter) <= 2 and len(alertThing) <= 2:
        #     print 'here~~~'
        #     print counter, alertThing

        for idx, (rate, space, y) in enumerate(sortedVes):
            addThing = 0
            if y.wcRate:
                if y.ec:
                    rateWeUsing = y.comboRate
                else:
                    rateWeUsing = y.wcRate
            else: #x.dischargePort.coast == 'EC'
                if y.wc:
                    rateWeUsing = y.comboRate
                else:
                    rateWeUsing = y.ecRate
            if (y.vesQty > 21 and y.wc + y.ec ==1) or len(y.fullClientDist) == y.wc + y.ec:
                addThing = 1
            if (y.vesQty > 21 and y.wc + y.ec ==0):
                addThing = 2
            #print costLeft, space, rateWeUsing, y.addPortRate, y.ec, y.wc, addThing
            costLeft += space*(rateWeUsing+y.addPortRate*max(y.ec + y.wc-1 + addThing,0))

        #max(y.ec + y.wc-1,0))

        if not len(alertThing):
            print 'um lol'
            # for x in someState[0]:
            #     print x.name, sum(x.qDist.itervalues()), x.qDist
            print 'cost is', sum(y.currentCost for y in someState[1])
            return costLeft

        costLeft += len(alertThing)*len(counter)

        costLeft*= (1.+(p-0.001)/sum(y.vesQty for y in someState[1]))
        #costLeft*= (1-0.1* ((len(someState[1]) - len(alertThing))/len(someState[1]))**1.5  )
        #costLeft*= (.995+0.05*len(counter)/len(someState[0]))
        return costLeft

    return CostSearch(initialState, goalTest, actionslist, successorfunction, heuristicfunction)