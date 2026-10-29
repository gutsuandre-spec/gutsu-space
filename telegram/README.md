# Telegram channel control

Channel: @gutsuspace

This repository contains an Actions workflow that can execute commands against the channel without exposing the Telegram bot token to ChatGPT or to the repository.

Required repository secret:
- TELEGRAM_BOT_TOKEN

The bot must be an administrator of @gutsuspace.

Supported command.json operations:
- send
- edit
- delete
- pin
- send_photo

The command file is changed only when a channel action is requested.

## Client data boundary

`lead-tracker.csv` is a legacy empty header, not a place to store contacts or live requests. The repository is public. Store real leads, correspondence, attachments and prices only in the private Radar state outside Git. The security check rejects populated tracker rows; Pages publishes only the explicit `dist` bundle and never this directory. Do not put credentials into command files: keep the existing GitHub Secret mechanism.
