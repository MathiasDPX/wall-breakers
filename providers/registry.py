from .actufr import ActuArticle
from .charentelibre import CharenteLibreArticle
from .common import Article
from .courrierinternational import CourrierInternationalArticle
from .lefigaro import FigaroArticle
from .lejdc import JDCArticle
from .lejdd import JDDArticle
from .lemonde import LeMondeArticle
from .leparisien import LeParisienArticle
from .lequipe import EquipeArticle
from .lesechos import LesEchosArticle
from .letelegramme import LeTelegrammeArticle
from .lexpress import ExpressArticle
from .liberation import LiberationArticle
from .mediapart import MediapartArticle
from .nouvelobs import NouvelObsArticle
from .nytimes import NYTimesArticle
from .ouestfrance import OuestFranceArticle
from .parismatch import ParisMatchArticle
from .telerama import TeleramaArticle
from .theathletic import TheAthleticArticle
from .washingtonpost import WashingtonPostArticle
from .financialtimes import FinancialTimesArticle
from .nikkei_asia import NikkeiAsiaArticle

PROVIDERS:list[Article] = [
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
    CourrierInternationalArticle,
    MediapartArticle,
    ActuArticle,
    CharenteLibreArticle,
    ExpressArticle,
    ParisMatchArticle,
    NouvelObsArticle,
    TeleramaArticle,
    JDCArticle,
    FinancialTimesArticle,
    NikkeiAsiaArticle,
]

ARTICLES:dict[str, Article] = {provider.SLUG: provider for provider in PROVIDERS}