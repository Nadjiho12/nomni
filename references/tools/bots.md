# Tools: bots (Discord, Telegram, Slack) and chat integrations

*Last updated: 2026-09-30 | Version-sensitive: Discord/Telegram/Slack API and library versions; intents and permissions | Re-check current docs before pinning versions, prices, or API names.*

Deliver bot code that runs on first try: pinned library versions, token from the environment, least-privilege permissions, and a short setup checklist. Bots cannot be run against live services here, so mark live behavior **open gap** and syntax-check the code.

## Contents
1. Choose the platform and library
2. Discord (discord.py)
3. Discord (discord.js)
4. Telegram
5. Slack (Bolt)
6. Cross-platform patterns
7. Hosting
8. Verification

## 1. Platform and library

| Platform | Python | Node |
|---|---|---|
| Discord | `discord.py` 2.x | `discord.js` 14 |
| Telegram | `python-telegram-bot` 21 | `grammy` / `telegraf` |
| Slack | `slack_bolt` | `@slack/bolt` |

Use official libraries, slash commands over prefix/message parsing, and only the intents/scopes you need.

## 2. Discord (discord.py)

Setup: Developer Portal → New Application → Bot → copy token → enable only needed Privileged Intents → OAuth2 URL Generator with scopes `bot` + `applications.commands` and minimal permissions → invite. Token goes in `DISCORD_TOKEN`.

```python
import os, discord
from discord import app_commands
from discord.ext import commands, tasks

intents = discord.Intents.default()          # add intents.members = True only if you need member events
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()                    # register slash commands (guild sync is instant; global takes time)
    print(f"logged in as {bot.user}")

@bot.tree.command(name="ping", description="Latency check")
async def ping(i: discord.Interaction):
    await i.response.send_message(f"Pong {round(bot.latency*1000)} ms", ephemeral=True)

@bot.tree.command(name="kick", description="Kick a member")
@app_commands.describe(member="Who to kick", reason="Why")
@app_commands.checks.has_permissions(kick_members=True)     # permission gate on the invoker
async def kick(i: discord.Interaction, member: discord.Member, reason: str = "No reason"):
    if member.top_role >= i.user.top_role: return await i.response.send_message("Role too high.", ephemeral=True)
    await member.kick(reason=reason); await i.response.send_message(f"Kicked {member} ({reason})")

@kick.error
async def kick_err(i, e):
    if isinstance(e, app_commands.MissingPermissions): await i.response.send_message("You lack permission.", ephemeral=True)
    else: raise e

@tasks.loop(minutes=30)
async def housekeeping(): ...                # periodic jobs; start in setup_hook: housekeeping.start()

bot.run(os.environ["DISCORD_TOKEN"])
```
Voice-channel management pattern (join-to-create): on `on_voice_state_update`, if a member joins the "Create" channel, create a channel in the category, move them, and delete the channel when empty. Buttons/menus: subclass `discord.ui.View` with `@discord.ui.button`. Role structure: create roles by script with least-privilege permission bits; never give `administrator` to a bot unless required. Persist per-guild config in SQLite keyed by `guild.id`. Handle `discord.Forbidden` and rate limits gracefully.

## 3. Discord (discord.js)

```js
import { Client, GatewayIntentBits, REST, Routes, SlashCommandBuilder, PermissionFlagsBits } from 'discord.js';
const client = new Client({ intents: [GatewayIntentBits.Guilds] });
const cmds = [new SlashCommandBuilder().setName('ping').setDescription('Latency').toJSON(),
  new SlashCommandBuilder().setName('purge').setDescription('Delete messages').addIntegerOption(o => o.setName('n').setMinValue(1).setMaxValue(100).setRequired(true))
    .setDefaultMemberPermissions(PermissionFlagsBits.ManageMessages).toJSON()];
client.once('ready', async () => {
  await new REST().setToken(process.env.DISCORD_TOKEN).put(Routes.applicationGuildCommands(client.user.id, process.env.GUILD_ID), { body: cmds });
  console.log('ready');
});
client.on('interactionCreate', async i => {
  if (!i.isChatInputCommand()) return;
  if (i.commandName === 'ping') return i.reply({ content: `Pong ${client.ws.ping} ms`, ephemeral: true });
  if (i.commandName === 'purge') { const n = i.options.getInteger('n'); const d = await i.channel.bulkDelete(n, true); return i.reply({ content: `Deleted ${d.size}`, ephemeral: true }); }
});
client.login(process.env.DISCORD_TOKEN);
```

## 4. Telegram

```python
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
async def start(u: Update, c: ContextTypes.DEFAULT_TYPE): await u.message.reply_text("Hi! Send /help")
async def echo(u: Update, c): await u.message.reply_text(u.message.text[:4000])
app = Application.builder().token(os.environ["TELEGRAM_TOKEN"]).build()
app.add_handler(CommandHandler("start", start)); app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
app.run_polling()          # webhooks for production behind HTTPS
```
Inline keyboards: `InlineKeyboardMarkup` + `CallbackQueryHandler`. Restrict admin commands by allow-listing user IDs from env.

## 5. Slack (Bolt)

```python
import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
app = App(token=os.environ["SLACK_BOT_TOKEN"])
@app.command("/hello")
def hello(ack, respond, command): ack(); respond(f"Hi <@{command['user_id']}>")
@app.event("app_mention")
def mention(event, say): say(f"You rang, <@{event['user']}>?")
SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
```

## 6. Cross-platform patterns

- Command registry: one function table, adapters per platform.
- Rate limits: queue outgoing messages, respect `Retry-After`.
- Persistence: SQLite for small bots (guild/user settings, cooldowns, warnings).
- Moderation features: log to a mod-log channel, require confirmation for destructive commands, keep audit entries.
- Permissions: check the invoking user's rights and the bot's rights separately.
- Error handling: catch per-command, reply with a short user-safe message, log the stack trace privately.
- AI features: call a model API or a local model over HTTP (for example an Ollama endpoint), with a timeout, a per-user cooldown, and output length limits; never let model output trigger privileged actions directly.
- Privacy: store the minimum; document what you log.

## 7. Hosting

Small VPS or PaaS, `systemd` unit (`Restart=always`, `EnvironmentFile=/etc/bot.env`), or Docker (`restart: unless-stopped`). Use a virtualenv, pin dependencies (`requirements.txt`), rotate logs, and keep the token out of the repo (`.env` in `.gitignore`, provide `.env.example`).

## 8. Verification

`python -m py_compile bot.py` / `node --check bot.js`; confirm every command has a permission check where needed; walk through the invite URL scopes; list the manual test steps in a test server (each command, a permission-denied case, a restart).
