# Mijn Decos Join API

## Introduction

A REST API which discloses the decos-join data


### Requirements

- Access to Rattic

### Local development

1. Clone repo and `cd` in
2. Create a virtual env and activate
3. Run `pip install -r decosjoin/requirements.txt`
4. Set environment variables:
   - `export FLASK_APP=decosjoin/api/server.py`
   - `export TMA_CERTIFICATE=<path to certificate>`
      - TMA certificate to decode the saml token (rattic: "TMA certificaat local")
        (you can put this line in your shell rc file)
    
5. Run `flask run`

### Deployment

1. Make sure the env vars described in 'Local development' are set
3. Run `docker-compose up --build`
4. Get '/status/health' to check if the API is up and running

### Testing

1. Clone repo
2. Create a virtual env and activate
3. Run `pip install -r decosjoin/requirements.txt`
4. `cd decosjoin`
5. Run `python -m unittest`
