from .leparisien import LeParisienArticle
from .lemonde import LeMondeArticle
from .letelegramme import LeTelegrammeArticle
from .lesechos import LesEchosArticle
from .theathletic import TheAthleticArticle

PROVIDERS = [
    LeParisienArticle,
    LeMondeArticle,
    LeTelegrammeArticle,
    LesEchosArticle,
    TheAthleticArticle
]

ARTICLES = {provider.SLUG: provider for provider in PROVIDERS}