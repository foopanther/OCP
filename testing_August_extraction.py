import datetime
import math
from openpyxl import Workbook, load_workbook
from July_19_backend import Vessel, Client, Port
from July_19_backend import get_arrangements

FILENAME = 'August_Loading_Template.xlsx'
NEWFILENAME = 'August_Schedule.xlsx'

wb = load_workbook(filename = FILENAME)
behind = wb.worksheets[1]
visible = wb.worksheets[0]
timetable = wb.worksheets[2]

for cell in behind.columns[4]:
	if not cell.value:
		numPorts = cell.row - 1
		break
for idx,cell in enumerate(visible.columns[0]):
	if not cell.value and idx>4:
		numVes = cell.row - 1 - 2
		break

STARTING_DATE = visible.columns[2][3+numVes+1].value - datetime.timedelta(days=1)

#####laycans have been switched to tuples
vesselNames = [cell.value for cell in visible.columns[4][3:numVes+2]]
ves1 = [ Vessel(math.ceil(behind.columns[8][idx].value), behind.columns[9][idx].value, (1,40),
	behind.columns[7][idx].value, behind.columns[10][idx].value,
	behind.columns[11][idx].value, behind.columns[12][idx].value, 
	behind.columns[13][idx].value, behind.columns[14][idx].value) for idx in range(len(behind.columns[0])) if (
	behind.columns[7][idx].value in vesselNames)]

for vessel in ves1:
	for idx, cell in enumerate(visible.columns[4]):
		if cell.value == vessel.name:
			vessel.laycanDates = ( int((visible.columns[2][idx].value-STARTING_DATE).total_seconds()/86400.),
				int((visible.columns[3][idx].value-STARTING_DATE).total_seconds()/86400.))
			vessel.rowIndex = idx
			break

ports = tuple([Port(behind.columns[4][idx].value, behind.columns[3][idx].value,
	behind.columns[5][idx].value) for idx in range(1, numPorts)])
vess = tuple(ves1)

clients1=[]
for idx1, cell in enumerate(visible.rows[2]):
	if idx1 < 6:
		continue
	if cell.value == 'TOTAL':
		break
	OGclientName = cell.value.split("_")[0]
	for idx2,clientDB in enumerate(behind.columns[0]):
		if clientDB.value == OGclientName:
			correspondingDPort = behind.columns[1][idx2].value
			break
	for port in ports:
		if port.name == correspondingDPort:
			portInQuestion = port
			break 
	clients1.append(Client(portInQuestion, visible.rows[5+numVes][idx1].value, cell.value,
		((visible.rows[3+numVes][idx1].value-STARTING_DATE).total_seconds()/86400.,
		int((visible.rows[4+numVes][idx1].value-STARTING_DATE).total_seconds()/86400.)), idx1))

for client in clients1:
	for idx, cell in enumerate(timetable.columns[0]):
		if cell.value == client.dischargePort.name:
			for idx2,cell2 in enumerate(timetable.rows[idx]):
				if not idx2:
					continue
				client.timeTable[timetable.rows[0][idx2].value] = cell2.value
			break

clients = tuple(clients1)

final_list = get_arrangements(vess, clients, ports)

for column,row,qty in final_list[0]:
	visible.columns[column][row].value = qty
for row, portsVisited in final_list[1]:
	for idx, port in enumerate(portsVisited):
		visible.rows[row][6+len(clients)+1+idx].value = port

wb.save(NEWFILENAME)
print 'yay!'


# print visible.columns[2][3].value
# print (visible.columns[2][3].value-STARTING_DATE).total_seconds()/86400.
# a= Port(11.6, 'B. Qasim', 'WC') #pakistan, Northernmost
# b= Port(12, 'Jubail', 'WC') #east coast of Saudi Arabia
# ports = (a,b,c,d,e,f,g,h,i,j)

# clients = (
#     Client(a, 20, 'FFBL_1', (34,39)), #34,35 stretched late to accomadate Genuine Hercules to DFL
#     Client(a, 20, 'FFBL_2', (41,44)), #43,44 stretched early to accomadate IVY GALAXY
#	  )

# '''capacity,max draft,name,   wcRate, ecRate, comboRate, addPortRate, max discharge ports'''
# vess = (
#     Vessel(19, 9.61, (31,40), 'Ginga Hawk', 39.50, 44.75, 48.50-1.5, 1.5, 2), #LAYCAN ADJUSTED I have as west coast only,
#     Vessel(19, 9.46, (8,15), 'AZALEA GALAXY', 39.50, False, False, 1.5, 2),)#LAYCAN ADJUSTED