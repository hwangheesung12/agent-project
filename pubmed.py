from __future__ import annotations

from dataclasses import dataclass
import json
import sqlite3
import time
from typing import Callable, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


EUTILS_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


class PubMedError(RuntimeError):
    pass


@dataclass(frozen=True)
class PubMedRecord:
    pmid: str
    title: str
    abstract: str
    journal: str
    pub_year: int | None
    authors: str


def _text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return "".join(element.itertext()).strip()


def _publication_year(article: ET.Element) -> int | None:
    candidate_paths = (
        ".//JournalIssue/PubDate/Year",
        ".//ArticleDate/Year",
        ".//DateCompleted/Year",
        ".//DateCreated/Year",
    )
    for path in candidate_paths:
        value = article.findtext(path)
        if value and value.isdigit():
            return int(value)

    medline_date = article.findtext(".//JournalIssue/PubDate/MedlineDate", "")
    for token in medline_date.split():
        if len(token) >= 4 and token[:4].isdigit():
            return int(token[:4])
    return None


def parse_pubmed_xml(xml_data: bytes | str) -> tuple[list[PubMedRecord], int]:
    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as exc:
        raise PubMedError("PubMed 응답 XML을 해석하지 못했습니다.") from exc

    records: list[PubMedRecord] = []
    failed = 0
    for item in root.findall(".//PubmedArticle"):
        pmid = _text(item.find(".//MedlineCitation/PMID"))
        if not pmid:
            failed += 1
            continue

        title = _text(item.find(".//Article/ArticleTitle"))
        abstract_parts = [
            _text(part) for part in item.findall(".//Article/Abstract/AbstractText")
        ]
        abstract = "\n".join(part for part in abstract_parts if part)
        journal = _text(item.find(".//Article/Journal/Title"))

        authors: list[str] = []
        for author in item.findall(".//Article/AuthorList/Author"):
            collective = author.findtext("CollectiveName", "").strip()
            if collective:
                authors.append(collective)
                continue
            last_name = author.findtext("LastName", "").strip()
            fore_name = author.findtext("ForeName", "").strip()
            full_name = " ".join(part for part in (fore_name, last_name) if part)
            if full_name:
                authors.append(full_name)

        records.append(
            PubMedRecord(
                pmid=pmid,
                title=title,
                abstract=abstract,
                journal=journal,
                pub_year=_publication_year(item),
                authors="; ".join(authors),
            )
        )
    return records, failed


class PubMedClient:
    def __init__(
        self,
        api_key: str = "",
        email: str = "",
        opener: Callable[..., object] = urlopen,
    ) -> None:
        self.api_key = api_key.strip()
        self.email = email.strip()
        self.opener = opener

    def _request(self, endpoint: str, params: dict[str, str | int]) -> bytes:
        request_params = {**params, "tool": "pubmed_streamlit_collector"}
        if self.api_key:
            request_params["api_key"] = self.api_key
        if self.email:
            request_params["email"] = self.email

        url = f"{EUTILS_BASE_URL}/{endpoint}?{urlencode(request_params)}"
        request = Request(url, headers={"User-Agent": "PubMedStreamlitCollector/1.0"})
        try:
            with self.opener(request, timeout=30) as response:
                return response.read()
        except (HTTPError, URLError, TimeoutError) as exc:
            raise PubMedError(f"PubMed API 요청 오류: {exc}") from exc

    def search(
        self, keyword: str, start_year: int, end_year: int, max_papers: int
    ) -> list[str]:
        query = f"({keyword}) AND ({start_year}:{end_year}[pdat])"
        raw_response = self._request(
            "esearch.fcgi",
            {
                "db": "pubmed",
                "term": query,
                "retmode": "json",
                "retmax": max_papers,
                "sort": "pub date",
            },
        )
        try:
            payload = json.loads(raw_response)
            return [str(pmid) for pmid in payload["esearchresult"]["idlist"]]
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise PubMedError("PubMed 검색 응답을 해석하지 못했습니다.") from exc

    def fetch(self, pmids: Iterable[str]) -> tuple[list[PubMedRecord], int]:
        pmid_list = list(pmids)
        if not pmid_list:
            return [], 0

        all_records: list[PubMedRecord] = []
        failed = 0
        for index in range(0, len(pmid_list), 100):
            batch = pmid_list[index : index + 100]
            raw_response = self._request(
                "efetch.fcgi",
                {
                    "db": "pubmed",
                    "id": ",".join(batch),
                    "retmode": "xml",
                },
            )
            records, parse_failed = parse_pubmed_xml(raw_response)
            all_records.extend(records)
            failed += parse_failed + max(0, len(batch) - len(records) - parse_failed)
            if index + 100 < len(pmid_list):
                time.sleep(0.11 if self.api_key else 0.34)
        return all_records, failed


def get_connection(db_path: str = "pubmed.db") -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pubmed_records (
            pmid TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            abstract TEXT NOT NULL,
            journal TEXT NOT NULL,
            pub_year INTEGER,
            authors TEXT NOT NULL
        )
        """
    )
    return conn


def save_records(
    conn: sqlite3.Connection, records: Iterable[PubMedRecord]
) -> tuple[int, int]:
    saved = 0
    duplicates = 0
    for record in records:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO pubmed_records
                (pmid, title, abstract, journal, pub_year, authors)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                record.pmid,
                record.title,
                record.abstract,
                record.journal,
                record.pub_year,
                record.authors,
            ),
        )
        if cursor.rowcount == 1:
            saved += 1
        else:
            duplicates += 1
    conn.commit()
    return saved, duplicates


def list_records(conn: sqlite3.Connection) -> list[dict[str, object]]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT pmid, title, abstract, journal, pub_year, authors
        FROM pubmed_records
        ORDER BY pub_year DESC, pmid DESC
        """
    ).fetchall()
    return [dict(row) for row in rows]
