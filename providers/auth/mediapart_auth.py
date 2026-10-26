import json
import logging
import os
import re
import threading
import time
from pathlib import Path
from secrets import token_hex

import requests
from bs4 import BeautifulSoup

from providers.exceptions import (
    MediapartInvalidLogin,
    MediapartRegistrationError,
    MediapartThrottledException,
)

logger = logging.getLogger(__name__)

BASE_URL = "https://abo.mediapart.fr"
ENTRY_URL = f"{BASE_URL}/abonnement/parrainage?xtor=EPR-1030-[activation-filleul]"
ONBOARDING_URL = f"{BASE_URL}/onboarding"

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:158.0) Gecko/20100101 Firefox/158.0"

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Upgrade-Insecure-Requests": "1",
}

TIMEOUT = (3.05, 20)

# 1 month
TRIAL_SECONDS = 30 * 24 * 60 * 60

PASSWORD = "P@ssword1234"

REFRESH_INTERVAL = 24 * 60 * 60
COOLDOWN_SECONDS = 15 * 60
MAX_COOLDOWN_SECONDS = 6 * 60 * 60

USER_ID_PATTERNS = (
    # abo.mediapart.fr
    re.compile(r"window\.mediapart\.user\.uid\s*=\s*(\d+)"),
    # www.mediapart.fr, where the user is part of the global state object
    re.compile(r"window\.mediapart\s*=\s*\{.*?\buid\s*:\s*(\d+)", re.DOTALL),
)


def read_json(path):
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(path.name + ".tmp")

    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)

    os.chmod(tmp_path, 0o600)
    tmp_path.replace(path)


def _input_value(soup, name):
    field = soup.find("input", attrs={"name": name})

    if field is None:
        return None

    return field.get("value")


def _token(soup, form):
    token = _input_value(soup, f"{form}[_token]")

    if not token:
        raise MediapartRegistrationError(f"CSRF token not found: {form}")

    return token


def _offer(soup):
    offers = soup.find_all("input", attrs={"name": "request_subscription[offer]"})

    for offer in offers:
        if offer.has_attr("checked"):
            return offer.get("value")

    if offers:
        return offers[0].get("value")

    raise MediapartRegistrationError("Sponsorship offer not found")


def _user_id(page):
    for pattern in USER_ID_PATTERNS:
        match = pattern.search(page)

        if match:
            return int(match.group(1))

    return None


