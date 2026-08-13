"""
Place lookup tests.

This module replaced four separate implementations, so these cases are not
ceremony: two of them are real bugs caught the first time it was written.
"""

import pytest

from src.providers import places


class TestBasicResolution:
    def test_direct_iata_code(self):
        result = places.resolve("DPS")
        assert result[0].iata == "DPS"
        assert result[0].country == "Indonesia"

    def test_city_name(self):
        assert places.primary_iata("Denpasar") == "DPS"

    def test_empty_query(self):
        assert places.resolve("") == []
        assert places.resolve("   ") == []

    def test_nonsense_place(self):
        assert places.primary_iata("qwertyuiop asdf") is None

    def test_case_insensitive(self):
        assert places.primary_iata("bAlI") == places.primary_iata("Bali")


class TestIndonesianNicknames:
    """People rarely use a city's official name."""

    @pytest.mark.parametrize(
        "query,expected",
        [
            ("Bali", "DPS"),
            ("Jogja", "YIA"),
            ("Jogjakarta", "YIA"),
            ("Yogyakarta", "YIA"),
            ("Jakarta", "CGK"),
            ("JKT", "CGK"),
        ],
    )
    def test_common_nicknames(self, query, expected):
        assert places.primary_iata(query) == expected


class TestMultiAirportCities:
    """When the user names only a city, the primary airport must win."""

    @pytest.mark.parametrize(
        "city,expected",
        [
            ("Tokyo", "NRT"),         # not HND
            ("Jakarta", "CGK"),       # not HLP or PCB
            ("London", "LHR"),
            ("Kuala Lumpur", "KUL"),  # not SZB
        ],
    )
    def test_primary_airport_first(self, city, expected):
        assert places.primary_iata(city) == expected

    def test_singapore_resolves_to_changi_not_seletar(self):
        """Regression: without an explicit preference, Seletar (XSP) sorted first."""
        assert places.primary_iata("Singapore") == "SIN"


class TestAirportsMissingFromDataset:
    """
    Regression: airports.dat (OpenFlights) stops around 2017, so airports that
    opened later are absent. Without the supplement, 'Jogja' resolved to JOG,
    which no longer handles scheduled commercial traffic.
    """

    def test_yia_exists(self):
        yia = places.describe("YIA")
        assert yia is not None
        assert yia.city == "Yogyakarta"

    def test_yia_beats_jog(self):
        assert places.primary_iata("Yogyakarta") == "YIA"

    def test_ber_exists(self):
        assert places.primary_iata("Berlin") == "BER"


class TestNormalisation:
    def test_accents_ignored(self):
        assert places.primary_iata("São Paulo") == places.primary_iata("Sao Paulo")

    def test_extra_whitespace(self):
        assert places.primary_iata("  Kuala   Lumpur  ") == "KUL"


class TestIndex:
    def test_dataset_fully_loaded(self):
        by_iata, by_city = places._build_index()
        # If the data path is wrong these drop to 0 -- exactly the bug that
        # appeared when the module moved into providers/
        assert len(by_iata) > 5000
        assert len(by_city) > 3000

    def test_index_built_once(self):
        first, _ = places._build_index()
        second, _ = places._build_index()
        assert first is second
