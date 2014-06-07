import json
import requests
from pytz import timezone
import pytz
from datetime import datetime
import time
import monthdelta
from datetime import timedelta
from dateutil import rrule

measurementsUri = 'http://sensor.nevada.edu/Services/Measurements/Measurement.svc'
dataRetrievalUri = 'http://sensor.nevada.edu/Services/DataRetrieval/DataRetrieval.svc'
timeZoneUTC = {"BaseUtcOffset": "PT0S","DaylightName": "Coordinated Universal Time","DisplayName": "(UTC) Coordinated Universal Time","Id": "UTC","StandardName": "Coordinated Universal Time","SupportsDaylightSavingsTime": False}
timeZoneUSPacific = {"Id": "Pacific Standard Time","DisplayName": "(UTC-08:00) Pacific Time (US & Canada)","DaylightName": "Pacific Daylight Time","StandardName": "Pacific Standard Time","SupportsDaylightSavingsTime": True,"BaseUtcOffset": "-PT8H"}
def getLogicalSensorInfo():
	'''
		Retrives the logical sensros (we need the sensorId and the unitId)
	'''
	response = requests.post(measurementsUri+'/json/LogicalSensorInformation/ListLogicalSensorInformation')
	logicalSensors = json.loads(response.text)
	return logicalSensors['d']


def getUTCTimestamp(dateTime,timeZone='UTC'):
	'''
		Returns the UTC timestamp (in milisecs) for a given date in a given timezone
	'''
	tz = timezone(timeZone)
	#make the datetime local
	dt = tz.localize(dateTime)
	#convert the datetime to utc
	dtUtc = dt.astimezone(pytz.UTC)
	#return the number of milisecs
	return int(time.mktime(dtUtc.timetuple()) * 1000)


def getNumberOfData(UTCTimestampFrom,UTCTimestampTo,timeZone,sensorId,unitId):
	'''
		returns the number of date from a given time interval in a specified logical sensor.
		getting data in US/Pacific timeZone
	'''
	headers = {'Content-type': 'application/json;charset=utf-8'}
	data = { "Starting": "/Date(" + str(UTCTimestampFrom) + ")/", "Ending": "/Date(" + str(UTCTimestampTo) + ")/","TimeZone": timeZone,"Sensors": [{"LogicalSensorId":sensorId,"UnitId": unitId}]}
	data = { "search": data}
	response = requests.post(dataRetrievalUri+'/json/Search/NumberOfResults',data=json.dumps(data), headers=headers)
	response = json.loads(response.text)
	return response['d']

def getData(UTCTimestampFrom,UTCTimestampTo,timeZone,sensorId,unitId,totalResults=0):
	resultsPerPage = 1000
	headers = {'Content-type': 'application/json;charset=utf-8'}
	searchQuery = { "Starting": "/Date(" + str(UTCTimestampFrom) + ")/", "Ending": "/Date(" + str(UTCTimestampTo) + ")/","TimeZone": timeZone,"Sensors": [{"LogicalSensorId":sensorId,"UnitId": unitId}]}
	data = []
	for i in range(0,totalResults,resultsPerPage):
	    if i+resultsPerPage > totalResults:
	        search = { "search": searchQuery, "skip": i,"take": (totalResults-i)}
	    else:
	        search = { "search": searchQuery, "skip": i,"take": (i+resultsPerPage)}
	    response = requests.post(dataRetrievalUri+'/json/Search/Search',data=json.dumps(search), headers=headers)
	    response = json.loads(response.text)
	    data.extend(response['d'])

	return data
    
def dateStrToISODate(dateStr,timeZone):
	'''
	    the date format is something like /Date(1388563260000-0800)/
	    here 1388563260000 is the unix timestamp in milisecs and 0800 is the offset in hours
	'''
	#get the value 1388563260000-0800
	dateStr = dateStr[dateStr.index("(") + 1:dateStr.rindex(")")]
	#split it
	dateStr = dateStr.split("-")
	#now subtract the offset from the timestamp
	dateTimestamp = int(dateStr[0]) - int(dateStr[1][0:2])*3600000
	#create the timezone
	tz = timezone(timeZone)
	#make the datetime object aware of timezone
	dt = tz.localize(datetime.fromtimestamp(0) + timedelta(seconds=dateTimestamp/1000))
	#return the date in iso format
	return dt.isoformat()