class MediapartClient:
    def __init__(self, data_dir=None):
        self.email = None
        self.password = None
        self.nickname = None
        self.user_id = 0
        self.created_at = None
        self.expire_at = 0

        data_path = Path(data_dir or os.getenv("DATA_DIR", "data"))
        self._account_path = data_path / "mediapart-account.json"

        self._lock = threading.Lock()
        self._session = requests.Session()
        self._session.headers.update(HEADERS)

        self._failures = 0
        self._cooldown_until = 0
        self._refresh_thread = threading.Thread(
            target=self._auto_refresh_loop,
            daemon=True,
        )

        self._load_account()

    @property
    def is_authenticated(self):
        return bool(self.email and self.password and time.time() < self.expire_at)

    def trial_remaining(self):
        return max(0, self.expire_at - time.time())

    def is_trial_expired(self):
        return self.trial_remaining() <= 0

    def _load_account(self):
        account = read_json(self._account_path)

        if not isinstance(account, dict):
            return

        email = account.get("email")
        password = account.get("password")
        expire_at = account.get("expire_at")

        if not email or not password or not isinstance(expire_at, (int, float)):
            return

        self.email = email
        self.password = password
        self.nickname = account.get("nickname")
        self.user_id = int(account.get("user_id") or 0)
        self.created_at = account.get("created_at")
        self.expire_at = float(expire_at)

    def _save_account(self):
        write_json(self._account_path, {
            "email": self.email,
            "password": self.password,
            "nickname": self.nickname,
            "user_id": self.user_id,
            "created_at": self.created_at,
            "expire_at": self.expire_at,
        })

    def _cooldown_remaining(self):
        return max(0, self._cooldown_until - time.time())

    def _check_cooldown(self):
        remaining = self._cooldown_remaining()

        if remaining > 0:
            raise MediapartThrottledException(
                f"last registration failed, next attempt in {int(remaining) + 1}s."
            )

    def _back_off(self):
        self._failures += 1
        cooldown = min(
            COOLDOWN_SECONDS * 2 ** (self._failures - 1),
            MAX_COOLDOWN_SECONDS,
        )
        self._cooldown_until = time.time() + cooldown

    def _clear_back_off(self):
        self._failures = 0
        self._cooldown_until = 0

    def _next_delay(self):
        delay = max(60, min(REFRESH_INTERVAL, self.trial_remaining()))

        return max(delay, self._cooldown_remaining())

    def _auto_refresh_loop(self):
        # Preventive refresh in case nobody requests an article for a while
        while True:
            try:
                self.refresh()
            except Exception:
                logger.warning("Mediapart refresh failed", exc_info=True)

            time.sleep(self._next_delay())

    def start_refresh_loop(self):
        if not self._refresh_thread.is_alive():
            self._refresh_thread.start()

    def _post(self, url, data, referer):
        return self._session.post(
            url,
            data=data,
            headers={"Referer": referer, "Origin": BASE_URL},
            timeout=TIMEOUT,
        )

    def create_account(self):
        with self._lock:
            self._create_account()

            return True

    def _create_account(self):
        # Start from a clean jar so a previous account's cookies don't leak in
        self._session.cookies.clear()

        page = self._session.get(ENTRY_URL, timeout=TIMEOUT)
        page.raise_for_status()

        soup = BeautifulSoup(page.text, "html.parser")
        offer = _offer(soup)

        email = f"test{token_hex(5)}@mediapart.fr"

        page = self._post(
            ENTRY_URL,
            {
                "request_subscription[offer]": offer,
                "request_subscription[email]": email,
                "request_subscription[cgu]": "1",
                "request_subscription[_token]": _token(soup, "request_subscription"),
            },
            ENTRY_URL,
        )
        page.raise_for_status()

        soup = BeautifulSoup(page.text, "html.parser")
        nickname = email.split("@")[0]

        page = self._post(
            ONBOARDING_URL,
            {
                "onboarding[password]": PASSWORD,
                "onboarding[nickname]": nickname,
                "onboarding[_token]": _token(soup, "onboarding"),
            },
            ONBOARDING_URL,
        )
        page.raise_for_status()

        user_id = _user_id(page.text)
        if not user_id:
            raise MediapartRegistrationError("Account creation was not confirmed")

        self.email = email
        self.password = PASSWORD
        self.nickname = nickname
        self.user_id = user_id
        self.created_at = time.time()
        self.expire_at = self.created_at + TRIAL_SECONDS
        self._save_account()

        return True

    def refresh(self, force=False):
        with self._lock:
            self._check_cooldown()

            try:
                if not force:
                    # Another worker may have created an account in the meantime
                    self._load_account()

                    if self.is_authenticated:
                        self._clear_back_off()
                        return True

                self._create_account()
            except Exception:
                self._back_off()
                raise

            self._clear_back_off()

            return True

    def is_logged_out(self, response):
        if response.status_code in (401, 403):
            return True

        if "/connexion" in response.url or "/signin" in response.url:
            return True

        # Mediapart exposes the logged-in user id on its pages
        user_id = _user_id(response.text)

        return self.user_id > 0 and user_id == 0

    def request(self, method: str, url: str, retry=True, **kwargs):
        if not self.is_authenticated:
            self.refresh()

        headers = kwargs.pop("headers", {})
        kwargs.setdefault("timeout", TIMEOUT)

        response = self._session.request(
            method,
            url,
            headers=headers,
            **kwargs,
        )

        if self.is_logged_out(response):
            if not retry:
                raise MediapartInvalidLogin("The Mediapart session is no longer valid.")

            self.refresh(force=True)
            return self.request(method, url, retry=False, headers=headers, **kwargs)

        response.raise_for_status()

        return response

    def get(self, url, **kwargs):
        return self.request("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self.request("POST", url, **kwargs)
