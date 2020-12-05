# CatLamp [![Codacy Badge](https://app.codacy.com/project/badge/Grade/3f06c8cbb6fd49eebd345e057de3614d)](https://www.codacy.com?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=hpenney2/CatLamp&amp;utm_campaign=Badge_Grade)
 CatLamp, the all-in-one Discord bot.

## Getting the bot running
 1. Preferably, but not necessary, be running an Ubuntu system.
 2. Run `python3 -m pip install -r requirements.txt`.
 4. (Only if on an Ubuntu server) Run `sudo apt-get install libgl1-mesa-glx gcc python3-dev opus-tools` (C compiler [for some packages], Python 3, and libopus [for voice])
 5. Set up a `config.json` file in the repository root with the format below ~~or run `gen_config.py`~~.
 6. Follow the *Setting up MongoDB* guide below.
 7. Start the bot with `python3 CatLampPY.py.`

## Setting up MongoDB
**The bot will NOT run without MongoDB being properly installed.**
Follow the intructions [in the MongoDB documentation](https://docs.mongodb.com/manual/installation/) to install MongoDB.  
After installing, make sure MongoDB is running before starting the bot. **If you have an old `reminders.json` file, run `remindersJSONtoMongo.py` to convert it to MongoDB.**

If you're on Ubuntu, you can have MongoDB start up with your system with the command `sudo systemctl enable mongod.service`.

If you're on Windows, MongoDB should automatically start up with your system, however if it does not, you can make it by starting `services.msc` from the Run dialog (press Win + R), finding the `MongoDB Server` service, then changing its startup type to `Automatic`.

## `config.json` format (subject to change)
You can either copy the format below (recommended) or run the included `gen_config.py` file included.
Optional keys are noted in parentheses, however make sure to remove the parentheses from the actual JSON file.
```json
{
	"token": "bot_token_here",
	"githubUser": "github_username_here",
	"githubPAT": "github_personal_access_token_here",
	"redditCID": "client_id_here",
	"redditSecret": "client_secret_here",
	(OPTIONAL) "dblToken": "DBL_token_here",
	(OPTIONAL) "statcordKey": "statcord_api_key_here"
}
```
`githubPAT` can be your password or a personal access token generated in settings (that has the repo scope).
