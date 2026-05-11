from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import requests
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class Connector(ABC):
    def __init__(
        self,
        source_id: str,
        *,
        verify_ssl: bool = True,
        connect_timeout: int = 5,
        read_timeout: int = 15,
        retries: int = 2,
    ) -> None:
        self.source_id = source_id
        self.verify_ssl = verify_ssl
        self.timeout = (connect_timeout, read_timeout)
        self.session = self._build_session(retries=retries)

    def _build_session(self, *, retries: int) -> requests.Session:
        session = requests.Session()
        retry_policy = Retry(
            total=retries,
            backoff_factor=1,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
        )
        adapter = HTTPAdapter(max_retries=retry_policy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        if not self.verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        return session

    def get_json(self, url: str) -> dict[str, Any]:
        response = self.session.get(url, timeout=self.timeout, verify=self.verify_ssl)
        response.raise_for_status()
        return response.json()

    def get_text(self, url: str) -> str:
        response = self.session.get(url, timeout=self.timeout, verify=self.verify_ssl)
        response.raise_for_status()
        return response.text

    def run(self) -> Any:
        return self.parse_bulletin(self.fetch_source())

    @abstractmethod
    def fetch_source(self) -> Any:
        raise NotImplementedError

    @abstractmethod
    def parse_bulletin(self, raw_source: Any) -> Any:
        raise NotImplementedError