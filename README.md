# CloudGenix Slackbot (Preview)
[![image](https://img.shields.io/pypi/v/slackbot-cloudgenix.svg)](https://pypi.org/project/slackbot-cloudgenix/)
[![image](https://img.shields.io/pypi/pyversions/slackbot-cloudgenix.svg)](https://pypi.org/project/slackbot-cloudgenix/)
[![Downloads](https://pepy.tech/badge/slackbot-cloudgenix)](https://pepy.tech/project/slackbot-cloudgenix)
[![License: MIT](https://img.shields.io/pypi/l/slackbot-cloudgenix.svg?color=brightgreen)](https://pypi.org/project/slackbot-cloudgenix/)
[![GitHub issues open](https://img.shields.io/github/issues/ebob9/slackbot-cloudgenix.svg)](https://github.com/ebob9/slackbot-cloudgenix/issues)

CloudGenix AppFabric plugin functions for lins05/slackbot.

#### Synopsis
Slackbot for CloudGenix Items.

#### Features
Create a bot, ask it about your network. Details/examples to be added. Ask your bot `@botname help`
 
#### Requirements
* Active CloudGenix Account
* Python >=3.6
* Python modules:
    * Slackbot - <https://github.com/lins05/slackbot>
    * CloudGenix Python SDK >= 5.2.1b1 - <https://github.com/CloudGenix/sdk-python>
    * Tabulate - <https://github.com/astanin/python-tabulate>
    * IDNA - <https://github.com/kjd/idna>
    * FuzzyWuzzy - <https://github.com/seatgeek/fuzzywuzzy>
    * Pandas - <https://pandas.pydata.org/>

#### License
MIT

#### Installation:
 - **PIP:** `pip install slackbot-cloudgenix`. After install, configure the following:
   - Copy `slackbot_settings.py.example` to `slackbot_settings.py`, and edit/fill out.
   - Run `python3 ./run_bot.py`
   - Send `@your_bot_name help` message to bot on slack, try out the commands.

#### Examples of usage:
```

Aaron Edwards  10:21 PM
@cloudgenix_bot show sites
✅

CloudGenix BotAPP  10:21 PM
@aaron:
    Name                    Admin State    Tags           Domain
    ----------------------  -------------  -------------  -------------------
    Chicago Branch 2        active         AUTO-zscaler   East Coast Branches
    New York Branch 1       active         Prisma_Access  East Coast Branches
    San Francisco DC 1      active
    Seattle Branch 3        active                        West Coast Branches
    Washington D.C. - DC 2  active
```

#### Caveats and known issues:
 - This is a PREVIEW release, hiccups to be expected. Please file issues on Github for any problems.
 
#### Version
| Version | Build | Changes |
| ------- | ----- | ------- |
| **0.5.1** | **b1** | Update to fix large site response, add initial site health prototype |
| **0.5.0** | **b1** | Initial Release |
| **0.0.1** | **b1** | Placeholder Release |
