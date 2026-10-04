import unicodedata

from .actufr import ActuArticle
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
from .scienceetvie import ScienceEtVieArticle
from .telerama import TeleramaArticle
from .theathletic import TheAthleticArticle
from .washingtonpost import WashingtonPostArticle
from .financialtimes import FinancialTimesArticle
from .nikkei_asia import NikkeiAsiaArticle
from .scmp import SCMPArticle
from .gsoi import CharenteLibreArticle, SudOuestArticle, RepubliquePyreneesArticle
from .ebra import AlsaceArticle, BienPublicArticle, DaupineArticle, DNAArticle, EstRepuArticle, ProgresArticle, JSLArticle, RepuLorrainArticle, VosgesMatinArticle
from .canardenchaine import CanardEnchaineArticle
from .charliehebdo import CharlieHebdoArticle
from .lequipe_video import EquipeVideoArticle
from .socialter import SocialterArticle
from .rossel import VDNArticle, LeMessagerArticle, LeSoirArticle, NordLittArticle, ParisNormandieArticle, SudInfoArticle, CourrierPicardArticle, AisneNouvelleArticle, ArdennaisArticle, EstEclairArticle, LibChampagneArticle, UnionArticle

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
    SCMPArticle,
    JSLArticle,
    DNAArticle,
    AlsaceArticle,
    BienPublicArticle,
    DaupineArticle,
    EstRepuArticle,
    VosgesMatinArticle,
    ProgresArticle,
    RepuLorrainArticle,
    CanardEnchaineArticle,
    CharlieHebdoArticle,
    EquipeVideoArticle,
    ScienceEtVieArticle,
    SudOuestArticle,
    RepubliquePyreneesArticle,
    SocialterArticle,
    VDNArticle,
    LeMessagerArticle,
    LeSoirArticle,
    NordLittArticle,
    ParisNormandieArticle,
    SudInfoArticle,
    CourrierPicardArticle,
    AisneNouvelleArticle,
    ArdennaisArticle,
    EstEclairArticle,
    LibChampagneArticle,
    UnionArticle
]

ARTICLES:dict[str, Article] = {provider.SLUG: provider for provider in PROVIDERS}


def _sort_key(name: str) -> str:
    """Sort key ignoring case and accents, so "Les Echos" sorts next to "Le Monde"."""
    folded = unicodedata.normalize("NFKD", name)

    return "".join(char for char in folded if not unicodedata.combining(char)).lower()


def get_sources() -> list[dict]:
    """Build the list of sources to advertise, sorted by name.

    Providers with LISTED = False are left out. Providers sharing a GROUP are
    merged into a single entry named after the group.
    """
    listed = [provider for provider in PROVIDERS if provider.LISTED]

    sources = []
    grouped = set()

    for provider in listed:
        if provider.GROUP is None:
            sources.append({
                "name": provider.PROVIDER,
                "members": None,
                "enabled": provider.is_enabled(),
            })
        elif provider.GROUP not in grouped:
            grouped.add(provider.GROUP)
            members = [p for p in listed if p.GROUP == provider.GROUP]
            sources.append({
                "name": provider.GROUP,
                "members": sorted((p.PROVIDER for p in members), key=_sort_key),
                "enabled": all(p.is_enabled() for p in members),
            })

    return sorted(sources, key=lambda source: _sort_key(source["name"]))
