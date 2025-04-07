# -*- coding: utf-8 -*-
"""
Created on Monday 16 May 2022
@author: Jeff Cooke

Configuration file for default notebook options.

The below will be what is initially displayed (or used in the background in the case of requestType when the NEMSQC_Notebook or TSDataExplorer notebooks are opened.
"""

# Currently only Hilltop requests are supported, but functions in web_service.py have been built to hopefully allow other types of serverss to be easily supported.
requestType = "Hilltop"

# This is based off Hilltop type requests / urls
serverBase ="https://data.hbrc.govt.nz/EnviroData/"

# This is based off the Hilltop url structure.  The serverBase and serverFile when concatonated form the url before the ? in the url request.
serverFile ="Telemetry.hts"

# The default site to show, needs to be available from the default server files, otherwise there will be errors showing the measurement list.
defaultSite ='HAWQi'

#This is the file that contains the check data
checkFile ="EMARContinuousCheck.hts"

# The default start date to show
startDate = "2020-01-01"

# The default end date to show
endDate = "2020-02-01"