# Automated NEMS Information

## Introduction

## Parameters
The parameters are saved in the optionsList.csv file.  This file can be manually edited, or once you have a set of options that you are happy with then these can be saved to the file for future use.

**Note**  The latest (last row) set of options for a site and measurement combination will be loaded when that site and measurement is selected.  If there isn't an entry for that site and measurement then the last entry for site Default will be loaded.  If there isn't a Default entry then the system default values will be displayed and used.

### NEMS

The [NEMS Documents](http://www.nems.org.nz/documents/) define the acceptable values for measurements.

**resolution**
Number of decimal places that the results should have.

**timeGap**
The maximum number of minutes allowed between readings.

**accuracyThreshold**
Not yet implemented. This is the amount of deviation allowed between readings and check readings.  It relies on check readings being available.

**accuracyBandwidth**
??? 

## General

These tests are from Qartod.
The full definition of the quartod tests is [here](https://ioos.github.io/ioos_qc/api/ioos_qc.html#module-ioos_qc.qartod)
The tests used are gross_range_test, flat_line_test, rate_of_change_test and spike_test.

**grossRangeFailBelow**
The minimum value that the sensor can record.

**grossRangeFailAbove**
The maximum value that the sensor can record.

**grossRangeSuspectBelow**
The lowest value expected for the site and measurement.

**grossRangeSuspectAbove**
The highest value expected for the site and measurement.

**flatLineTolerance**
The tolerance value that should be exceeded by a reading within the time threshold window.

**flatLineSuspectThreshold**
The number of seconds to assess the flatline test over before flagging as suspect.

**flatLineFailThreshold**
The number of seconds to assess the flatline test over before flagging as fail.

**rateOfChangeThreshold**
The maximum allowed rate of change of the observational unit per second.

**spikeSuspectThreshold**
The suspect threshold for spike detection (in observational units).

**spikeFailThreshold**
The fail threshold for spike detection (in observational units).

## Mapping to NEMS Codes.

The file QC_Mapping.csv is the mapping table that converts the output from the automated script to NEMS codes, and a flag determining whether the data point should be kept or not.  This file uses the quartod flag numeric codes as the input for the mapping.

|Flag|Description|
|:-----:|:-------------|
| 1 | Good |
| 2 | Unknown |
| 3 | Suspect |
| 4 | Fail |
| 9 | Missing |

The combination of aggregate (from qartod / general), NEMS_accuracy, and NEMS_aggregate fields are mapped to NEMS codes and the flag for the data point.

|NEMS QC|Action|Criteria|
|:--------:|:--------:|:--------------------------------------------------------------------|
|QC600| Keep | Only be attained if all of the flags are good (1). |
|QC500| Keep | If the accuracy is good (1), the qartod aggregate is either good (1) or suspect (3), and the NEMS aggregate is not good (2,3,4). |
|QC400| Keep | If the accuracy fails (4), and the qartod aggregate is either good (1) or suspect (3). |
|QC400| Drop | If the qartod aggregate fails (4). |
|QC200| Keep | Everything else.|

