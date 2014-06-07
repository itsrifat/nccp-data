nccp-data
=========

python script for extracting data from nevada climate change portal.

all we need to do is call the function ```getDataMonthly``` s follows:
```python

#it gets a list of logicalSensor objects
logicalSensors = getLogicalSensorInfo()
#here starting month is Janury 2012, ending month is December 2014
getDataMonthly(2012,1,2014,12,logicalSensors)

```

An exmaple data file should lok like follows (the date is in ISO 8601 format)

```csv

Site:Snake Range West Subalpine
Deployment:Air temperature (10-meter) monitor
Monitored System:Atmosphere
Measured Property:Temperature
Vertical Offset from Surface:10
Units:degK
Measurement Type:Average
Measurement interval:PT1M
Time Stamp (UTC)
2012-01-01T00:00:00+00:00,269.392
2012-01-01T00:01:00+00:00,269.397
2012-01-01T00:02:00+00:00,269.377
....
....

```
