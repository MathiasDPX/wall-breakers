import ipaddress
import json
import os
import socket
import threading
import time
from hashlib import sha256
from pathlib import Path

import requests

from providers.exceptions import (
    SocialterMissingSubscriptionException,
    SocialterRegistrationError,
    SocialterThrottledException,
)

BASE_URL = "https://www.socialter.fr"
LOGIN_URL = f"{BASE_URL}/connexion"

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

TIMEOUT = (3.05, 15)


def is_routable(address):
    """Whether a resolved address is worth attempting a connection to."""
    try:
        ip = ipaddress.ip_address(address.split("%")[0])
    except ValueError:
        # Not an IP literal (unix socket, weird resolver answer), let it through
        return True

    if ip.version == 6:
        return not (ip.is_link_local or ip.is_multicast or ip.is_unspecified)

    # Private IPv4 is left alone, some providers are only reachable internally
    return True


def install_dns_workaround():
    """Stop unroutable IPv6 answers from eating the connect timeout."""
    if getattr(socket.getaddrinfo, "_drops_unroutable", False):
        return

    resolver = socket.getaddrinfo

    def getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        results = resolver(host, port, family, type, proto, flags)
        routable = [res for res in results if is_routable(res[4][0])]

        return routable or results

    getaddrinfo._drops_unroutable = True
    socket.getaddrinfo = getaddrinfo

REGISTER_PAYLOAD = {
    "id_element": "-1",
    "moduleAction": "1",
    "moduleName": "User",
    "keyControl": "a965b745560d1519ed04f799c37cccb4",
    "redirect": f"{BASE_URL}/confirmation-inscription",
    "mod_user_user_front_id": "",
    "user_action": "register",
    "mod_user_civ": "0",
    "mod_user_firstname": "John",
    "mod_user_lastname": "Doe",
    "mod_user_company": "",
    "mod_user_address": "55 rue du Faubourg-Saint-Honoré",  # Palais de l'Elysée
    "mod_user_address_complement": "",
    "mod_user_address_locality": "",
    "mod_user_zip": "75008",
    "mod_user_city": "Paris",
    "mod_user_country": "2",
    "mod_user_tel": "",
    "mod_user_newsletter": "0",
    "mod_user_term": "1",
}

PAYWALL_MARKER = '<div class="frame-registration-title">Débloquez cet article gratuitement !</div>'

COOLDOWN_SECONDS = 15 * 60
MAX_COOLDOWN_SECONDS = 6 * 60 * 60

REGISTRATION_WINDOW = 6 * 60 * 60
MAX_REGISTRATIONS_PER_WINDOW = 3


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