def dumpData(filename,sensorMetadata,timeZoneMetadata,data):
	with open(filename,'w') as f:
		#put the metada at first
		f.write('Site:'+sensorMetadata['Deployment']['Site']['Name']+'\n')
		f.write('Deployment:'+sensorMetadata['Deployment']['Name']+'\n')
		f.write('Monitored System:'+sensorMetadata['MonitoredProperty']['System']['Name']+'\n')
		f.write('Measured Property:'+sensorMetadata['MonitoredProperty']['Name']+'\n')
		#not sure what this is going to be???
		f.write('Vertical Offset from Surface:'+str(sensorMetadata['SurfaceAltitudeOffset'])+'\n')
		f.write('Units:'+sensorMetadata['Unit']['Abbreviation']+'\n')
		f.write('Measurement Type:'+sensorMetadata['Type']['Name']+'\n')
		f.write('Measurement interval:'+sensorMetadata['MeasurementInterval']+'\n')
		f.write('Time Stamp '+'('+timeZoneMetadata['Id']+')'+'\n')
		#time to put the data
		for row in data:
			#convert the timestamp to ISO 8601 format
			isoDate = dateStrToISODate(str(row['TimeStamp']),timeZoneUTC['Id'])
			f.write(isoDate+','+str(row['Value']))
			f.write('\n')


def getDataMonthly(startYear,startMonth,endYear,endMonth,logicalSensors):
	#iterate through each month ()
	for dt in rrule.rrule(rrule.MONTHLY, dtstart=datetime(startYear,startMonth,1,0,0,0), until=datetime(endYear,endMonth,1,1,1)):
	    #starting time (example 2014-01-01 00:00:00)
	    startTime = getUTCTimestamp(dt)
	    #ending time (example 2014-01-31 23:59:00)
	    endTime = getUTCTimestamp(dt+monthdelta.MonthDelta(1)- timedelta(minutes=1))
	    #for each sensor get the data for the month
	    for sensor in logicalSensors:
	    	#get the number of results
	        numResults = getNumberOfData(startTime,endTime,timeZoneUTC,sensor['Id'],sensor['Unit']['Id'])
	        if numResults > 0:
	        	#get the data
		        data = getData(startTime,endTime,timeZoneUTC,sensor['Id'],sensor['Unit']['Id'],totalResults=numResults)
		        fileName = str(startTime)+'-'+str(endTime)+'-'+str(sensor['Id'])+'-'+str(sensor['Unit']['Id'])
		        #dump the data to a file
		        dumpData(fileName,sensor,timeZoneUTC,data)
	       	


#This is how we call the getDataMonthly function
#logicalSensors = getLogicalSensorInfo()
#getDataMonthly(2014,1,2014,12,logicalSensors)


#Lets check the function with a single logical sensor and data of a single single month 
logicalSensors = [{
		"__type" : "LogicalSensor:http://sensor.nevada.edu/Measurement/2012/05",
		"Deployment" : {
			"__type" : "MonitoringDeployment:http://sensor.nevada.edu/Measurement/2012/05",
			"Id" : 204,
			"LocationWkt" : "POINT (-114.308911645998 38.9061140862817 3353.4096)",
			"Name" : "Air temperature (10-meter) monitor",
			"Site" : {
				"__type" : "MonitoringSite:http://sensor.nevada.edu/Measurement/2012/05",
				"Id" : 8,
				"Name" : "Snake Range West Subalpine"
			}
		},
		"Id" : 1088,
		"LocationWkt" : "POINT (-114.308911645998 38.9061140862817 3353.4096)",
		"MeasurementInterval" : "PT1M",
		"MonitoredProperty" : {
			"__type" : "PhysicalProperty:http://sensor.nevada.edu/Measurement/2012/05",
			"Description" : "The temperature of the air.",
			"Id" : 3,
			"Name" : "Temperature",
			"System" : {
				"__type" : "MonitoredSystem:http://sensor.nevada.edu/Measurement/2012/05",
				"Id" : 4,
				"Name" : "Atmosphere"
			}
		},
		"SurfaceAltitudeOffset" : 10,
		"Type" : {
			"__type" : "MeasurementType:http://sensor.nevada.edu/Measurement/2012/05",
			"Description" : "The average of a series of automatically-collected sensor measurements over a period of time.",
			"Id" : 2,
			"Name" : "Average"
		},
		"Unit" : {
			"__type" : "MeasurementUnit:http://sensor.nevada.edu/Measurement/2012/05",
			"Abbreviation" : "degK",
			"Aspect" : {
				"__type" : "PhysicalQuantity:http://sensor.nevada.edu/Measurement/2012/05",
				"Id" : 55,
				"Name" : "Temperature"
			},
			"Id" : 99,
			"Name" : "degree kelvin"
		}
}]
getDataMonthly(2014,1,2014,1,logicalSensors)