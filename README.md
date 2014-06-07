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
