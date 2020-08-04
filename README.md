# CatLamp
 CatLamp, the all-in-one Discord bot.

# Getting the bot running
 1. Preferably, but not necessary, be running a Linux system.
 2. Run `python3 -m pip install -r requirements.txt`.
 3. Set up a `config.json` file in the repository root with the format below or run `gen_config.py`.
 4. Start the bot with `python3 CatLampPY.py.`

# `config.json` format (subject to change)
You can either copy the format below or run the included `gen_config.py` file included (recommended).
```json
{
	"token": "bot_token_here",
	"githubUser": "github_username_here",
	"githubPAT": "github_personal_access_token_here",
	"redditCID": "client_id_here",
	"redditSecret": "client_secret_here"
}
```
`githubPAT` can be your password or a personal access token generated in settings (that has the repo scope).