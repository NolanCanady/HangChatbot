#!/usr/bin/env python

import urllib
import json
import os
import gspread
import datetime
import threading,time
import string
import random
from pytz import timezone

from oauth2client.service_account import ServiceAccountCredentials

from flask import Flask
from flask import request
from flask import make_response

#Flask app should start in global layout

app = Flask(__name__)

scope = ['https://spreadsheets.google.com/feeds']
creds = ServiceAccountCredentials.from_json_keyfile_name('client-secret.json', scope)
client = gspread.authorize(creds)

sheet = client.open("Hang Users").sheet1
groupsSheet = client.open("Hang Users").get_worksheet(1)

def gspreadUpdater():
    global scope,creds,client,sheet
    while True:
        print("I called gspreadUpdater")
        scope = ['https://spreadsheets.google.com/feeds']
        creds = ServiceAccountCredentials.from_json_keyfile_name('client-secret.json', scope)
        client = gspread.authorize(creds)
        sheet = client.open('Hang Users').sheet1
        #p1 = wks.worksheet('Printer One')
        time.sleep(3590)

gsUpdateThread = threading.Thread(target=gspreadUpdater)
gsUpdateThread.daemon = True
gsUpdateThread.start()
#
@app.route('/webhook', methods=['POST'])
def webhook():
    #changeAvailability()
    #/
    #scope = ['https://spreadsheets.google.com/feeds']
    #creds = ServiceAccountCredentials.from_json_keyfile_name('client-secret.json', scope)
    #client = gspread.authorize(creds)
    #client.login()
    sheet = client.open("Hang Users").sheet1
    groupsSheet = client.open("Hang Users").get_worksheet(1)
    print(client)
    #
    
    req = request.get_json(silent=True, force=True)
    
    print("Request:")
    print(json.dumps(req, indent=4))
    
    flipShit()
    
    res = makeWebhookResult(req)
    
    res = json.dumps(res, indent=4)
    print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    print(r)
    return r

def flipShit():
    ##
    tz = timezone('EST')
    availabilities = list()
    checkCells = str(sheet.col_values(5))
    checkCells = checkCells.split(',')
    del checkCells[0]
    row = 2
    #while row <= sheet.row_count:
    for x in checkCells:
        avalability = str(x)
        #print(avalability)
        #print(avalability)
        avalability = int(avalability[2])
        if(avalability == 1):
            duration = str(sheet.cell(row,6))
            unit = duration[-3]
            #duration = int(duration[12:-3])
            if (row >= 100):
                duration = int(duration[14:-3])
            elif(row >= 10):
                duration = int(duration[13:-3])
                #print(str(duration)+" ten")
            
                #print(str(duration)+" 100")
            else:
                duration = int(duration[12:-3])
                #print(str(duration)+" 1")
            
            currentTime = int(datetime.datetime.now(tz).strftime("%H%M"))
            login = str(sheet.cell(row,7))
            #print(row)
            if (row >= 100):
                login = int(login[14:-2])
                #print(str(login)+" 100")
            elif(row >= 10):
                login = int(login[13:-2])
                #print(str(login)+" ten")
            else:
                login = int(login[12:-2])
               # print(str(login)+" one")
            if(login > currentTime):
                currentTime = currentTime+2400
            if(unit == 'h'):
                duration = duration * 100
            elif(unit == 'm'):
                duration = duration * 1
            #print(str(duration)+" current-duration: "+str(currentTime-duration)+" login: "+str(login))
            if(currentTime - duration > login):
                sheet.update_cell(row, 5, '0')
        availabilities.append(avalability)
        row+=1

