# MtgDiscordTradingBot

Discord bot to facilitate local trades for Magic the Gathering cards. Allows players to link their [moxfield collections](https://moxfield.com/collection) and search other players' collections.

You can get a discord access token to host your own bot, or you can install the existing bot here: https://discord.com/oauth2/authorize?client_id=1445699447802826762

# Testing
* Set PYTHONPATH: `$env:PYTHONPATH = "{pwd}\src"`
* Run tests: `python3 -m pytest src/test/<test_file_name>.py


## Instructions
* Click share on Moxfield collection
* Set Moxfield collection to public
* Use `!link_moxfield <collection-id>` to link your collection
    * Can link either collections or binders
* Use `!unlink_moxfield` to remove your collection
* Use `!search` to search for a single card in other people's collections
* Use `!search_list` to search for a list of cards
* Use `!search_self` to search your own collection

## Searching

All search commands accept **Moxfield export format** — paste lines directly from a Moxfield export without any editing:

```
!search 1 Counterspell (CMR) 632
```

```
!search_list 1 Sol Ring
1 Teval, Arbiter of Virtue (TDM) 373 *F*
1 Agadeem's Awakening / Agadeem, the Undercrypt (ZNR) 90
```

Quantity, set code, collector number, and foil finish (`*F*` / `*E*`) are all parsed automatically. When a collector number is included, `!search` filters results to that exact printing.

The legacy `{{ card name | collector_number }}` format is still supported for single-card queries typed by hand.

<img width="2183" height="905" alt="image" src="https://github.com/user-attachments/assets/2c2da1b1-a37e-4f77-a733-a0880b7c36e0" />

<img width="708" height="452" alt="image" src="https://github.com/user-attachments/assets/0d709c1d-8f83-4a5b-bb0f-bd4e54e75e91" />
