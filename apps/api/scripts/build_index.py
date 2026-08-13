"""
Build the ChromaDB knowledge index.

    python -m scripts.build_index              # curated data + Wikivoyage
    python -m scripts.build_index --offline    # curated data only
    python -m scripts.build_index --cities 20  # limit Wikivoyage fetches

Runs at Docker build time so the index ships inside the image, read-only. Cloud
Run's filesystem is ephemeral and scales to zero, so there is nowhere durable to
write at runtime -- and since the corpus is curated travel content that changes
rarely, baking it in means every deploy gets a byte-identical, reproducible
index rather than one that drifts.

Two sources:

- **Wikivoyage** — CC-licensed travel guides, fetched through the MediaWiki API
  rather than the full dump. The dump is multiple gigabytes and mostly
  irrelevant here; fetching the cities we actually care about is faster, keeps
  the image small, and is trivial to re-run.
- **Curated data** — destination_data.py and season_intelligence.py. This is the
  part that earns the RAG its place: Wikivoyage has no idea what a trip costs in
  rupiah from Jakarta, and neither does a language model.
"""

from __future__ import annotations

import argparse
import logging
import re
import shutil
import sys
import time
from dataclasses import dataclass
from typing import Iterable, Optional

import requests

from src.providers import destination_data, season_intelligence
from src.providers.knowledge import CHROMA_DIR, COLLECTION
from src.providers.places import primary_iata

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("build_index")

WIKIVOYAGE_API = "https://en.wikivoyage.org/w/api.php"
USER_AGENT = "TravelCompanion/2.0 (portfolio project; https://github.com/shendyppy/travel-companion)"

# Sections worth indexing. Wikivoyage articles also carry Get in / Get around /
# Connect, which are mostly logistics that go stale fast and add noise.
USEFUL_SECTIONS = {
    "see", "do", "eat", "drink", "buy", "sleep", "stay safe",
    "understand", "respect", "cope", "go next",
}

# Passage size. Long enough to hold a complete thought, short enough that a hit
# is mostly signal -- an entire "Eat" section would bury the relevant restaurant
# among thirty others.
MAX_CHARS = 1200
MIN_CHARS = 120

# Cities to pull from Wikivoyage: the curated destinations plus the routes
# Indonesian travellers actually ask about.
EXTRA_CITIES = [
    "Bali", "Jakarta", "Bandung", "Surabaya", "Semarang", "Solo (Indonesia)",
    "Labuan Bajo", "Raja Ampat", "Bromo-Tengger-Semeru National Park",
    "Singapore", "Bangkok", "Phuket", "Chiang Mai", "Hanoi", "Da Nang",
    "Kuala Lumpur", "Penang", "Manila", "Cebu", "Phnom Penh", "Siem Reap",
    "Vientiane", "Luang Prabang", "Yangon",
    "Tokyo", "Osaka", "Kyoto", "Fukuoka", "Sapporo", "Seoul", "Busan",
    "Taipei", "Hong Kong", "Shanghai", "Beijing",
    "Dubai", "Istanbul", "Mecca", "Medina",
    "Sydney", "Melbourne", "Auckland",
]


@dataclass
class Document:
    id: str
    text: str
    title: str
    city: Optional[str]
    section: Optional[str]
    source: str
    url: Optional[str]

    def metadata(self) -> dict[str, str]:
        # Chroma rejects None in metadata, so empty strings stand in
        return {
            "title": self.title,
            "city": (self.city or "").lower(),
            "section": (self.section or "").lower(),
            "source": self.source,
            "url": self.url or "",
        }


# ==============================================================================
# Curated data
# ==============================================================================


def curated_documents() -> list[Document]:
    """
    Turn the curated destination and seasonal data into passages.

    Written as prose rather than dumped as JSON: the retriever embeds text, and
    a sentence about what a day in Yogyakarta costs matches a question about
    budget far better than a serialised dict does.
    """
    docs: list[Document] = []

    for dest in destination_data.get_all_destinations():
        city = dest.name
        daily = dest.estimated_daily_cost or {}
        total = sum(daily.values()) if daily else 0
        breakdown = ", ".join(f"{k} around Rp{v:,.0f}" for k, v in daily.items())

        docs.append(Document(
            id=f"curated:{city}:overview",
            text=(
                f"{city}, {dest.country}. {dest.description} "
                f"This is a {dest.budget_category.value} destination, best suited to "
                f"{', '.join(t.value for t in dest.travel_types)} trips. "
                f"Best season: {dest.best_season.value.replace('_', ' ')}. "
                f"{dest.why_budget_friendly}"
            ),
            title=f"{city} overview",
            city=city, section="understand", source="curated", url=None,
        ))

        if daily:
            docs.append(Document(
                id=f"curated:{city}:budget",
                text=(
                    f"Daily budget for {city}, {dest.country}: roughly Rp{total:,.0f} per person "
                    f"per day, broken down as {breakdown}. That is a {dest.budget_category.value} "
                    f"level of spending for an Indonesian traveller. "
                    f"A week here costs in the region of Rp{total * 7:,.0f} excluding flights."
                ),
                title=f"{city} daily cost",
                city=city, section="budget", source="curated", url=None,
            ))

        if dest.highlights:
            docs.append(Document(
                id=f"curated:{city}:highlights",
                text=f"Things to see and do in {city}, {dest.country}: {'; '.join(dest.highlights)}.",
                title=f"{city} highlights",
                city=city, section="see", source="curated", url=None,
            ))

        iata = primary_iata(city)
        if iata:
            info = season_intelligence.get_season_info(iata)
            if info:
                parts = [
                    f"Seasonal guidance for {city} (airport {iata}).",
                    getattr(info, "description", "") or "",
                    f"Weather: {getattr(info, 'weather', '')}." if getattr(info, "weather", None) else "",
                    f"Crowds: {getattr(info, 'crowd_level', '')}." if getattr(info, "crowd_level", None) else "",
                    f"Prices: {getattr(info, 'price_level', '')}." if getattr(info, "price_level", None) else "",
                ]
                cheapest = season_intelligence.get_cheapest_months(iata)
                if cheapest:
                    parts.append(f"Cheapest months to fly: {cheapest}.")
                text = " ".join(p for p in parts if p).strip()
                if len(text) >= MIN_CHARS:
                    docs.append(Document(
                        id=f"curated:{city}:season",
                        text=text,
                        title=f"{city} seasons",
                        city=city, section="when to go", source="curated", url=None,
                    ))

    logger.info("Curated passages: %d", len(docs))
    return docs


