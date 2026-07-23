from __future__ import annotations

from dataclasses import dataclass
import json
import re
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


def list_records(
    conn: sqlite3.Connection,
    search_term: str = "",
    start_year: int | None = None,
    end_year: int | None = None,
    journal: str = "",
) -> list[dict[str, object]]:
    conn.row_factory = sqlite3.Row
    filters: list[str] = []
    params: list[object] = []

    normalized_search = search_term.strip()
    if normalized_search:
        search_pattern = re.compile(
            rf"(?<!\w){re.escape(normalized_search)}(?!\w)",
            re.IGNORECASE,
        )
        conn.create_function(
            "matches_search_term",
            1,
            lambda value: search_pattern.search(value or "") is not None,
        )
        filters.append(
            "(matches_search_term(title) OR matches_search_term(abstract))"
        )

    if start_year is not None:
        filters.append("pub_year >= ?")
        params.append(start_year)

    if end_year is not None:
        filters.append("pub_year <= ?")
        params.append(end_year)

    normalized_journal = journal.strip()
    if normalized_journal:
        filters.append("journal = ?")
        params.append(normalized_journal)

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    rows = conn.execute(
        f"""
        SELECT pmid, title, abstract, journal, pub_year, authors
        FROM pubmed_records
        {where_clause}
        ORDER BY pub_year DESC, pmid DESC
        """,
        params,
    ).fetchall()
    return [dict(row) for row in rows]


def search_records_for_chat(
    conn: sqlite3.Connection,
    query: str,
    limit: int = 5,
) -> list[dict[str, object]]:
    """Return the most relevant stored papers for a chatbot search."""
    terms = list(
        dict.fromkeys(
            token.casefold()
            for token in re.findall(r"[0-9A-Za-z가-힣]+", query)
            if len(token) >= 2
        )
    )[:8]
    if not terms:
        return []

    conn.row_factory = sqlite3.Row
    match_clauses: list[str] = []
    params: list[object] = []
    for term in terms:
        pattern = f"%{term}%"
        match_clauses.append(
            """
            (
                title LIKE ? COLLATE NOCASE
                OR abstract LIKE ? COLLATE NOCASE
                OR journal LIKE ? COLLATE NOCASE
                OR authors LIKE ? COLLATE NOCASE
                OR pmid = ?
            )
            """
        )
        params.extend([pattern, pattern, pattern, pattern, term])

    rows = conn.execute(
        f"""
        SELECT pmid, title, abstract, journal, pub_year, authors
        FROM pubmed_records
        WHERE {" OR ".join(match_clauses)}
        LIMIT 200
        """,
        params,
    ).fetchall()
    normalized_query = query.casefold().strip()

    def relevance(row: sqlite3.Row) -> tuple[int, int, str]:
        title = str(row["title"]).casefold()
        abstract = str(row["abstract"]).casefold()
        journal = str(row["journal"]).casefold()
        authors = str(row["authors"]).casefold()
        score = 0
        if normalized_query and normalized_query in title:
            score += 12
        if normalized_query and normalized_query in abstract:
            score += 5
        for term in terms:
            score += 5 if term in title else 0
            score += 2 if term in abstract else 0
            score += 2 if term in journal else 0
            score += 1 if term in authors else 0
            score += 10 if term == str(row["pmid"]).casefold() else 0
        return (
            score,
            int(row["pub_year"]) if row["pub_year"] is not None else 0,
            str(row["pmid"]),
        )

    ranked = sorted(rows, key=relevance, reverse=True)
    safe_limit = max(1, min(int(limit), 10))
    return [dict(row) for row in ranked[:safe_limit]]


def list_journals(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        """
        SELECT DISTINCT journal
        FROM pubmed_records
        WHERE journal != ''
        ORDER BY journal COLLATE NOCASE
        """
    ).fetchall()
    return [row[0] for row in rows]


def count_journals(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        """
        SELECT COUNT(DISTINCT journal)
        FROM pubmed_records
        WHERE TRIM(journal) != ''
        """
    ).fetchone()
    return int(row[0])


def count_records(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COUNT(*) FROM pubmed_records").fetchone()
    return int(row[0])


def count_records_by_year(conn: sqlite3.Connection) -> list[dict[str, int]]:
    rows = conn.execute(
        """
        SELECT pub_year, COUNT(*) AS paper_count
        FROM pubmed_records
        WHERE pub_year IS NOT NULL
        GROUP BY pub_year
        ORDER BY pub_year
        """
    ).fetchall()
    return [
        {"pub_year": int(pub_year), "paper_count": int(paper_count)}
        for pub_year, paper_count in rows
    ]


def count_top_journals(
    conn: sqlite3.Connection, limit: int = 10
) -> list[dict[str, str | int]]:
    rows = conn.execute(
        """
        SELECT journal, COUNT(*) AS paper_count
        FROM pubmed_records
        WHERE TRIM(journal) != ''
        GROUP BY journal
        ORDER BY paper_count DESC, journal ASC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [
        {"journal": str(journal), "paper_count": int(paper_count)}
        for journal, paper_count in rows
    ]
