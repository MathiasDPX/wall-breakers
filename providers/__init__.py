from .leparisien import LeParisienArticle
from .lemonde import LeMondeArticle
from .letelegramme import LeTelegrammeArticle
from .lesechos import LesEchosArticle
from .theathletic import TheAthleticArticle
from .common import Article

PROVIDERS = [
    LeParisienArticle,
    LeMondeArticle,
    LeTelegrammeArticle,
    LesEchosArticle,
    TheAthleticArticle
]

ARTICLES:dict[str, Article] = {provider.SLUG: provider for provider in PROVIDERS}