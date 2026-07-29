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
- [L'Équipe](https://www.lequipe.fr/)
- [Washington Post](https://www.washingtonpost.com)
- [New York Times](https://www.nytimes.com/)
- [Le JDD](https://www.lejdd.fr/)
- [Les Echos](https://www.lesechos.fr/)
- [The Athletic](https://www.nytimes.com/athletic/)

## Deployment

You can run Wall Breakers with Docker and docker-compose.yml

```bash
docker run -p 8000:8000 ghcr.io/mathiasdpx/wall-breakers:latest
```

```bash
docker run -p 8000:8000 \
  ghcr.io/mathiasdpx/wall-breakers:latest
```

It supports Sentry with the `SENTRY_ENVIRONMENT` and `SENTRY_DSN` environment variable but both are optional.

## API

API Documentation is in [`static/openapi.yml`](./static/openapi.yml) or [`http://localhost:5000/openapi.yml`](http://localhost:5000/openapi.yml)

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
3. Write tests in `tests/test_common.py`
4. Add it to the list of supported medias in `templates/index.html`
5. Add it to the README
6. Add it to `static/openapi.yml`
7. Make a PR!
