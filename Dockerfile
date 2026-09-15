FROM python:3.12

# Set up Python
RUN pip3 install --upgrade pip
COPY ./requirements.txt ./requirements.txt
# argostranslate's PyPI metadata depends on stanza/torch; skip those extras.
RUN pip3 install --no-deps argostranslate==1.11.0 && pip3 install -r requirements.txt

WORKDIR /root
COPY ./argos_setup.py ./argos_setup.py
COPY ./babble_bot.cfg ./babble_bot.cfg
COPY ./babble_bot.py ./babble_bot.py
COPY ./mangle.py ./mangle.py

# Language packages live on the host and must be bind-mounted at
# /root/argos_packages (see README). Do not COPY them into the image.
CMD ["python3", "babble_bot.py"]