# ==============================================================================
# Wikivoyage
# ==============================================================================


def _split_sections(raw: str) -> Iterable[tuple[str, str]]:
    """Split a plaintext extract on '== Section ==' headings."""
    parts = re.split(r"\n==+\s*([^=]+?)\s*==+\n", "\n" + raw)
    if len(parts) == 1:
        yield "understand", raw
        return
    intro = parts[0].strip()
    if intro:
        yield "understand", intro
    for index in range(1, len(parts) - 1, 2):
        yield parts[index].strip().lower(), parts[index + 1].strip()


def _chunk(text: str) -> list[str]:
    """Split on paragraphs, packing them up to MAX_CHARS."""
    chunks, current = [], ""
    for paragraph in (p.strip() for p in text.split("\n") if p.strip()):
        if len(current) + len(paragraph) + 1 > MAX_CHARS and current:
            chunks.append(current)
            current = paragraph
        else:
            current = f"{current}\n{paragraph}" if current else paragraph
    if current:
        chunks.append(current)
    return [c for c in chunks if len(c) >= MIN_CHARS]


def fetch_wikivoyage(titles: list[str], session: requests.Session) -> list[Document]:
    docs: list[Document] = []

    for title in titles:
        try:
            response = session.get(
                WIKIVOYAGE_API,
                params={
                    "action": "query", "format": "json", "titles": title,
                    "prop": "extracts", "explaintext": "1", "redirects": "1",
                },
                timeout=30,
            )
            response.raise_for_status()
            pages = (response.json().get("query") or {}).get("pages") or {}
        except Exception as exc:
            logger.warning("  %s: fetch failed (%s)", title, exc)
            continue

        for page_id, page in pages.items():
            if page_id == "-1" or not page.get("extract"):
                logger.warning("  %s: no article", title)
                continue

            real_title = page.get("title", title)
            city = real_title.split("(")[0].strip()
            url = f"https://en.wikivoyage.org/wiki/{real_title.replace(' ', '_')}"
            kept = 0

            for section, body in _split_sections(page["extract"]):
                if section not in USEFUL_SECTIONS:
                    continue
                for index, chunk in enumerate(_chunk(body)):
                    docs.append(Document(
                        id=f"wv:{real_title}:{section}:{index}",
                        text=chunk,
                        title=f"{real_title} — {section.title()}",
                        city=city, section=section, source="wikivoyage", url=url,
                    ))
                    kept += 1
            logger.info("  %s: %d passages", real_title, kept)

        # Wikivoyage is donation-funded infrastructure; do not hammer it
        time.sleep(0.3)

    return docs


# ==============================================================================
# Index
# ==============================================================================


def build(documents: list[Document]) -> None:
    import chromadb

    if CHROMA_DIR.exists():
        logger.info("Removing existing index at %s", CHROMA_DIR)
        shutil.rmtree(CHROMA_DIR)
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.create_collection(
        COLLECTION,
        metadata={"hnsw:space": "l2"},
    )

    # Batched so the embedding model is not handed thousands of documents at once
    batch_size = 128
    for start in range(0, len(documents), batch_size):
        batch = documents[start:start + batch_size]
        collection.add(
            ids=[d.id for d in batch],
            documents=[d.text for d in batch],
            metadatas=[d.metadata() for d in batch],
        )
        logger.info("Embedded %d/%d", min(start + batch_size, len(documents)), len(documents))

    logger.info("Index built: %d passages at %s", collection.count(), CHROMA_DIR)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the travel knowledge index")
    parser.add_argument("--offline", action="store_true", help="skip Wikivoyage, curated data only")
    parser.add_argument("--cities", type=int, default=0, help="cap Wikivoyage articles (0 = all)")
    args = parser.parse_args()

    documents = curated_documents()

    if not args.offline:
        titles = list(dict.fromkeys(
            [d.name for d in destination_data.get_all_destinations()] + EXTRA_CITIES
        ))
        if args.cities:
            titles = titles[:args.cities]

        logger.info("Fetching %d Wikivoyage articles", len(titles))
        session = requests.Session()
        session.headers["User-Agent"] = USER_AGENT
        wiki_docs = fetch_wikivoyage(titles, session)
        logger.info("Wikivoyage passages: %d", len(wiki_docs))

        if not wiki_docs:
            # Better to fail loudly than to ship an index that quietly lost its
            # largest source
            logger.error("Wikivoyage returned nothing. Use --offline if that is intended.")
            return 1
        documents += wiki_docs

    # Deduplicate: a city can appear in both the curated list and EXTRA_CITIES
    unique = {d.id: d for d in documents}
    documents = list(unique.values())

    if not documents:
        logger.error("No documents to index")
        return 1

    build(documents)
    return 0


if __name__ == "__main__":
    sys.exit(main())
