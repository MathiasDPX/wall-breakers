# Deployment

**All** environment variables are optional for a minimal running environment

```bash
docker run -p 8000:8000 \
  ghcr.io/mathiasdpx/wall-breakers:latest
```

## Sentry

You can enable Sentry with the `SENTRY_ENVIRONMENT` and `SENTRY_DSN` environments variables.

## Ouest-France

Ouest-France requires you to have an account with an active subscriptions. Set `OUESTFRANCE_REFRESH_TOKEN` to your refresh token and make sure you have the correct `OUESTFRANCE_AZP` (default is `bms-sso-login`, verify on jwt.io)

## Mediapart

🤫 You need to create an account on the [Pierre Vives library](https://mediatheque-departementale.herault.fr/mediatheque-numerique/nos-ressources/lire/mediapart) and set `PIERREVIVES_USERNAME` and `PIERREVIVES_PASSWORD`

<br>
<br>

# Development

## Run

The `DEBUG` env variable enable Flask built-in debugger and the debug section under the subheadline

```bash
# Run wall-breakers (venv recommended)
pip install -r requirements.txt
DEBUG="true"
python main.py
```

```bash
# Run tests
pytest
```

## Add a media

1. Create a file in `providers/` named after your media (take examples on others medias)
2. Add your media in `providers/registry.py`
3. Write tests in `tests/`
4. Add it everywhere (`templates/index.html`, `README.md`, `static/openapi.yml`, `static/userscript.js`)
5. Make a PR!
