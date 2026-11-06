# Discord Organiser Bot

A Discord bot for managing organization of game rounds with buyer spots and claiming system.

## Features

- `o!organise` command to create an organization embed
- `o!template` command to save an administrator-defined incense template
- Permission checks (Organiser role or Administrator)
- Buyer spots display with interactive claim buttons
- Auto-update embed when spots are claimed
- Persistent data storage in `buyer.json`

## Setup

1. **Install Python** (3.8 or higher)

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Create a Discord Bot:**
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Click "New Application"
   - Go to "Bot" tab and click "Add Bot"
   - Copy the token (you'll need this to run the bot)
   - Enable these intents: Message Content, Members

4. **Run the bot:**
```bash
python bot.py
```
   - When prompted, paste your bot token

## Configuration

- **Target Channel ID**: Currently set to `1322105765783146518`. Change this in `bot.py` if needed.
- **Prefix**: Command prefix is `o!` (e.g., `o!organise`)
- **Buyer Categories**: Edit `buyer.json` to customize buyer spots

## Permissions

The `o!organise` command can only be run by:
- Users with the "Organiser" role
- Users with Administrator permissions
- Users with a role that has Administrator permissions

## Commands

- `o!organise <template-name>` - Create an organization using a saved template,
  such as `o!organise hw26`
- `o!template <name>` - Reply to a normal message containing lines in the form
  `Category - number incense - price` to save a named template, such as
  `o!template hw26`. Only administrators can use this command. Incense totals must
  be exactly 100, 200, 300, 400, or 500.
- `o!allow @role` - Allow an administrator-selected role to run `o!start`.
- `o!start` - After all spots and incense channels are bought, send the stored
  reserve commands in the current channel.
- `o!bp 1` - Bypass waiting for all spots to be claimed.
- `o!bp 2` - Bypass waiting for all incense channels to be bought.

`o!bp` is restricted to administrators and the role configured with `o!allow`.
Phase 1 bypass still tracks every configured incense channel, including channels
for unclaimed spots. Ending the org removes the temporary round-buyer role from
all participants.

## How It Works

1. Run `o!organise` in any channel (if you have permission)
2. An embed is sent to the configured target channel showing all buyer spots
3. Users can click buttons below the embed to claim spots
4. The embed automatically updates to show who claimed each spot
5. Claiming data is saved to `buyer.json`
6. Users who claim a spot receive the configured buyer role for the current round;
   releasing their last spot removes it. When all spots are claimed, that role is
   pinged to buy incense. When all incense is bought, the organiser is pinged to
   start the reserve announcement. The organiser is never ended automatically.

## Data Storage

All claimed spots are stored in `buyer.json` and persist between bot restarts.
