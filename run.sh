docker run -it -e TELEGRAM_TOKEN="$(cat ../babble_key.txt)" -v "$PWD/argos_packages:/root/argos_packages:ro" babble-bot
