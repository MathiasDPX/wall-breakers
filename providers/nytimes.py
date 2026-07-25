from .common import Article, add_figure
import demjson3
import base64
import re
import requests

_URL_ID_PATTERN = re.compile(r"https:\/\/(?:www\.)?nytimes\.com(\/.+\.html)")

_PAGE_DATA_PATTERN = re.compile(r"<script>window.__preloadedData = ({.+});<\/script>")

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:153.0) Gecko/20100101 Firefox/153.0",
    "Host": "www.nytimes.com",
}

_COOKIES = {
    "nyt-gdpr": "1",
    "NYT-Edition": "edition|INTERNATIONAL",
    "nyt-a": "8uyH55SxV5FQmPnTzAE7ZX",
    "datadome": "N7J4r0MM81cG2juz6uQ9AJtX9Gs17wlliVxRL76Elv3VjZIx8MuWHQ2X0dp61OGyIPnETsGIKc8XEbwYkM6eas2nTGA1qMWDs65d06lZ3wfFOaVkeBgIXH7JFdy7C~Ok",
}


class NYTimes(Article):
    SLUG = "nyt"
    PROVIDER = "New York Times"

    def __init__(self, article_id: str):
        article_path = base64.b64decode(article_id).decode()
        r = requests.get(
            f"https://www.nytimes.com{article_path}", headers=_HEADERS, cookies=_COOKIES
        )
        r.raise_for_status()
        data = NYTimes._get_data(r.content.decode())["initialData"]["data"]["article"]

        content = ""
        report = []
        
        # TODO:
        # - ListBlock
        # - InteractiveBlock
        # - Support more ParagraphBlock formats
        # - Recursive function (ListBlock contains ParagraphBlock inside them)
        for block in data["sprinkledBody"]["content"]:
            typename = block["__typename"]

            if typename == "HeaderBasicBlock":
                content += f"<h1>{block['label']['content'][0]['text']}</h1>"
            elif typename == "Heading2Block":
                content += f"<h2>{block['content'][0]['text']}</h2>"
            elif typename == "ParagraphBlock":
                content += "<p>"
                
                for subblock in block['content']:
                    subcontent = subblock['text']
                    
                    for format in subblock['formats']:
                        format_typename = format['__typename']
                        
                        if format_typename == "LinkFormat":
                            title = f' title="{format['title']}"' if format['title'] else ""
                            subcontent = f'<a href="{format['url']}{title}">{subcontent}</a>'
                        else:
                            report.append(f"Unhandled ParagraphBlock format `{format_typename}`")
                    
                    content += subcontent
                
                content += "</p>"
            elif typename == "GridBlock":
                content += '<div class="gallery">'
                
                medias = block["gridMedia"]
                for media in medias:
                    content += add_figure(
                        media["crops"][0]["renditions"][-1]["url"],
                        title=media["caption"]["text"]
                    )
                    
                content += f"<figcaption>{block["caption"]}</figcaption>"
                content += "</div>"
            elif typename == "ImageBlock":
                media = block["media"]
                content += add_figure(
                    media["crops"][0]["renditions"][-1]["url"],
                    media["caption"]["text"]
                )
            elif typename not in ["Dropzone", "DetailBlock", "RelatedLinksBlock", "HeaderFullBleedHorizontalBlock"]:
                report.append(f"Unhandled block `{typename}`")

        if report:
            content = "<!--\n" + "\n".join(report) + "\n-->" + content

        super().__init__(
            id=article_id,
            headline=data["headline"]["default"],
            subheadline=data["summary"],
            content=content,
            url=data["url"],
            image=data["promotionalImage"]["socialMediaRendition"]["rendition"]["url"],
        )

    def get_id_from_url(url: str):
        match = _URL_ID_PATTERN.search(url)
        if match is None:
            return None

        return base64.b64encode(match.group(1).encode()).decode("ascii")

    def _get_data(content):
        match = _PAGE_DATA_PATTERN.search(content)
        if match is None:
            return None

        return demjson3.decode(match.group(1))


if __name__ == "__main__":
    article = NYTimes.get_from_url(
        "https://www.nytimes.com/2026/07/25/opinion/boy-scouts-girls-gender.html"
    )

    print(article)
