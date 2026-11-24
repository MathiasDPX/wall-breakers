import re

import requests

from .common import Article, add_figure
from metrics import upstream_request_timer

_URL_ID_PATTERN = re.compile(
    r"https:\/\/www\.capital\.bg\/.+\/.+\/\d{4}\/\d{2}\/\d{2}\/(\d+)_.+\/"
)

def _build_segment(segment):
    words = []
    for word in segment.get("words", []):
        words.append(word.get("text", ""))
    
    return " ".join(words)

class CapitalArticle(Article):
    SLUG = "cap"
    PROVIDER = "Capital"
    FAVICON = "https://beyondwordsneproduction.blob.core.windows.net/production/public-upload/2026-04-30/f13b1f6c-e9b0-4fbd-87d8-327445e44cd3-logo%20(4).png"
    
    def __init__(self, article_id: str):
        data = CapitalArticle.get_data(article_id)
        
        content = data["content"][0]
        
        segments = content["segments"]
        subheadline = segments[1]
        segments = segments[2:]
        
        text = "".join(f"<p>{_build_segment(segment)}</p>" for segment in segments)
        
        image = content.get("image_url", "")
        audio = content["audio"][-1]["url"]
        
        text = add_figure(image) + f'<audio src="{audio}" controls></audio>' + text

        super().__init__(
            id=article_id,
            headline=content.get("title"),
            subheadline=_build_segment(subheadline),
            content=text,
            url="https://www.capital.bg/"+str(article_id),
            image=image,
            publication_date=None
        )
    
    def get_id_from_url(url: str):
        match = _URL_ID_PATTERN.search(url)
        if match is not None:
            return match.group(1)
        
        return None
    
    @classmethod
    @upstream_request_timer
    def get_data(cls, id):
        r = requests.get(
            f"https://api.beyondwords.io/v1/projects/47343/player/by_source_id/{id}?words=true",
            timeout=30
        )
        r.raise_for_status()
        return r.json()


if __name__ == "__main__":
    article = CapitalArticle.get_from_url("https://www.capital.bg/politika_i_ikonomika/bulgaria/2026/11/24/4983801_koaliciiata_zad_prevrata_sreshtu_blagomir_kocev/")

    print(article)
