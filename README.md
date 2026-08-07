<div align="center">
<br>
<img src="./static/images/logo.png" alt="Wall Breakers Logo"/>
<hr>

![Test workflow status badge](https://img.shields.io/github/actions/workflow/status/MathiasDPX/wall-breakers/tests.yml?label=tests) ![Test workflow status badge](https://img.shields.io/github/actions/workflow/status/MathiasDPX/wall-breakers/docker-image.yml) ![Last commit badge](https://img.shields.io/github/last-commit/MathiasDPX/wall-breakers)
</div>

## Supported medias

- [Le Monde](https://www.lemonde.fr/)
- [Le Parisien](https://www.leparisien.fr/)
- [Le Figaro](https://www.lefigaro.fr/)
- [Le Télégramme](https://www.letelegramme.fr/)
- [Libération](https://www.liberation.fr/)
- [Mediapart](https://www.mediapart.fr/)
- [Actu.fr](https://actu.fr/)
- [Charente Libre](https://www.charentelibre.fr/)
- [Paris Match](https://www.parismatch.com/)
- [L'Équipe](https://www.lequipe.fr/)
- [L'Express](https://www.lexpress.fr/)
- [Washington Post](https://www.washingtonpost.com)
- [Le JDD](https://www.lejdd.fr/)
- [Les Echos](https://www.lesechos.fr/)
- [Ouest-France](https://www.ouest-france.fr/)
- [Le Nouvel Obs](https://www.nouvelobs.com/)
- [Télérama](https://www.telerama.fr/)
- [Courrier International](https://www.courrierinternational.com/)
- [The Athletic](https://www.nytimes.com/athletic/)
<!-- - [New York Times](https://www.nytimes.com/)-->

## Userscript

A userscript that displays a banner at the top of compatible websites, with a redirect to Wall Breakers, is available at [`https://news.mathiasd.fr/redirect.user.js`](https://news.mathiasd.fr/redirect.user.js) or [`static/userscript.js`](./static/userscript.js). It is compatible with Tampermonkey and Greasemonkey


## API

API Documentation is in [`static/openapi.yml`](./static/openapi.yml) or [`https://news.mathiasd.fr/openapi.yml`](https://news.mathiasd.fr/openapi.yml)

## Deployment

You can run Wall Breakers with Docker or docker-compose.yml

```bash
docker run -p 8000:8000 \
  ghcr.io/mathiasdpx/wall-breakers:latest
```

It supports Sentry with the `SENTRY_ENVIRONMENT` and `SENTRY_DSN` environments variables but both are optional.

## Development

```bash
# Run wall-breakers (venv recommended)
pip install -r requirements.txt
DEBUG="true"
python main.py

# Run tests
pytest
```

### Add a media

1. Create a file in `providers/` named after your media (take examples on others medias)
2. Add your media in `providers/registry.py`
3. Write tests in `tests/`
4. Add it everywhere (`templates/index.html`, `README.md`, `static/openapi.yml`, `static/userscript.js`)
5. Make a PR!
