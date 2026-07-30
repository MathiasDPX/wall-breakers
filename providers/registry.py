from .common import Article
from .lemonde import LeMondeArticle
from .leparisien import LeParisienArticle
from .lesechos import LesEchosArticle
from .letelegramme import LeTelegrammeArticle
from .nytimes import NYTimesArticle
from .theathletic import TheAthleticArticle
from .washingtonpost import WashingtonPostArticle
from .lejdd import JDDArticle
from .lefigaro import FigaroArticle
from .liberation import LiberationArticle
from .lequipe import EquipeArticle
from .ouestfrance import OuestFranceArticle

PROVIDERS = [
    LeParisienArticle,
    LeMondeArticle,
    LeTelegrammeArticle,
    LesEchosArticle,
    TheAthleticArticle,
    NYTimesArticle,
    WashingtonPostArticle,
    JDDArticle,
    FigaroArticle,
    LiberationArticle,
    EquipeArticle,
    OuestFranceArticle,
]

ARTICLES:dict[str, Article] = {provider.SLUG: provider for provider in PROVIDERS}