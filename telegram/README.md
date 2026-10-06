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
