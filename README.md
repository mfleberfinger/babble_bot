# babble_bot

it's that babble boy

[best of.](https://docs.google.com/document/d/1UiTHk2Z7wy-_rXSBy8YJ_N2CqeXsEROLD5NXcvXYd8A/edit?usp=sharing)

## Running

Translation uses [Argos Translate](https://github.com/argosopentech/argos-translate) offline. Official language packages are several GB and live in `argos_packages/` (gitignored).

### Local

1. `git clone https://github.com/mfleberfinger/babble_bot && cd babble_bot`
1. Get a Telegram Bot API Key by making a new bot using Telegram's BotFather.
1. Rename the config example to `babble_bot.cfg` and copy in your API key.
1. Install dependencies and download language packages:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   pip install --no-deps argostranslate==1.11.0
   python3 download_argos_packages.py
   ```
1. `python3 babble_bot.py`

### Docker

Language packages stay on the host in `argos_packages/` and are bind-mounted into the container. Populate that folder first (see Local above). The image does not contain the packages.

The bot API key is not copied into the image. Pass it only when you start the container, as the `TELEGRAM_TOKEN` environment variable. Do not pass it as a build argument.

1. `git clone https://github.com/mfleberfinger/babble_bot && cd babble_bot`
1. Get a Telegram Bot API Key by making a new bot using Telegram's BotFather.
1. Build the Docker image:
   ```bash
   docker build -t babble-bot .
   ```
1. Run the Docker image, passing the key and mounting the host packages directory:
   ```bash
   docker run -it \
     -e TELEGRAM_TOKEN="your-telegram-bot-api-key" \
     -v "$PWD/argos_packages:/root/argos_packages:ro" \
     babble-bot
   ```
   For convenience, a script, like `run.sh`, in this directory, can be used.
