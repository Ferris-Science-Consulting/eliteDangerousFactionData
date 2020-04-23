import pickle
import requests
import json
import math
import configparser
import importlib
import os.path
from numpy import array,zeros,c_
from datetime import date,timedelta,datetime
from pathlib import Path
from scipy.stats.stats import pearsonr
from matplotlib import pyplot
from pprint import pprint
import logging

def getDataFromEDDB(url, file):
    webRequest = requests.get(url) 
    with open(file,'w') as localDataFile:
        data = webRequest.text
        localDataFile.write(data)
        return data


def readLocalData(fileName):
        localDataFile = open(fileName,'r')
        data = json.load(localDataFile)
        localDataFile.close()
        return data

def convertToFactionData(systems,facList):
        factions = {}
        for sid,system in systems.items():
                systemName = system['name']
                x = system['x']
                y = system['y']
                z = system['z']
                d = distanceFromMeliae(x,y,z)
                for faction in system['minor_faction_presences']:
                        id = str(faction['minor_faction_id'])
                        inf = faction['influence']
                        name = facList[eval(id)]['name']
                        try:
                                factions[id]['systems'].append(dict(systemId = sid, systemName = systemName,influence = inf, distance=d))
                        except KeyError:
                                factions[id] = {'name':name,'systems':[dict(systemId = sid,systemName = systemName,influence = inf, distance=d)]}
        return factions

def createSystemInfluceList(systems):
        for sid,sys in systems.items():
                for i,faction in enumerate(sys['minor_faction_presences']):
                        inf = faction['influence']
                        systems[sid]['minor_faction_presences'][i]['influence']=[inf]
        return systems

def addDailyInfluence(previousSystems,currentSystems,length):
        for sid,sys in previousSystems.items():
                for i,faction in enumerate(sys['minor_faction_presences']):
                        id = faction['minor_faction_id']
                        currentFactions = currentSystems[sid]['minor_faction_presences']
                        factionExists = False
                        for currFac in currentFactions:
                                if id == currFac['minor_faction_id']:
                                        inf = currFac['influence']
                                        previousSystems[sid]['minor_faction_presences'][i]['influence'].append(inf)
                                        factionExists = True
                                        break
                        if factionExists==False:
                                previousSystems[sid]['minor_faction_presences'][i]['influence'].append(0)
                for i,newFac in enumerate(currentSystems[sid]['minor_faction_presences']):
                        id = newFac['minor_faction_id']
                        factionExists = False
                        previousFactions = previousSystems[sid]['minor_faction_presences']
                        for prevFac in previousFactions:
                                if id == prevFac['minor_faction_id']:
                                        factionExists=True
                                        break
                        if factionExists ==False:
                                inf = newFac['influence']
                                infVec = [0]*(length+1)
                                infVec[-1] = inf
                                previousSystems[sid]['minor_faction_presences'].append(newFac)
                                previousSystems[sid]['minor_faction_presences'][-1]['influence']=infVec
        return previousSystems                       

def reduceSystems(systems,maxRadius):
        smallSystems = {}
        for sys in systems:
                x = sys['x']
                y = sys['y']
                z = sys['z']
                r = distanceFromMeliae(x,y,z)
                if r < maxRadius:
                        id = str(sys['id'])
                        smallSystems[id]=dict(
                                name=sys['name'],#
                                distance=r,#
                                minor_faction_presences=sys['minor_faction_presences'],#
                                x = sys['x'], #
                                y = sys['y'], #,
                                z = sys['z'] #
                                )
        return smallSystems

def reduceSystemsCube(systems,originSystemName,cubesize):
        smallSystems = {}
        originSystem = findObject(systems,originSystemName)
        for targetSystem in systems.values():
                if inSideCube(originSystem,targetSystem,cubesize):
                        id = str(targetSystem['id'])
                        smallSystems[id]=dict(
                                name=targetSystem['name'],#
                                # distance=r,#
                                minor_faction_presences=targetSystem['minor_faction_presences'],#
                                x = targetSystem['x'], #
                                y = targetSystem['y'], #,
                                z = targetSystem['z'], #
                                lastUpdatedAt=targetSystem['updated_at']
                                )
        return smallSystems

