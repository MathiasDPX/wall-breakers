<div align="center">
<br>
<img src="./static/images/logo.png" alt="Wall Breakers Logo"/>
<hr>

Break news paywalls 

![Test workflow status badge](https://img.shields.io/github/actions/workflow/status/MathiasDPX/wall-breakers/tests.yml?label=tests) ![Test workflow status badge](https://img.shields.io/github/actions/workflow/status/MathiasDPX/wall-breakers/docker-image.yml) ![Last commit badge](https://img.shields.io/github/last-commit/MathiasDPX/wall-breakers)
</div>

## Supported medias

- [Le Monde](https://www.lemonde.fr/)
- [Le Parisien](https://www.leparisien.fr/)
- [Le Télégramme](https://www.letelegramme.fr/)

## Deployment

You can run Wall Breakers with Docker and docker-compose.yml

```bash
docker run -p 8000:8000 ghcr.io/mathiasdpx/wall-breakers:latest
```

## Development

```bash
# Run wall-breakers (venv recommended)
pip install -r requirements.txt
python main.py

# Run tests
pytest
```