class SocialterClient:
    def __init__(self, data_dir=None):
        install_dns_workaround()

        self.email = None
        self.password = None
        self.created_at = None
        self.trial_seconds = 7 * 24 * 60 * 60

        data_path = Path(data_dir or os.getenv("DATA_DIR", "data"))
        self._account_path = data_path / "socialter-account.json"
        self._registrations_path = data_path / "socialter-registrations.json"

        self._lock = threading.Lock()
        self._refresh_thread = threading.Thread(
            target=self._auto_refresh_loop,
            daemon=True,
        )
        self._session = requests.Session()

        self._failures = 0
        self._cooldown_until = 0
        self._registrations = self._load_registrations()

        self._load_account()

    def _auto_refresh_loop(self):
        # Preventive refresh every 24 hours in case nobody sent a request to Socialter
        while True:
            try:
                self.refresh()
            except SocialterThrottledException:
                pass

            time.sleep(self._next_delay())

    def _next_delay(self):
        delay = min(24 * 60 * 60, max(60, self.trial_remaining()))
        
        return max(delay, self._cooldown_remaining())

    def start_refresh_loop(self):
        if not self._refresh_thread.is_alive():
            self._refresh_thread.start()

    def _load_account(self):
        account = read_json(self._account_path)

        if not isinstance(account, dict):
            return

        email = account.get("email")
        password = account.get("password")
        created_at = account.get("created_at")

        if not email or not password or created_at is None:
            return

        self.email = email
        self.password = password
        self.created_at = created_at

    def _save_account(self):
        write_json(self._account_path, {
            "email": self.email,
            "password": self.password,
            "created_at": self.created_at,
        })

    def _load_registrations(self):
        data = read_json(self._registrations_path) or {}
        timestamps = data.get("registrations")

        if not isinstance(timestamps, list):
            return []

        now = time.time()

        return [
            ts for ts in timestamps
            if isinstance(ts, (int, float)) and 0 < now - ts < REGISTRATION_WINDOW
        ]

    def _reserve_registration(self):
        now = time.time()
        self._registrations = [
            ts for ts in self._registrations if now - ts < REGISTRATION_WINDOW
        ]

        if len(self._registrations) >= MAX_REGISTRATIONS_PER_WINDOW:
            raise SocialterThrottledException(
                f"{MAX_REGISTRATIONS_PER_WINDOW} accounts were already created "
                f"in the last {REGISTRATION_WINDOW // 3600} hours."
            )

        self._registrations.append(now)
        write_json(self._registrations_path, {"registrations": self._registrations})

    def _cooldown_remaining(self):
        return max(0, self._cooldown_until - time.time())

    def _check_cooldown(self):
        remaining = self._cooldown_remaining()

        if remaining > 0:
            raise SocialterThrottledException(
                f"last refresh failed, next attempt in {int(remaining) + 1}s."
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

    @property
    def trial_expires_at(self):
        if self.created_at is None:
            return None

        return self.created_at + self.trial_seconds

    def trial_remaining(self):
        if self.created_at is None:
            return 0

        return max(0, self.trial_expires_at - time.time())

    def is_trial_expired(self):
        return self.trial_remaining() <= 0

    def _headers(self, **headers):
        return {
            "User-Agent": USER_AGENT,
            **headers,
        }

    def _ajax_headers(self, **headers):
        return self._headers(
            Accept="application/json, text/javascript, */*; q=0.01",
            **{
                "X-Requested-With": "XMLHttpRequest",
                "Origin": BASE_URL,
                "Referer": LOGIN_URL,
                **headers,
            },
        )

    def _post_action(self, payload):
        r = self._session.post(
            LOGIN_URL,
            data=payload,
            headers=self._ajax_headers(),
            timeout=TIMEOUT,
        )
        r.raise_for_status()

        return r.json()

    def login(self, email=None, password=None):
        email = email or self.email
        password = password or self.password

        if not email or not password:
            return False

        result = self._post_action({
            "user_action": "login",
            "user_login": email,
            "user_password": password,
        })

        if not result.get("result"):
            return False

        self.email = email
        self.password = password

        return True

    def create_account(self):
        print("create account")
        self._reserve_registration()

        email = sha256(str(time.time()).encode()).hexdigest()[:10] + "@gmail.com"
        password = "soci@lter1"

        result = self._post_action({
            **REGISTER_PAYLOAD,
            "user_login": email,
            "user_password": password,
            "user_password_confirm": password,
        })

        if not result.get("result"):
            raise SocialterRegistrationError(result.get("msg", "Unknown error"))

        self.email = email
        self.password = password
        self.created_at = time.time()
        self._save_account()

        self.login(email, password)

        return True

    def refresh(self):
        with self._lock:
            self._check_cooldown()

            try:
                if self._refresh_session():
                    self._clear_back_off()
                    return True
            except SocialterThrottledException:
                raise
            except Exception:
                self._back_off()
                raise

            self._back_off()
            raise SocialterRegistrationError("Could not register a new account")

    def _refresh_session(self):
        if self.created_at is not None and not self.is_trial_expired():
            if self.login():
                return True

        return self.create_account()

    def is_logged_out(self, response):
        return (
            response.status_code == 401
            or LOGIN_URL in response.url
            or not self.is_subscribed(response.text)
        )

    def request(self, method: str, url: str, retry=True, **kwargs):
        headers = kwargs.pop("headers", {})
        kwargs.setdefault("timeout", TIMEOUT)
        response = self._session.request(
            method,
            url,
            headers=self._headers(**headers),
            **kwargs,
        )

        logged_out = self.is_logged_out(response)

        if logged_out and retry:
            self.refresh()
            return self.request(method, url, retry=False, headers=headers, **kwargs)

        if logged_out:
            raise SocialterMissingSubscriptionException(
                "The Socialter account has no active subscription."
            )

        response.raise_for_status()
        return response

    def get(self, url, **kwargs):
        return self.request("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self.request("POST", url, **kwargs)

    @staticmethod
    def is_subscribed(content):
        # Return if the account has a subscription from an article
        return PAYWALL_MARKER not in content