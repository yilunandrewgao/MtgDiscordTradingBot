# MtgDiscordTradingBot

A Discord bot for facilitating local Magic: the Gathering trades. Players link their [Moxfield][moxfield-collection] collections or binders and search each other's inventory directly from Discord.

You can [add the bot to your server][bot-invite], or host your own using the instructions below.

## Setup

1. [Create a Discord bot][discord-dev] and copy the token into a `.env` file:
   ```
   DISCORD_TOKEN=your_token_here
   ```
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `python3 src/main.py`

## Commands

| Command                  | Description                              |
|--------------------------|------------------------------------------|
| `!link_moxfield <url>`   | Link your Moxfield collection or binder  |
| `!unlink_moxfield`       | Unlink your collection                   |
| `!link_wishlist <url>`   | Link a Moxfield deck as your wishlist    |
| `!unlink_wishlist`       | Unlink your wishlist                     |
| `!search`                | Search other members' collections by name|
| `!search_exact`          | Search for specific printings            |
| `!search_self`           | Search your own collection               |

To link a collection, set it to public on Moxfield (**Share → Public**), then paste the URL:
```
!link_moxfield https://www.moxfield.com/collection/Tn1Ta-3HsEKtpGYrJG_d6Q
!link_moxfield https://www.moxfield.com/binders/6fs4Mh8xUEScfzKmh0av6Q
```

To link a wishlist, paste the share link from your Moxfield wishlist (**Share → Copy URL**):
```
!link_wishlist https://www.moxfield.com/decks/your-wishlist-share-id
```

You can find the share link at `https://www.moxfield.com/wishlist`.

When a member has a wishlist linked, their name appears with a 🛍️ link in search results.

## Searching

Paste one or more lines directly from a [Moxfield export][moxfield-collection]. Set codes and collector numbers are accepted but ignored — results include all printings:

```
!search 1 Sol Ring
1 Teval, Arbiter of Virtue
1 Agadeem's Awakening / Agadeem, the Undercrypt
```

## Advanced Searching

Use `!search_exact` to match specific printings. Foil finish is respected — cards without a foil marker (`*F*` / `*E*`) are treated as non-foil. Cards without a set code or collector number fall back to a name-only search:

```
!search_exact 1 Sol Ring
1 Teval, Arbiter of Virtue (TDM) 373 *F*
1 Agadeem's Awakening / Agadeem, the Undercrypt (ZNR) 90
```

## Development

**Requirements:** Python 3.11+

Run all tests:
```bash
pytest
```

[discord-dev]: https://discord.com/developers/applications
[bot-invite]: https://discord.com/oauth2/authorize?client_id=1445699447802826762
[moxfield-collection]: https://www.moxfield.com/collection
