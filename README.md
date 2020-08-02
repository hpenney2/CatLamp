# CatLamp
 CatLamp, the all-in-one Discord bot.

# Getting the bot running
 1. Preferably, but not necessary, be running a Linux system.
 2. Run `python3 -m pip install -r requirements.txt`.
 3. Set up a `config.json` file in the repository root with the format below.
 4. Start the bot with `python3 CatLampPY.py.`

# `config.json` format (subject to change)
```json
{
	"token":"bot_token_here",
	"githubUser":"github_username_here",
	"githubPAT":"github_personal_access_token_here"
}
```
`githubPAT` can be your password or a personal access token generated in settings (that has the repo scope).