def inSideCube(originSystem,targetSystem,cubesize):
        if (
                abs(originSystem['x']-targetSystem['x']) < cubesize and
                abs(originSystem['y']-targetSystem['y']) < cubesize and
                abs(originSystem['z']-targetSystem['z']) < cubesize ):
                inside = True
        else:
                inside = False
        return inside

def distanceFromTarget(target,origin):
        x0 = origin['x']
        y0 = origin['y']
        z0 = origin['z']
        x = target['x']
        y = target['y']
        z = target['z']
        distance = math.sqrt(pow((x-x0),2)+pow((y-y0),2)+pow((z-z0),2)) 
        return distance

def getFactionName(factions,factionData):
        for k in factions:
                factions[k]['name']=factionData[eval(k)]['name']
        return factions

def createSeries(systems):
        series = []
        for sysId,sys in systems.items():
                x = sys['x']
                y = sys['y']
                z = sys['z']
                distance = distanceFromMeliae(x,y,z)
                for fac in sys['minor_faction_presences']:
                        facId = str(fac['minor_faction_id'])
                        influence = fac['influence']
                        series.append([sysId,facId,influence,distance])                
        return series

def countFactionSystems(factions):
        count = 0
        for i in factions:
                for k,s in enumerate(factions[i]['systems']):
                        count += 1
                        if k>0:
                                s
        return count

def getData(file,url):
        if os.path.isfile(file):
                data = readLocalData(file)
                logging.info('local file loaded: '+file)
        else:
                data = getDataFromEDDB(url,file)
                logging.info('local file loaded: '+file)
        return data

def convertListToDict(list):
        dictionary = {}
        for l in list:
                id = l['id']
                dictionary[id] = l
        return dictionary

def getDateString(dateTime):
        day = dateTime.strftime("%Y_%m_%d")
        return day

def createTimeSeries(baseLineSystems,startDate,endDate,maxRadius,folder):
        currentDate = startDate
        timeSeries = []
        length = 0
        while currentDate < endDate:
                currentDate = currentDate + timedelta(days=1)
                logging.info(currentDate)
                systemsfile = getFileName(currentDate,folder,'_localSystems.json')
                if os.path.isfile(systemsfile):
                        length += 1
                        currentSystems =  readLocalData(systemsfile)
                        logging.info(systemsfile)
                        currentSystems = reduceSystems(currentSystems,maxRadius)
                        timeSeries = addDailyInfluence(baseLineSystems,currentSystems,length)
        return timeSeries

def getFileName(targetDate,folder,fileType):
        fileName = str(folder/getDateString(targetDate))+fileType
        return fileName


def getDailyFiles(sysURL,facURL,folder):
        sysFile = getFileName(date.today(),folder,'_localSystems.json')
        facFile = getFileName(date.today(),folder,'_localFactions.json')
        getData(sysFile,sysURL)
        getData(facFile,facURL)


def calculateCorrelation(vectors,NewPkey):
        ''' 
        vectors = ['sysId','facId',[influence],radius]
        results = ['sysId','facId',radiu,pearsonCoeff,p-value]
        '''
        results = []
        # find Meliae
        for v in vectors:
                if v[1]==NewPkey:
                        NewPvec = v[2]
                        logging.info('Found NewP')
                        break
        # Calculate pearson coefficient
        for v in vectors:
                systemVec = v[2]
                if len(systemVec) != len(NewPvec):
                        logging.info("Vectors are not equal")
                coeff = pearsonr(NewPvec,v[2])
                results.append([v[0],v[1],v[3],coeff[0],coeff[1]])
        return results
                