def changeAvailability():
    tz = timezone('EST')
    availabilities = list()
    checkCells = str(sheet.col_values(5))
    checkCells = checkCells.split(',')
    del checkCells[0]
    row = 2
    #while row <= sheet.row_count:
    for x in checkCells:
        avalability = str(x)
        print(avalability)
        avalability = int(avalability[2])
        if(avalability == 1):
            duration = str(sheet.cell(row,6))
            unit = duration[-3]
            duration = int(duration[12:-3])
            currentTime = int(datetime.datetime.now(tz).strftime("%H%M"))
            login = str(sheet.cell(row,7))
            login = int(login[12:-2])
            if(login > currentTime):
                currentTime = currentTime+2400
            if(unit == 'h'):
                duration = duration * 10
            elif(unit == 'm'):
                duration = duration * 1
            print(str(duration)+" current-duration: "+str(currentTime-duration)+" login: "+str(login))
            if(currentTime - duration > login):
                sheet.update_cell(row, 5, '0')
        availabilities.append(avalability)
        row+=1
    print("finished Parse")

def makeWebhookResult(req):
    speech = "Something went wrong... I'm sorry! Please try again <3"
    
    if(req.get("result").get("action") == "set.status"):
        data = req.get("originalRequest")
        context = data.get("data")
        senderData = context.get("From")
        phoneNumber = senderData[1:]
        list_of_number = sheet.col_values(2)
        if (phoneNumber not in list_of_number):
            speech = "You aren't in our system yet, please tell me your name and zip code! ex: 'My name is Hang and my zipcode is 10101"
            return{
                "speech":speech,
                "displayText":speech,
                #"data":{},
                #"contextOut":[],
                "source": "hang-social-app-test"
            }
        else:
            tz = timezone('EST')
            result = req.get("result")
            parameters = result.get("parameters")
            durationParameters = parameters.get("duration")
            duration = durationParameters.get("amount")
            durationUnit = durationParameters.get("unit")
            if durationUnit == "min":
                durationUnit = durationUnit[0]
            status = parameters.get("status")
            speech = "Your status has been set to "+str(status)+" for "+str(duration)+" "+str(durationUnit)
            cell = str(sheet.find(phoneNumber))
            row = cell[7:]
            row = row.split('C')
            col = row[1]
            col = col.split(" ")
            col = int(col[0])
            row = row[0]
            row = int(row)
            #row = int(cell[7])
            #column = int(cell[9])
            sheet.update_cell(row, 4, status)
            sheet.update_cell(row, 5, "1")
            sheet.update_cell(row, 6, str(duration)+str(durationUnit))
            sheet.update_cell(row, 7, datetime.datetime.now(tz).strftime("%H%M"))
            outHour = 0
            outMinute = 0
            if(durationUnit == "h"):
                outHour = int(datetime.datetime.now(tz).strftime("%H")) + duration
                sheet.update_cell(row, 8, str(outHour)+""+datetime.datetime.now(tz).strftime("%M"))
            else:
                outMinute = datetime.datetime.now(tz).minute+duration
                if(outMinute >= 60):
                    outMinute = outMinute - 60
                    outHour = int(datetime.datetime.now(tz).strftime("%H"))
                    outHour = outHour+1
                else:
                    outHour = datetime.datetime.now(tz).strftime("%H")
                sheet.update_cell(row, 8, str(outHour)+""+str(outMinute))
            return{
                "speech":speech,
                "displayText":speech,
                #"data":{},
                #"contextOut":[],
                "source": "hang-social-app-test"
            }
     
    
    
    
    
    if(req.get("result").get("action") == "see.available"):
        data = req.get("originalRequest")
        context = data.get("data")
        senderData = context.get("From")
        phoneNumber = senderData[1:]
        list_of_number = sheet.col_values(2)
        if(phoneNumber not in list_of_number):
            speech = "You aren't in our system yet, please tell me your name and zip code! ex: 'My name is Hang and my zipcode is 10101"
            return{
                "speech":speech,
                "displayText":speech,
                #"data":{},
                #"contextOut":[],
                "source": "hang-social-app-test"
            }
        userPhoneCell = str(sheet.find(phoneNumber))
        userRow = int(userPhoneCell[7])
        userZipCode = str(sheet.cell(userRow,5))
        userZipCode = userZipCode[12:]
        userZipCode = userZipCode[:-2]
        #find all with same zipcode
        flipShit()
        sameZipCells = str(sheet.findall('1'))
        #print("sameZip "+sameZipCells)
        sameRows = list()
        splitZip = sameZipCells.split(',')
        for x in splitZip:
            if(x != "[]"):
                cellStrNew = x
                test = str(cellStrNew)
                row = test[7:]
                row = row.split('C')
                row = row[0]
                row = int(row[1:])
                #row = test[8]
                sameRows.append(row)
        names = list()
        statuses = list()
        durations = list()
        speech = "These people are available in your area:  "
        #print("same Rows "+str(sameRows[0]))
        for x in sameRows:
            #print(x)
            #print(sheet.cell(x,5))
            thisAvailable = str(sheet.cell(x,5))
            #print("this available"+thisAvailable)
            if (x >= 100):
                thisAvailable = thisAvailable[12+2]
            elif(x >= 10):
                thisAvailable = thisAvailable[12+1]
            else:
                thisAvailable = thisAvailable[12]
           # print("this available "+thisAvailable)
            #theirDuration = str(sheet.cell(x,6))
            #theirDuration = theirDuration[12:]
            #theirDuration = theirDuration[:-3]
            #theirDuration = int(theirDuration)
            #tz = timezone('EST')
            #currentTime = datetime.datetime.now(tz).strftime("%H%M")
            #currentTime = int(currentTime)
            #theirLoginTime = str(sheet.cell(x,7))
            #theirLoginTime = theirLoginTime[12:-2]
            #theirLoginTime = int(theirLoginTime)
            #if(theirLoginTime > currentTime):
            #    currentTime = currentTime+2400
            #if(thisAvailable == '1' and currentTime - theirDuration < theirLoginTime):
            if(thisAvailable == '1'):
                addName = str(sheet.cell(x,1))
                addStatus = str(sheet.cell(x,4))
                addDuration = str(sheet.cell(x,6))
                if(x >= 100):
                    addName = addName[14:-2]
                    addStatus = addStatus[14:-2]
                    addDuration = addDuration[14:-2]
                elif(x >= 10):
                    addName = addName[13:-2]
                    addStatus = addStatus[13:-2]
                    addDuration = addDuration[13:-2]
                else:
                    addName = addName[12:-2]
                    addStatus = addStatus[12:-2]
                    addDuration = addDuration[12:-2]
                print(addDuration+" "+addStatus+" "+addName)
                durations.append(addDuration)
                statuses.append(addStatus)
                names.append(addName)
            #elif thisAvailable == '1' and currentTime - theirDuration > theirLoginTime:
                #sheet.update_cell(x, 5, "0")
        count = 0
        for x in names:
            speech = speech+" "+x+" "+statuses[count]+" "+durations[count]+"--"
            count = count +1
        count = 0
        speech = speech[:-2]
        #l
        return{
            "speech": speech,
            "displayText": speech,
            "source": "hang-social-app-test"
        }
        
    if(req.get("result").get("action") == "create.account"):
        data = req.get("originalRequest")
        context = data.get("data")
        senderData = context.get("From")
        phoneNumber = senderData[1:]
        list_of_number = sheet.col_values(2)
        if (phoneNumber not in list_of_number):
            tz = timezone('EST')
            result = req.get("result")
            parameters = result.get("parameters")
            name = parameters.get("name")
            #zipcode = parameters.get("zip-code")
            injection = list()
            injection.append(name)
            injection.append(phoneNumber)
            injection.append("31401")
            injection.append("")
            injection.append("0")
            injection.append("0")
            injection.append("0")
            sheet.append_row(injection)
            inputRow = sheet.row_count
            #sheet.update_cell(inputRow, 1, name)
            #llll
            #sheet.update_cell(inputRow, 2, phoneNumber)
            #sheet.update_cell(inputRow, 3, zipcode)
            #sheet.update_cell(inputRow, 4, "")
            #sheet.update_cell(inputRow, 5, 0)
            #sheet.update_cell(inputRow, 6, "0m")
            #sheet.update_cell(inputRow, 7, 0)
            #sheet.update_cell(inputRow, 8, 0)
            speech = "How's it going "+name+"? Welcome to Hang! To start, ask 'Who's available?' or set your status like 'Set my status to coffee for 30 minutes'"
            return{
                "speech": speech,
                "displayText": speech,
                "source": "hang-social-app-test"
            }
        else:
            cell = str(sheet.find(phoneNumber))
            row = int(cell[7])
            result = req.get("result")
            parameters = result.get("parameters")
            zipcode = parameters.get("zip-code")
            sheet.update_cell(row, 3, str(zipcode))
            speech = "Your zip code has been updated, now go Hang with some more friends!"
            return{
                "speech": speech,
                "displayText": speech,
                "source": "hang-social-app-test"
            }
        
        
    if(req.get("result").get("action") == "create.group"):
        data = req.get("originalRequest")
        context = data.get("data")
        senderData = context.get("From")
        phoneNumber = senderData[1:]
        check_in_system(phoneNumber)
        userPhoneCell = str(sheet.find(phoneNumber))
        userRow = int(userPhoneCell[7])
        result = req.get("result")
        parameters = result.get("parameters")
        groupName = parameters.get("groupName")
        
        groups = str(groupsSheet.col_values(1))
        print(groups)
        if(userRow >= 100):
            groups = groups[13:-2]
        elif(userRow >= 10):
            groups = groups[12:-2]
        else:
            groups = groups[11:-2]
        groups = groups.split(',')
        print(groups)
        samesies = 0
        newGroupName = groupName
        lastGroup = groups[len(groups)-1]
        lastGroup = lastGroup+"'"
        groups[len(groups)-1] = lastGroup
        for x in groups:
            xHold = x
            print(xHold+"---"+xHold[2:-1])
            if(xHold[2:-1] == newGroupName):
                samesies += 1
                newGroupName = groupName+str(samesies)
        groupName = newGroupName
        uniqueID = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        ids = str(groupsSheet.col_values(2))
        if(userRow >= 10):
            ids = ids[12:-2]
        elif(userRow >= 100):
            ids = ids[13:-2]
        else:
            ids = ids[11:-2]
        ids = ids.split(',')
        samesies = 0
        newID = uniqueID
        for x in ids:
            if(x == newID):
                samesies += 1
                newID = uniqueID+samesies
                
        uniqueID  = newID
        groupData = list()
        groupData.append(groupName)
        groupData.append(uniqueID)
        groupData.append(phoneNumber)
        
        cell = str(sheet.find(phoneNumber))
        row = cell[7:]
        row = row.split('C')
        row = row[0]
        row = int(row)
        #row = int(cell[7])
        
        currentGroups = str(sheet.cell(row,9))
        currentIDS = str(sheet.cell(row,10))
        if(row >= 100):
            currentGroups = str(currentGroups[14:-2])
            currentIDS = str(currentIDS[15:-2] )
        elif(row >= 10):
            currentGroups = str(currentGroups[13:-2])
            currentIDS = str(currentIDS[14:-2] )
        else:
            currentGroups = str(currentGroups[12:-2])
            currentIDS = str(currentIDS[13:-2])
        
        print(currentGroups)
        print(currentIDS)
        print(groupName)
        print(uniqueID)
        newGroupsString = currentGroups+","+groupName
        newIDSString = currentIDS+","+uniqueID
        sheet.update_cell(row, 9, newGroupsString)
        sheet.update_cell(row, 10, newIDSString)
        groupsSheet.append_row(groupData)
        speech = "The group: "+groupName+" has been made! Add friends to this group by having them text me this code: "+uniqueID
        return{
            "speech":speech,
            "displayText":speech,
            #"data":{},
            #"contextOut":[],
            "source":"hang-social-app-test"
        }
        
    
    if(req.get("result").get("action") == "join.group"):
        data = req.get("originalRequest")
        context = data.get("data")
        senderData = context.get("From")
        phoneNumber = senderData[1:]
        check_in_system(phoneNumber)
        userPhoneCell = str(sheet.find(phoneNumber))
        #
        userRow = userPhoneCell[7:]
        userRow = userRow.split('C')
        userRow = userRow[0]
        userRow = int(userRow)
        flipShit()
        #userRow = int(userPhoneCell[7])
        result = req.get("result")
        parameters = result.get("parameters")
        joinId = parameters.get("groupID")
        list_of_ids = groupsSheet.col_values(2)
        if(joinId not in list_of_ids):
            speech = "Sorry, I wasn't able to find that group ID in my system.. Please double check it and try again"
            return{
                "speech":speech,
                "displayText":speech,
                #"data":{},
                #"contextOut":[],
                "source": "hang-social-app-test"
            }
        foundIdHolder = str(groupsSheet.find(joinId))
        idRow = foundIdHolder[7:]
        idRow = idRow.split('C')
        idRow = idRow[0]
        idRow = int(idRow)
        #idRow = int(foundIdHolder[7])#
        currentNumbers = str(groupsSheet.cell(idRow, 3))
        if(idRow >= 100):
            currentNumbers = currentNumbers[14:-2] 
        elif(idRow >= 10):
            currentNumbers = currentNumbers[13:-2]
        else:
            currentNumbers = currentNumbers[12:-2]
        groupsSheet.update_cell(idRow, 3, currentNumbers+"'"+phoneNumber)
        groupName = str(groupsSheet.cell(idRow,1))
        groupName = groupName[12:-2]
        currentGroups = str(sheet.cell(userRow,9))
        currentIDS = str(sheet.cell(userRow,10))
        if(idRow >= 100):
            currentGroups = currentGroups[15:-2]
            currentIDS = currentIDS[16:-2] 
        elif(idRow >= 10):
            currentGroups = currentGroups[14:-2]
            currentIDS = currentIDS[15:-2]
        else:
            currentGroups = currentGroups[13:-2]
            currentIDS = currentIDS[14:-2]
        sheet.update_cell(userRow, 9, currentGroups+","+groupName)
        sheet.update_cell(userRow, 10, currentIDS+","+joinId)
        speech = "Congrats! You've joined: "+groupName+". Text 'Whose available in "+groupName+"' to see people here that want to hang"
        return{
            "speech":speech,
            "displayText":speech,
            #"data":{},
            #"contextOut":[],
            "source": "hang-social-app-test"
        }
        
        
    
    if(req.get("result").get("action") == "group.available"):
        data = req.get("originalRequest")
        context = data.get("data")
        senderData = context.get("From")
        phoneNumber = senderData[1:]
        check_in_system(phoneNumber)
        result = req.get("result")
        parameters = result.get("parameters")
        groupName = parameters.get("groupName")
        list_of_groups = str(groupsSheet.col_values(1))
        if(groupName not in list_of_groups):
            speech = "Sorry, I wasn't able to find that group in my system.. Please double check it and try again"
            return{
                "speech":speech,
                "displayText":speech,
                #"data":{},
                #"contextOut":[],
                "source": "hang-social-app-test"
            }
        groupCell = str(groupsSheet.find(groupName))
        groupRow = groupCell[7:]
        groupRow = groupRow.split('C')
        groupRow = groupRow[0]
        groupRow = int(groupRow)
        #groupRow = int(groupCell[7])
        
        groupMembers = str(groupsSheet.cell(groupRow,3))
        groupMembers = groupMembers[:-2]
        
        if(groupRow >= 100):
            groupMembers = groupMembers[14:]
        elif(groupRow >= 10):
            groupMembers = groupMembers[13:]
        else:
            groupMembers = groupMembers[12:]
        groupMembers = groupMembers.split("'")
        
        speech = "These group members are available: "
        groupRows = list()
        names = list()
        statuses = list()
        durations = list()
        for x in groupMembers:
            #find their phonenumbers rows
            #
            member = str(x[1:])
            member = str(sheet.find(x))
            row = member[7:]
            row = row.split('C')
            row = row[0]
            memberRow = int(row)
            #memberRow = int(member[7])
            groupRows.append(memberRow)
        for x in groupRows:
            memberAvailable = str(sheet.cell(x,5))
            if(x >= 100):
                memberAvailable = memberAvailable[14]
            elif (x >= 10):
                memberAvailable = memberAvailable[13]
            else:
                memberAvailable = memberAvailable[12]
            if(memberAvailable == '1'):
                
                addName = str(sheet.cell(x,1))
                addStatus = str(sheet.cell(x,4))
                addDuration = str(sheet.cell(x,6))
                if(x >= 100):
                    addName = addName[14:-2]
                    addStatus = addStatus[14:-2]
                    addDuration = addDuration[14:-2]
                elif (x >= 10):
                    addName = addName[13:-2]
                    addStatus = addStatus[13:-2]
                    addDuration = addDuration[13:-2]
                else:
                    addName = addName[12:-2]
                    addStatus = addStatus[12:-2]
                    addDuration = addDuration[12:-2]
                names.append(addName)
                statuses.append(addStatus)
                durations.append(addDuration)
                
                
        count = 0
        for x in names:
            speech = speech+" "+x+" "+statuses[count]+" "+durations[count]+"--"
            count = count +1
        count = 0
        speech = speech[:-2]
        return{
            "speech":speech,
            "displayText":speech,
            "source":"hang-social-app-test"
        }
        
    if(req.get("result").get("action") == "get.groups"):
        data = req.get("originalRequest")
        context = data.get("data")
        senderData = context.get("From")
        phoneNumber = senderData[1:]
        check_in_system(phoneNumber)
        row = str(sheet.find(phoneNumber))
        row = row[7:]
        row = row.split('C')
        row = int(row[0])
        list_of_groups = str(sheet.cell(row, 9))
        list_of_ids = str(sheet.cell(row,10))
        print(list_of_groups)
        print(list_of_ids)
        speech = "Here are your groups:  "
        #if(row >= 10):
         #   list_of_groups
        #elif(row >= 100):
            
        #else:
            
        list_of_groups = list_of_groups.split(",")
        list_of_ids = list_of_ids.split(",")
        print(list_of_groups)
        print(list_of_ids)
        count = 0
        holdString = list_of_groups[0]
        
        if(row >= 100):
            holdString = holdString[13:]
        elif(row >= 10):
            holdString = holdString[12:]
        else:
            holdString = holdString[11:]
        list_of_groups[0] = holdString[1:]
        holdString = list_of_groups[len(list_of_groups)-1]
        holdString = holdString[:-2]
        list_of_groups[len(list_of_groups)-1] = holdString
        lastId = list_of_ids[len(list_of_ids)-1]
        lastId = lastId[:-2]
        list_of_ids[len(list_of_ids)-1] = lastId
        for x in list_of_groups:
            thisid = list_of_ids[count]
            thisid = thisid[-6:]
            groupName = x
            groupName = groupName[:]
            speech = speech+groupName+" - "+thisid+", "
            count+=1
        speech = speech[:-2]
        return{
            "speech":speech,
            "displayText":speech,
            "source":"hang-social-app-test"
        }
           
    return{
        "speech": speech,
        "displayText": speech,
        "source": "hang-social-app-test"
    }

def check_in_system(phoneNumber):
    list_of_number = sheet.col_values(2)
    if(phoneNumber not in list_of_number):
        speech = "You aren't in our system yet, please tell me your name and zip code! ex: 'My name is Hang and my zipcode is 10101"
        return {
            "speech":speech,
            "displayText":speech,
            #"data":{},
            #"contextOut":[],
            "source": "hang-social-app-test"
        }

if __name__ == '__main__':
    port = int(os.getenv('PORT',5000))
    print("Starting app on port %d" % port)
    app.run(debug=True, port=port, host='0.0.0.0')