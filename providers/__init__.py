from .common import Article
from .lemonde import LeMondeArticle
from .leparisien import LeParisienArticle
from .lesechos import LesEchosArticle
from .letelegramme import LeTelegrammeArticle
from .nytimes import NYTimesArticle
from .theathletic import TheAthleticArticle
from .washingtonpost import WashingtonPostArticle
from .lejdd import JDDArticle

PROVIDERS = [
    LeParisienArticle,
    LeMondeArticle,
    LeTelegrammeArticle,
    LesEchosArticle,
    TheAthleticArticle,
    NYTimesArticle,
    WashingtonPostArticle,
    JDDArticle,
]

ARTICLES:dict[str, Article] = {provider.SLUG: provider for provider in PROVIDERS}