def plot(correlation):
        # correlation = ['sysId','facId',radiu,pearsonCoeff,p-value]
        coeff = []
        pValue = []
        for v in correlation:
                coeff.append(v[3])
                pValue.append(v[4])
        pyplot.plot(coeff)
        pyplot.show()
        pyplot.plot(pValue)
        pyplot.show()

# def pickSystems(systems,sysIDs):
#         reducedSystems = {}
#         for id in sysIDs:
#                 for sys in systems:
#                         reducedSystems[id] = systems[id]
#         return reducedSystems

def findExpansionCandidate (targetSystemName):
        sysFile = getFileName(date.today(),data_folder,cf.get('sysFileType'))
        systems = getData(sysFile,cf.get('systemsURL'))
        systems = convertListToDict(systems)
        systems = reduceSystemsCube(systems,targetSystemName,20)
        targetSystem = findObject(systems,targetSystemName)
        facFile = getFileName(date.today(),data_folder,cf.get('facFileType'))
        facList = getData(facFile,cf.get('factionsURL'))
        factions = convertListToDict(facList) 
        uncontestedSystems = []
        contestedSystems = []
        latestTick = findLatestTick()
        for sys in systems.values():
                if (len(sys['minor_faction_presences']) < 7) :
                        sys['d']=distanceFromTarget(sys,targetSystem)
                        uncontestedSystems.append(sys)
                else:
                        sys['minor_faction_presences'].sort(key=returnFactionInfluence)
                        for facs in sys['minor_faction_presences']:
                                facId = facs['minor_faction_id']
                                if not (factions[facId]['is_player_faction'] or factions[facId]['government']=='Engineer' or facId==76748):
                                        name = sys['name']
                                        influence = facs['influence']
                                        factionName = factions[facId]['name']
                                        if datetime.utcfromtimestamp(sys['lastUpdatedAt'] ) > latestTick:
                                                updatedToday = True
                                        contestedSystems.append({
                                                "system":name,
                                                "faction":factionName,
                                                "influence":influence,
                                                "updatedToday":updatedToday})
                                        break
                                
        dumpExpansionTargets(uncontestedSystems,contestedSystems)
        


def dumpExpansionTargets(uncontested,contested):
        data = {}
        if len(uncontested)>0:
                uncontested.sort(key=returnSystemDistance)
                data['Uncontested_Systems'] = uncontested
        if len(contested)>0:
                contested.sort(key=returnFactionInfluence)
                data['Contested_Systems'] = contested
        with open(cf.get('expansionTargetFile'),'w',encoding='utf-8') as file:
                json.dump(data,file,ensure_ascii=False, indent=4)

def loadExpansionTargets(top):
        with open(cf.get('expansionTargetFile'),'r',encoding='utf-8') as file:
                data = json.load(file)
                reduced = {}
                if 'Uncontested_Systems' in data:
                        a = min(len(data['Uncontested_Systems']),top)
                        uncontested = data['Uncontested_Systems'][0:a]
                        reduced['Uncontested_Systems'] = uncontested
                if 'Contested_Systems' in data:
                        b = min(len(data['Contested_Systems']),top)
                        contested = data['Contested_Systems'][0:b]
                        reduced['Contested_Systems'] = contested
                return reduced

def showExpansionData():
        data = loadExpansionTargets(10)
        output = ''
        if 'Uncontested_Systems' in data:
                output += '**Uncontested systems**\n'
                for fac in data['Uncontested_Systems']:
                        output += 'System: '+ fac['system'] + ', influence: '+ str(fac['influence']) + '\n'
        if 'Contested_Systems' in data:
                output += '**Contested systems**\n'
                for fac in data['Contested_Systems']:
                        output += 'System: '+ fac['system'] + ', influence: '+ str(fac['influence']) + '\n'
        return output

def returnSystemDistance(sys):
        return sys['d']

def returnFactionInfluence(fac):
        return fac['influence']

