import unittest
from urllib.parse import parse_qs, urlparse

from pubmed import (
    PubMedClient,
    PubMedRecord,
    count_journals,
    count_records,
    count_records_by_year,
    count_top_journals,
    get_connection,
    parse_pubmed_xml,
    save_records,
)


SAMPLE_XML = b"""<?xml version="1.0"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>12345678</PMID>
      <Article>
        <Journal>
          <JournalIssue><PubDate><Year>2024</Year></PubDate></JournalIssue>
          <Title>Journal of Tests</Title>
        </Journal>
        <ArticleTitle>A <i>useful</i> article</ArticleTitle>
        <Abstract>
          <AbstractText Label="BACKGROUND">First section.</AbstractText>
          <AbstractText Label="RESULTS">Second section.</AbstractText>
        </Abstract>
        <AuthorList>
          <Author><LastName>Kim</LastName><ForeName>Min Su</ForeName></Author>
          <Author><CollectiveName>Test Group</CollectiveName></Author>
        </AuthorList>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>
"""


class PubMedTests(unittest.TestCase):
    def test_parse_pubmed_xml(self):
        records, failed = parse_pubmed_xml(SAMPLE_XML)

        self.assertEqual(failed, 0)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].pmid, "12345678")
        self.assertEqual(records[0].title, "A useful article")
        self.assertEqual(records[0].abstract, "First section.\nSecond section.")
        self.assertEqual(records[0].journal, "Journal of Tests")
        self.assertEqual(records[0].pub_year, 2024)
        self.assertEqual(records[0].authors, "Min Su Kim; Test Group")

    def test_search_uses_filters_and_credentials(self):
        requested_urls = []

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return None

            def read(self):
                return b'{"esearchresult":{"idlist":["11","22"]}}'

        def fake_opener(request, timeout):
            self.assertEqual(timeout, 30)
            requested_urls.append(request.full_url)
            return FakeResponse()

        client = PubMedClient("secret-key", "owner@example.com", opener=fake_opener)
        pmids = client.search("cancer therapy", 2020, 2024, 2)

        self.assertEqual(pmids, ["11", "22"])
        query = parse_qs(urlparse(requested_urls[0]).query)
        self.assertEqual(query["db"], ["pubmed"])
        self.assertEqual(query["term"], ["(cancer therapy) AND (2020:2024[pdat])"])
        self.assertEqual(query["retmax"], ["2"])
        self.assertEqual(query["api_key"], ["secret-key"])
        self.assertEqual(query["email"], ["owner@example.com"])

    def test_table_and_duplicate_save(self):
        conn = get_connection(":memory:")
        record = PubMedRecord("1", "Title", "Abstract", "Journal", 2023, "Author")

        self.assertEqual(save_records(conn, [record]), (1, 0))
        self.assertEqual(save_records(conn, [record]), (0, 1))
        self.assertEqual(count_journals(conn), 1)

        second_record = PubMedRecord(
            "2", "Title 2", "Abstract 2", "Journal", 2024, "Author 2"
        )
        third_record = PubMedRecord(
            "3", "Title 3", "Abstract 3", "Another Journal", 2024, "Author 3"
        )
        self.assertEqual(save_records(conn, [second_record, third_record]), (2, 0))
        self.assertEqual(count_journals(conn), 2)
        self.assertEqual(count_records(conn), 3)
        self.assertEqual(
            count_records_by_year(conn),
            [
                {"pub_year": 2023, "paper_count": 1},
                {"pub_year": 2024, "paper_count": 2},
            ],
        )
        self.assertEqual(
            count_top_journals(conn),
            [
                {"journal": "Journal", "paper_count": 2},
                {"journal": "Another Journal", "paper_count": 1},
            ],
        )
        columns = {
            row[1] for row in conn.execute("PRAGMA table_info(pubmed_records)")
        }
        self.assertEqual(
            columns,
            {"pmid", "title", "abstract", "journal", "pub_year", "authors"},
        )
        conn.close()


if __name__ == "__main__":
    unittest.main()
