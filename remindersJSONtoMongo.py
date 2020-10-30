from json import load
import pymongo
import pymongo.errors as mongo_errors
import os
import sys

mongo = pymongo.MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
remindersDB = mongo["db"]["reminders"]
print("Checking if the MongoDB daemeon is running...")
try:
    mongo.server_info()
    print("MongoDB is running. Starting conversion...")
except mongo_errors.ServerSelectionTimeoutError:
    print('The MongoDB server is not currently running. Please read the "Setting up MongoDB" section in README.md.')
    input("Press enter to close, then restart the script when fixed.")
    sys.exit(1)

if os.path.isfile("reminders.json"):
    reminders = {}
    with open("reminders.json", "r") as file:
        reminders = load(file)
    for rem in reminders.values():
        id = rem["userId"]
        del rem["userId"]
        rem["_id"] = id
        remindersDB.insert_one(rem)
    print("Conversion complete. It is now safe to delete reminders.json.")
else:
    print("There is no reminders.json file, no conversion to be made.")
    sys.exit(0)