def findLatestTick():
        now = datetime.utcnow()
        if now.hour > int(cf.get('tickTime')):
                latestTick = datetime(now.year,now.month,now.day,14,0)
        else:
                latestTick = datetime(now.year,now.month,now.day,14,0)-timedelta(days=1)
        return latestTick

def createNumericalModel (startDate,systemsURL,maxRadius,endDate,NewPkey,folder):
        baseLineSystemsFile = getFileName(startDate,folder,'_localSystems.json')
        baseLineSystems = getData(baseLineSystemsFile,systemsURL)
        baseLineSystems = reduceSystems(baseLineSystems,maxRadius)
        systemsInf = createSystemInfluceList(baseLineSystems)
        timeSeries = createTimeSeries(systemsInf,startDate,endDate,maxRadius,folder)
        vectors = createSeries(timeSeries)
        correlation = calculateCorrelation(vectors,NewPkey)
        return correlation



def findObject(dict, targetName):
        for d in dict.values():
                if d['name'] == targetName:
                        return d
                else:
                        "Object not found"

def test_findSystem(systems):
        assert findSystem(systems,'Meliae')['id'] == 13569, "Should be 13569"

# Paths
root_path = Path("./")
data_folder = root_path/"Data/"
log_folder = root_path/"Log/"

# Loading config
config = configparser.ConfigParser()
config.read('config.ini')
cf = config['DEFAULT']

# logging
log_file = getFileName(date.today(),log_folder,'.log')
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',filename=log_file,level=logging.INFO)

# getDailyFiles(systemsURL,factionsURL,data_folder)

# findExpansionCandidate('Meliae')
#model = createNumericalModel(startDate,systemsURL,maxRadius,endDate,NewPkey,data_folder)

#plot(model)


# Add to task scheduler https://stackoverflow.com/questions/44727232/scheduling-a-py-file-on-task-scheduler-in-windows-10

""" if __name__ == "__main__":
    import sys
    readLocalData()

"""
import pickle
import requests
import json
import math
import configparser
import importlib
import os.path
from numpy import array,zeros,c_
from datetime import date,timedelta,datetime
from pathlib import Path
from scipy.stats.stats import pearsonr
from matplotlib import pyplot
from pprint import pprint
import logging

def getDataFromEDDB(url, file):
    webRequest = requests.get(url) 
    with open(file,'w') as localDataFile:
        data = webRequest.text
        localDataFile.write(data)
        return data


def readLocalData(fileName):
        localDataFile = open(fileName,'r')
        data = json.load(localDataFile)
        localDataFile.close()
        return data

def convertToFactionData(systems,facList):
        factions = {}
        for sid,system in systems.items():
                systemName = system['name']
                x = system['x']
                y = system['y']
                z = system['z']
                d = distanceFromMeliae(x,y,z)
                for faction in system['minor_faction_presences']:
                        id = str(faction['minor_faction_id'])
                        inf = faction['influence']
                        name = facList[eval(id)]['name']
                        try:
                                factions[id]['systems'].append(dict(systemId = sid, systemName = systemName,influence = inf, distance=d))
                        except KeyError:
                                factions[id] = {'name':name,'systems':[dict(systemId = sid,systemName = systemName,influence = inf, distance=d)]}
        return factions

def createSystemInfluceList(systems):
        for sid,sys in systems.items():
                for i,faction in enumerate(sys['minor_faction_presences']):
                        inf = faction['influence']
                        systems[sid]['minor_faction_presences'][i]['influence']=[inf]
        return systems

