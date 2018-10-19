#!/usr/local/bin/python
import sys
import json
import urllib2
import base64
import boto3
from boto3 import client
from datetime import date

# get login details from Parameter Store
ssm = boto3.client('ssm',region_name="us-east-1")
ssm_user = ssm.get_parameter(Name="JIRAuser",WithDecryption=True)['Parameter']['Value']
ssm_password = ssm.get_parameter(Name="JIRApassword",WithDecryption=True)['Parameter']['Value']

# set vars
username = ssm_user
password = ssm_password
today = date.today()
s3BucketName = "db-check"
s3 = client('s3')

# get current DB job
for key in s3.list_objects(Bucket=s3BucketName)['Contents']:
    currentDB = (key['Key'])

# create function to copy file to next week's DB type then delete the current file
def bucketOperation(newFile, oldFile):
    newPath = "%s/%s" % (s3BucketName, oldFile)
    s3Object = boto3.resource('s3')
    s3Object.Object(s3BucketName, newFile).copy_from(CopySource=newPath)
    s3Object.Object(s3BucketName,oldFile).delete()

# logic for DB type this week
if currentDB == "prod1.txt":
    dbTag = "Prod1 Restore Test %s/%s/%s" % (today.day, today.month, today.year)
    nextDB = "prod2.txt"
    bucketOperation(nextDB, currentDB)
elif currentDB == "prod2.txt":
     dbTag = "Prod2 Restore Test %s/%s/%s" % (today.day, today.month, today.year)
     nextDB = "prod3.txt"
     bucketOperation(nextDB, currentDB)
elif currentDB == "prod3.txt":
     dbTag = "Prod3 Restore Test %s/%s/%s" % (today.day, today.month, today.year)
     nextDB = "none.txt"
     bucketOperation(nextDB, currentDB)
elif currentDB == "none.txt":
     nextDB = "prod1.txt"
     bucketOperation(nextDB, currentDB)
     sys.exit()

# JIRA functions
# set endpoint
JiraEndPoint = 'https://your.JIRA.URL.net/rest/api/2/issue/'

# encode JIRA login details
myAuthString = base64.standard_b64encode('%s:%s' % (username, password))

# set values for ticket
json_values = {
    "fields": {
    "labels": ["BackupDBTest"],
    "project": {"key": "DEVOPS"},
    "summary": dbTag,
    "description": "Please follow the steps outlined in: "
      "<URL to confluence page here>"
      "This will test if our backups functions are working correctly",
    "issuetype": {"name": "Task"}
    }
}

# create the payload for the URL request
response = urllib2.Request(JiraEndPoint, data=json.dumps(json_values), headers={'Authorization': "Basic %s" % myAuthString, 'Content-Type': 'application/json'})
# make the URL request
resp = urllib2.urlopen(response)
