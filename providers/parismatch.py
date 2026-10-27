import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from .exceptions import sentry_block_error
from .common import Article, add_figure, fix_links, make_figcaption
from metrics import upstream_request_timer

_URL_ID_PATTERN = re.compile(
    r"https:\/\/www\.parismatch\.com\/.+-([A-Za-z0-9]+)"
)


def _sanitize_html(html):
    soup = BeautifulSoup(html, features="html.parser")

    fix_links(soup)

    return soup.decode_contents()


def _build_block(block):
    typename = block["nodeType"]

    if typename == "paragraph":
        return "<p>" + _build_blocks(block["content"]) + "</p>"
    elif typename == "hyperlink":
        return f'<a href="{block["data"]["uri"]}">{_build_blocks(block["content"])}</a>'
    elif typename == "entry-hyperlink":
        # hyperlink to a PM article
        uid = block['data']['target']['sys']['id']
        return f'<a href="/{ParisMatchArticle.SLUG}/{uid}">{_build_blocks(block["content"])}</a>'
    elif typename == "heading-2":
        return "<h2>" + _build_blocks(block["content"]) + "</h2>"
    elif typename == "blockquote":
        template = block["data"]["template"]
        if template == "related-articles":
            return ""
        return "<blockquote>" + _build_blocks(block["content"]) + "</blockquote>"
    elif typename == "hr":
        return "<hr>"
    elif typename == "text":
        return block['value']
        
    sentry_block_error(typename)

    return ""

def _build_blocks(blocks):
    return "".join(_build_block(block) for block in blocks)


class ParisMatchArticle(Article):
    SLUG = "pm"
    PROVIDER = "Paris Match"
    FAVICON = "https://www.parismatch.com/apple-touch-icon.png"

    def __init__(self, article_id: str):
        data = ParisMatchArticle.get_data(article_id)

        image = data.get("featuredImage", {})

        if image:
            content = add_figure(image.get("externalUrl"), make_figcaption(image.get("caption"), image.get("credits")))
        else:
            content = ""
            
        content += _build_blocks(data["body"]["json"]["content"])

        published_at = data["sys"].get("publishedAt")

        super().__init__(
            id=article_id,
            headline=data["title"],
            subheadline=data["introducing"],
            content=content,
            url="https://www.parismatch.com"+data["slug"],
            image=image.get("externalUrl", ""),
            publication_date=datetime.fromisoformat(published_at) if published_at else None
        )

    def get_id_from_url(url: str):
        match = _URL_ID_PATTERN.search(url)
        if match is None:
            return None

        return match.group(1)
    
    @classmethod
    @upstream_request_timer
    def get_data(cls, id):
        query = {
            "operationName": "GetArticleByIdQuery",
            "variables": {"id": id},
            "query": "query GetArticleByIdQuery($id: String!) { articleCollection(limit: 1, where: { sys: { id: $id }  } ) { items { __typename ...ArticleContentFieldsFragment } } }  fragment ArticleCategoryFieldsFragment on Category { name slug sys { id } }  fragment ArticlesMediaFieldsFragment on Media { media { url contentType height width } caption credits externalId externalUrl mediaType focalPoint framing sys { id } }  fragment ArticleAuthorFieldsFragment on Author { fullName slug photo { url } sys { id } }  fragment ArticlesListFieldsFragment on Article { slug title templateType estimatedReadingTime mainCategory { __typename ...ArticleCategoryFieldsFragment } featuredMediasCollection(limit: 4) { total items { __typename ...ArticlesMediaFieldsFragment } } featuredImage { __typename ...ArticlesMediaFieldsFragment } isPremium isSponsored sponsorName publishedAt updatedAt sys { id publishedAt firstPublishedAt } }  fragment ArticleContentMediaFieldsFragment on Media { altOverride caption credits media { url title description contentType fileName size width height } externalId externalUrl focalPoint framing sys { id } }  fragment ArticleBodyFieldsFragment on ArticleBody { json links { assets { block { url description __typename sys { id } } } entries { hyperlink { __typename ... on Article { __typename ...ArticlesListFieldsFragment } ... on Tag { __typename sys { id } tagType tagName } ... on Category { __typename ...ArticleCategoryFieldsFragment } } inline { __typename ... on Tag { tagName featuredImage { url } __typename sys { id } } ... on TechnicalFile { __typename artifactType sys { id } } ... on Article { __typename ...ArticlesListFieldsFragment } } block { __typename ... on Media { __typename ...ArticleContentMediaFieldsFragment } } } } }  fragment ArticleContentFieldsFragment on Article { title introducing slug drupalSlug isPremium defaultPaywallPercentage templateType estimatedReadingTime mainCategory { __typename ...ArticleCategoryFieldsFragment } secondaryCategory { __typename ...ArticleCategoryFieldsFragment } featuredImage { __typename ...ArticlesMediaFieldsFragment } featuredMediasCollection { items { __typename ...ArticlesMediaFieldsFragment } } authorGroups authorsCollection(limit: 10) { items { __typename ...ArticleAuthorFieldsFragment } } relatedArticlesCollection(limit: 5) { items { __typename ...ArticlesListFieldsFragment } } body { __typename ...ArticleBodyFieldsFragment } tagEditoCollection(limit: 20) { items { tagName featuredImage { url } __typename sys { id } } } publishedAt updatedAt sys { firstPublishedAt publishedAt id } }",
        }
        
        headers = {
            "Authorization": "Bearer intz0VmdRbcy-Ivsx-NJA7Ld1-Y_U8HO_Jd7Ur6NXko" # mobile app api key
        }
        
        r = requests.post("https://graphql.contentful.com/content/v1/spaces/iatfclnjf6rx/environments/master", json=query, headers=headers)
        r.raise_for_status()
        return r.json()["data"]["articleCollection"]["items"][0]


if __name__ == "__main__":
    article = ParisMatchArticle.get_from_url(
        "https://www.parismatch.com/victoire-inattendue-mais-pas-impossible-francois-hollande-veut-jouer-comme-lula-81s2PoClueev55WQxfMbZ"
    )

    print(article)