def addDailyInfluence(previousSystems,currentSystems,length):
        for sid,sys in previousSystems.items():
                for i,faction in enumerate(sys['minor_faction_presences']):
                        id = faction['minor_faction_id']
                        currentFactions = currentSystems[sid]['minor_faction_presences']
                        factionExists = False
                        for currFac in currentFactions:
                                if id == currFac['minor_faction_id']:
                                        inf = currFac['influence']
                                        previousSystems[sid]['minor_faction_presences'][i]['influence'].append(inf)
                                        factionExists = True
                                        break
                        if factionExists==False:
                                previousSystems[sid]['minor_faction_presences'][i]['influence'].append(0)
                for i,newFac in enumerate(currentSystems[sid]['minor_faction_presences']):
                        id = newFac['minor_faction_id']
                        factionExists = False
                        previousFactions = previousSystems[sid]['minor_faction_presences']
                        for prevFac in previousFactions:
                                if id == prevFac['minor_faction_id']:
                                        factionExists=True
                                        break
                        if factionExists ==False:
                                inf = newFac['influence']
                                infVec = [0]*(length+1)
                                infVec[-1] = inf
                                previousSystems[sid]['minor_faction_presences'].append(newFac)
                                previousSystems[sid]['minor_faction_presences'][-1]['influence']=infVec
        return previousSystems                       

def reduceSystems(systems,maxRadius):
        smallSystems = {}
        for sys in systems:
                x = sys['x']
                y = sys['y']
                z = sys['z']
                r = distanceFromMeliae(x,y,z)
                if r < maxRadius:
                        id = str(sys['id'])
                        smallSystems[id]=dict(
                                name=sys['name'],#
                                distance=r,#
                                minor_faction_presences=sys['minor_faction_presences'],#
                                x = sys['x'], #
                                y = sys['y'], #,
                                z = sys['z'] #
                                )
        return smallSystems

def reduceSystemsCube(systems,originSystemName,cubesize):
        smallSystems = {}
        originSystem = findObject(systems,originSystemName)
        for targetSystem in systems.values():
                if inSideCube(originSystem,targetSystem,cubesize):
                        id = str(targetSystem['id'])
                        smallSystems[id]=dict(
                                name=targetSystem['name'],#
                                # distance=r,#
                                minor_faction_presences=targetSystem['minor_faction_presences'],#
                                x = targetSystem['x'], #
                                y = targetSystem['y'], #,
                                z = targetSystem['z'], #
                                lastUpdatedAt=targetSystem['updated_at']
                                )
        return smallSystems

def inSideCube(originSystem,targetSystem,cubesize):
        if (
                abs(originSystem['x']-targetSystem['x']) < cubesize and
                abs(originSystem['y']-targetSystem['y']) < cubesize and
                abs(originSystem['z']-targetSystem['z']) < cubesize ):
                inside = True
        else:
                inside = False
        return inside

def distanceFromTarget(target,origin):
        x0 = origin['x']
        y0 = origin['y']
        z0 = origin['z']
        x = target['x']
        y = target['y']
        z = target['z']
        distance = math.sqrt(pow((x-x0),2)+pow((y-y0),2)+pow((z-z0),2)) 
        return distance

def getFactionName(factions,factionData):
        for k in factions:
                factions[k]['name']=factionData[eval(k)]['name']
        return factions

def createSeries(systems):
        series = []
        for sysId,sys in systems.items():
                x = sys['x']
                y = sys['y']
                z = sys['z']
                distance = distanceFromMeliae(x,y,z)
                for fac in sys['minor_faction_presences']:
                        facId = str(fac['minor_faction_id'])
                        influence = fac['influence']
                        series.append([sysId,facId,influence,distance])                
        return series

def countFactionSystems(factions):
        count = 0
        for i in factions:
                for k,s in enumerate(factions[i]['systems']):
                        count += 1
                        if k>0:
                                s
        return count

def getData(file,url):
        if os.path.isfile(file):
                data = readLocalData(file)
                logging.info('local file loaded: '+file)
        else:
                data = getDataFromEDDB(url,file)
                logging.info('local file loaded: '+file)
        return data

def convertListToDict(list):
        dictionary = {}
        for l in list:
                id = l['id']
                dictionary[id] = l
        return dictionary

