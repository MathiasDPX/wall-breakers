import base64
import re
from html import escape

import demjson3
import requests

from .common import Article, add_figure

_URL_ID_PATTERN = re.compile(r"https:\/\/(?:www\.)?nytimes\.com(\/.+\.html)")

_PAGE_DATA_PATTERN = re.compile(r"<script>window.__preloadedData = ({.+});<\/script>")

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:153.0) Gecko/20100101 Firefox/153.0",
    "Host": "www.nytimes.com",
}

_COOKIES = {
    "datadome": "", # TODO: find a fix for datadome cookie
}


class DataDomeCookieExpiredError(RuntimeError):
    pass


def _build_inline(inline):
    content = escape(inline.get("text", ""))

    for text_format in inline.get("formats", []):
        typename = text_format["__typename"]

        if typename == "LinkFormat":
            url = escape(text_format.get("url", ""), quote=True)
            id = NYTimesArticle.get_id_from_url(url)
            if id != None:
                url = f"/{NYTimesArticle.SLUG}/{id}"
                
            title = text_format.get("title")
            title = f' title="{escape(title, quote=True)}"' if title else ""
            content = f'<a target="_blank" href="{url}"{title}>{content}</a>'
        elif typename in ("BoldFormat", "StrongFormat"):
            content = f"<strong>{content}</strong>"
        elif typename in ("ItalicFormat", "EmphasisFormat"):
            content = f"<em>{content}</em>"
        elif typename == "UnderlineFormat":
            content = f"<u>{content}</u>"

    return content


def _build_content(content):
    return "".join(
        _build_inline(item)
        if item.get("__typename") == "TextInline"
        else _build_block(item)
        for item in content or []
    )


def _get_image_url(media):
    crops = media.get("crops") or []
    renditions = crops[0].get("renditions") if crops else []
    return renditions[-1].get("url") if renditions else media.get("url")


def _build_image(media):
    if not media:
        return ""

    url = _get_image_url(media)
    if not url:
        return ""

    caption = media.get("caption") or {}
    if isinstance(caption, dict):
        caption = caption.get("text", "")

    return add_figure(
        escape(url, quote=True),
        caption=escape(media.get("credit", ""), quote=True),
        title=escape(caption),
    )


def _build_block(block):
    if not block:
        return ""

    typename = block["__typename"]
    
    if typename == "Heading1Block":
        return f"<h1>{_build_content(block.get('content'))}</h1>"
    elif typename == "Heading2Block":
        return f"<h2>{_build_content(block.get('content'))}</h2>"
    elif typename in ("ParagraphBlock", "SummaryBlock"):
        return f"<p>{_build_content(block.get('content'))}</p>"
    elif typename == "TextOnlyDocumentBlock":
        return _build_content(block.get("content"))
    elif typename == "ListItemBlock":
        return f"<li>{_build_content(block.get('content'))}</li>"
    elif typename == "ListBlock":
        style = str(
            block.get("listType")
            or block.get("listStyle")
            or block.get("style")
            or block.get("type")
            or ""
        ).upper()
        tag = "ul" if "UNORDERED" in style else "ol"
        items = block.get("items") or block.get("content") or []
        content = "".join(
            _build_block(item)
            if item.get("__typename") == "ListItemBlock"
            else f"<li>{_build_block(item)}</li>"
            for item in items
        )
        return f"<{tag}>{content}</{tag}>"
    elif typename == "GridBlock":
        content = "".join(_build_image(media) for media in block.get("gridMedia", []))
        caption = block.get("caption") or ""
        if isinstance(caption, dict):
            caption = caption.get("text", "")
        caption = f"<figcaption>{escape(caption)}</figcaption>" if caption else ""
        return f'<div class="gallery">{content}{caption}</div>'
    elif typename == "ImageBlock":
        return _build_image(block.get("media"))
    elif typename == "InteractiveBlock":
        interactive = block.get("media") or block
        html = interactive.get("html") or interactive.get("embedCode")
        if html:
            return f'<div class="interactive">{html}</div>'

        url = interactive.get("url")
        if url:
            return (
                '<iframe class="interactive" '
                f'src="{escape(url, quote=True)}" loading="lazy"></iframe>'
            )

    return None


class NYTimesArticle(Article):
    SLUG = "nyt"
    PROVIDER = "New York Times"

    def __init__(self, article_id: str):
        data = NYTimesArticle.get_data(article_id)

        report = []
        content = ""
        for block in data["sprinkledBody"]["content"]:
            built = _build_block(block)
            if built == None:
                report.append(f"- Unhandled `{block['__typename']}` block")
            else:
                content += built

        report = list(set(report))
        image = data["promotionalImage"]["socialMediaRendition"]["rendition"]["url"]
        caption = " &copy; ".join(filter(None, [((data["promotionalImage"]["image"].get("caption") or {}).get("text") or "").strip(), (data["promotionalImage"]["image"].get("credit") or "").strip()]))
        content = add_figure(image, caption) + content
        content = "<!--\n" + "\n".join(report) + "\n-->" + content

        super().__init__(
            id=article_id,
            headline=data["headline"]["default"],
            subheadline=data["summary"],
            content=content,
            url=data["url"],
            image=image
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
    
    def get_data(id):
        article_path = base64.b64decode(id).decode()
        r = requests.get(
            f"https://www.nytimes.com{article_path}", headers=_HEADERS, cookies=_COOKIES
        )
        if r.status_code == 403:
            raise DataDomeCookieExpiredError("The New York Times DataDome cookie has expired")
        r.raise_for_status()
        return NYTimesArticle._get_data(r.content.decode())["initialData"]["data"]["article"]


if __name__ == "__main__":
    article = NYTimesArticle.get_from_url(
        "https://www.nytimes.com/2026/07/25/opinion/boy-scouts-girls-gender.html"
    )

    print(article)
