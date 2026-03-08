# MtgDiscordTradingBot

Discord bot to facilitate local trades for Magic the Gathering cards. Allows players to link their [moxfield collections](https://moxfield.com/collection) and search other players' collections.

You can get a discord access token to host your own bot, or you can install the existing bot here: https://discord.com/oauth2/authorize?client_id=1445699447802826762

# Testing
* Set PYTHONPATH: `$env:PYTHONPATH = "{pwd}\src"`
* Run tests: `python3 -m pytest src/test/<test_file_name>.py


## Instructions
* Click share on Moxfield collection
* Set Moxfield collection to public
* Use `!link_moxfield <url>` to link your collection or binder
* Use `!unlink_moxfield` to remove your collection
* Use `!search {{ <card_name> }}` to search for a single card in other people's collections
* Use `!search_list {{ <card_name1> | <card_name2> }}` to search for a list of cards
* Use `!search_self {{ <card_name1> | <card_name2> }}` to search your own collection

<img width="2183" height="905" alt="image" src="https://github.com/user-attachments/assets/2c2da1b1-a37e-4f77-a733-a0880b7c36e0" />

<img width="708" height="452" alt="image" src="https://github.com/user-attachments/assets/0d709c1d-8f83-4a5b-bb0f-bd4e54e75e91" />