def getDateString(dateTime):
        day = dateTime.strftime("%Y_%m_%d")
        return day

def createTimeSeries(baseLineSystems,startDate,endDate,maxRadius,folder):
        currentDate = startDate
        timeSeries = []
        length = 0
        while currentDate < endDate:
                currentDate = currentDate + timedelta(days=1)
                logging.info(currentDate)
                systemsfile = getFileName(currentDate,folder,'_localSystems.json')
                if os.path.isfile(systemsfile):
                        length += 1
                        currentSystems =  readLocalData(systemsfile)
                        logging.info(systemsfile)
                        currentSystems = reduceSystems(currentSystems,maxRadius)
                        timeSeries = addDailyInfluence(baseLineSystems,currentSystems,length)
        return timeSeries

def getFileName(targetDate,folder,fileType):
        fileName = str(folder/getDateString(targetDate))+fileType
        return fileName


def getDailyFiles(sysURL,facURL,folder):
        sysFile = getFileName(date.today(),folder,'_localSystems.json')
        facFile = getFileName(date.today(),folder,'_localFactions.json')
        getData(sysFile,sysURL)
        getData(facFile,facURL)


def calculateCorrelation(vectors,NewPkey):
        ''' 
        vectors = ['sysId','facId',[influence],radius]
        results = ['sysId','facId',radiu,pearsonCoeff,p-value]
        '''
        results = []
        # find Meliae
        for v in vectors:
                if v[1]==NewPkey:
                        NewPvec = v[2]
                        logging.info('Found NewP')
                        break
        # Calculate pearson coefficient
        for v in vectors:
                systemVec = v[2]
                if len(systemVec) != len(NewPvec):
                        logging.info("Vectors are not equal")
                coeff = pearsonr(NewPvec,v[2])
                results.append([v[0],v[1],v[3],coeff[0],coeff[1]])
        return results
                
def plot(correlation):
        # correlation = ['sysId','facId',radiu,pearsonCoeff,p-value]
        coeff = []
        pValue = []
        for v in correlation:
                coeff.append(v[3])
                pValue.append(v[4])
        pyplot.plot(coeff)
        pyplot.show()
        pyplot.plot(pValue)
        pyplot.show()

# def pickSystems(systems,sysIDs):
#         reducedSystems = {}
#         for id in sysIDs:
#                 for sys in systems:
#                         reducedSystems[id] = systems[id]
#         return reducedSystems

def findExpansionCandidate (targetSystemName):
        sysFile = getFileName(date.today(),data_folder,cf.get('sysFileType'))
        systems = getData(sysFile,cf.get('systemsURL'))
        systems = convertListToDict(systems)
        systems = reduceSystemsCube(systems,targetSystemName,20)
        targetSystem = findObject(systems,targetSystemName)
        facFile = getFileName(date.today(),data_folder,cf.get('facFileType'))
        facList = getData(facFile,cf.get('factionsURL'))
        factions = convertListToDict(facList) 
        uncontestedSystems = []
        contestedSystems = []
        latestTick = findLatestTick()
        for sys in systems.values():
                if (len(sys['minor_faction_presences']) < 7) :
                        sys['d']=distanceFromTarget(sys,targetSystem)
                        uncontestedSystems.append(sys)
                else:
                        sys['minor_faction_presences'].sort(key=returnFactionInfluence)
                        for facs in sys['minor_faction_presences']:
                                facId = facs['minor_faction_id']
                                if not (factions[facId]['is_player_faction'] or factions[facId]['government']=='Engineer' or facId==76748):
                                        name = sys['name']
                                        influence = facs['influence']
                                        factionName = factions[facId]['name']
                                        if datetime.utcfromtimestamp(sys['lastUpdatedAt'] ) > latestTick:
                                                updatedToday = True
                                        contestedSystems.append({
                                                "system":name,
                                                "faction":factionName,
                                                "influence":influence,
                                                "updatedToday":updatedToday})
                                        break
                                
        dumpExpansionTargets(uncontestedSystems,contestedSystems)
        


