import json
import os

if os.path.exists("config.json"):
    print("config.json already exists! If you'd like to make an new one, please remove the current one first.")
    exit(1)

data = {}

print("Note: Optional keys are not shown here. They must be added manually. See README.md for more details.")

print("Enter your bot token:")
token = input()
data["token"] = token

print("Enter your GitHub username:")
username = input()
data["githubUser"] = username

print("Enter your GitHub personal access token (requires repo scope):")
pat = input()
data["githubPAT"] = pat

print("Enter your Reddit client ID:")
clientID = input()
data["redditCID"] = clientID

print("Enter your Reddit client secret:")
secret = input()
data["redditSecret"] = secret

with open("config.json", "w") as config:
    json.dump(data, config)
print("config.json generated successfully!")
