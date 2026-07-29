import json
import re

import requests
from bs4 import BeautifulSoup

from .common import Article, add_figure

_URL_ID_PATTERN = re.compile(
    r".+nytimes\.com\/athletic\/(\d+)(?:\/(?:.+)?)?"
)

_METADATA_PATTERN = re.compile(
    r'<script type="application\/ld\+json">({.+})<\/script>'
)

_DATA_PATTERN = re.compile(
    r'<script id="__NEXT_DATA__" type="application\/json">({.+})<\/script>'
)


class TheAthleticArticle(Article):
    SLUG = "ta"
    PROVIDER = "The Athletic"
    
    def __init__(self, article_id: str):
        r = requests.get(
            f"https://www.nytimes.com/athletic/{article_id}"
        )
        r.raise_for_status()
        content = r.text
        
        match = _METADATA_PATTERN.search(content)
        if match is None:
            raise Exception("Article metadata not found")
        metadata = json.loads(match.group(1))
        
        match = _DATA_PATTERN.search(content)
        if match is None:
            raise Exception("Article data not found")
        data = json.loads(match.group(1))
        
        soup = BeautifulSoup(data["props"]["pageProps"]["article"]["article_body_desktop"], features="html.parser")
        
        for container in soup.select("div#inline-graphic, div.ad-container, hr"):
            container.decompose()
            
        for caption in soup.select("div.wp-caption"):
            img = caption.find("img")
            if not img:
                continue
                
            text = caption.select_one(".credits-text").get_text(strip=True) if caption.select_one(".credits-text") else None
            url = img.get("src")

            caption.replace_with(BeautifulSoup(add_figure(url, text), "html.parser"))
        
        for a in soup.find_all("a", href=True):
            a["target"] = "_blank"
            
            # Decode article URLs
            if "https://www.nytimes.com/athletic/" in a["href"]:
                id = TheAthleticArticle.get_id_from_url(a["href"])
                if id != None:
                    a["href"] = f"/{self.SLUG}/{id}"
        
        content = soup.decode_contents()
        
        image = metadata["image"][0]
        
        content = add_figure(image["url"], image["caption"]+" &copy; "+image['creditText']) + content

        super().__init__(
            id=article_id,
            headline=metadata["headline"],
            subheadline=metadata["description"],
            content=content,
            url=metadata["@id"],
            image=image["url"]
        )
    
    def get_id_from_url(url: str):
        match = _URL_ID_PATTERN.search(url)
        if match is None:
            return None

        return match.group(1)


if __name__ == "__main__":
    article = TheAthleticArticle.get_from_url("https://www.nytimes.com/athletic/7444334/2026/07/16/gianni-infantino-fifa-president-future/")

    print(article)