def dumpExpansionTargets(uncontested,contested):
        data = {}
        if len(uncontested)>0:
                uncontested.sort(key=returnSystemDistance)
                data['Uncontested_Systems'] = uncontested
        if len(contested)>0:
                contested.sort(key=returnFactionInfluence)
                data['Contested_Systems'] = contested
        with open(cf.get('expansionTargetFile'),'w',encoding='utf-8') as file:
                json.dump(data,file,ensure_ascii=False, indent=4)

def loadExpansionTargets(top):
        with open(cf.get('expansionTargetFile'),'r',encoding='utf-8') as file:
                data = json.load(file)
                reduced = {}
                if 'Uncontested_Systems' in data:
                        a = min(len(data['Uncontested_Systems']),top)
                        uncontested = data['Uncontested_Systems'][0:a]
                        reduced['Uncontested_Systems'] = uncontested
                if 'Contested_Systems' in data:
                        b = min(len(data['Contested_Systems']),top)
                        contested = data['Contested_Systems'][0:b]
                        reduced['Contested_Systems'] = contested
                return reduced

def showExpansionData():
        data = loadExpansionTargets(10)
        output = ''
        if 'Uncontested_Systems' in data:
                output += '**Uncontested systems**\n'
                for fac in data['Uncontested_Systems']:
                        output += 'System: '+ fac['system'] + ', influence: '+ str(fac['influence']) + '\n'
        if 'Contested_Systems' in data:
                output += '**Contested systems**\n'
                for fac in data['Contested_Systems']:
                        output += 'System: '+ fac['system'] + ', influence: '+ str(fac['influence']) + '\n'
        return output

def returnSystemDistance(sys):
        return sys['d']

def returnFactionInfluence(fac):
        return fac['influence']

def findLatestTick():
        now = datetime.utcnow()
        if now.hour > int(cf.get('tickTime')):
                latestTick = datetime(now.year,now.month,now.day,14,0)
        else:
                latestTick = datetime(now.year,now.month,now.day,14,0)-timedelta(days=1)
        return latestTick

def createNumericalModel (startDate,systemsURL,maxRadius,endDate,NewPkey,folder):
        baseLineSystemsFile = getFileName(startDate,folder,'_localSystems.json')
        baseLineSystems = getData(baseLineSystemsFile,systemsURL)
        baseLineSystems = reduceSystems(baseLineSystems,maxRadius)
        systemsInf = createSystemInfluceList(baseLineSystems)
        timeSeries = createTimeSeries(systemsInf,startDate,endDate,maxRadius,folder)
        vectors = createSeries(timeSeries)
        correlation = calculateCorrelation(vectors,NewPkey)
        return correlation



def findObject(dict, targetName):
        for d in dict.values():
                if d['name'] == targetName:
                        return d
                else:
                        "Object not found"

def test_findSystem(systems):
        assert findSystem(systems,'Meliae')['id'] == 13569, "Should be 13569"

# Paths
root_path = Path("./")
data_folder = root_path/"Data/"
log_folder = root_path/"Log/"

# Loading config
config = configparser.ConfigParser()
config.read('config.ini')
cf = config['DEFAULT']

# logging
log_file = getFileName(date.today(),log_folder,'.log')
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',filename=log_file,level=logging.INFO)

# getDailyFiles(systemsURL,factionsURL,data_folder)

# findExpansionCandidate('Meliae')
#model = createNumericalModel(startDate,systemsURL,maxRadius,endDate,NewPkey,data_folder)

#plot(model)


# Add to task scheduler https://stackoverflow.com/questions/44727232/scheduling-a-py-file-on-task-scheduler-in-windows-10

""" if __name__ == "__main__":
    import sys
    readLocalData()

"""
