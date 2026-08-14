"""
Destination data for budget-friendly travel recommendations
Contains destinations with cost categories, travel types, and seasonal info
"""

from typing import List, Dict, Optional
from enum import Enum
import json

class BudgetCategory(Enum):
    BUDGET = "budget"          # < 500k IDR per day
    AFFORDABLE = "affordable"  # 500k - 1M IDR per day
    MODERATE = "moderate"      # 1M - 2M IDR per day
    SPLURGE = "splurge"        # > 2M IDR per day (still reasonable)

class TravelType(Enum):
    BEACH = "beach"
    MOUNTAIN = "mountain"
    CULTURAL = "cultural"
    CITY = "city"
    ADVENTURE = "adventure"
    NATURE = "nature"
    FOODIE = "foodie"
    SHOPPING = "shopping"

class Season(Enum):
    ALL_YEAR = "all_year"
    SUMMER = "summer"      # Apr - Sep
    WINTER = "winter"      # Oct - Mar
    DRY_SEASON = "dry_season"  # May - Sep
    RAINY_SEASON = "rainy_season"  # Oct - Apr
    SPRING = "spring"      # Mar - May (cherry blossoms!)
    AUTUMN = "autumn"      # Sep - Nov (fall foliage)


# The daily-spend boundaries behind BudgetCategory, in IDR. These used to exist
# only as comments on the enum, which meant the landing page's budget picker
# would have had to restate them and quietly drift the first time one moved.
# `None` is an open end.
BUDGET_BANDS: Dict[BudgetCategory, Dict[str, Optional[int]]] = {
    BudgetCategory.BUDGET:     {"min_idr": None,      "max_idr": 500_000},
    BudgetCategory.AFFORDABLE: {"min_idr": 500_000,   "max_idr": 1_000_000},
    BudgetCategory.MODERATE:   {"min_idr": 1_000_000, "max_idr": 2_000_000},
    BudgetCategory.SPLURGE:    {"min_idr": 2_000_000, "max_idr": None},
}

REGIONS = ("domestic", "international")


class Destination:
    def __init__(self, name: str, country: str, region: str, description: str,
                 budget_category: BudgetCategory, travel_types: List[TravelType],
                 best_season: Season, estimated_daily_cost: Dict[str, float],
                 highlights: List[str], why_budget_friendly: str):
        self.name = name
        self.country = country
        self.region = region  # domestic/international
        self.description = description
        self.budget_category = budget_category
        self.travel_types = travel_types
        self.best_season = best_season
        self.estimated_daily_cost = estimated_daily_cost  # accommodation, food, activities
        self.highlights = highlights
        self.why_budget_friendly = why_budget_friendly

# Database of budget-friendly destinations
DESTINATIONS = [
    # Domestic Destinations
    Destination(
        name="Yogyakarta",
        country="Indonesia",
        region="domestic",
        description="Heart of Javanese culture with ancient temples, arts, and affordable culinary delights",
        budget_category=BudgetCategory.BUDGET,
        travel_types=[TravelType.CULTURAL, TravelType.FOODIE, TravelType.CITY],
        best_season=Season.ALL_YEAR,
        estimated_daily_cost={
            "accommodation": 150000,
            "food": 75000,
            "activities": 50000,
            "transport": 50000
        },
        highlights=[
            "Borobudur Temple sunrise",
            "Prambanan Temple",
            "Malioboro street shopping",
            "Kraton Yogyakarta palace",
            "Authentic Javanese cuisine"
        ],
        why_budget_friendly="Super affordable street food, cheap homestays, and many free cultural attractions"
    ),

    Destination(
        name="Lombok",
        country="Indonesia",
        region="domestic",
        description="Stunning beaches and the famous Gili Islands without Bali's crowds",
        budget_category=BudgetCategory.AFFORDABLE,
        travel_types=[TravelType.BEACH, TravelType.ADVENTURE, TravelType.NATURE],
        best_season=Season.DRY_SEASON,
        estimated_daily_cost={
            "accommodation": 200000,
            "food": 100000,
            "activities": 100000,
            "transport": 75000
        },
        highlights=[
            "Gili Islands (Trawangan, Meno, Air)",
            "Kuta Beach Lombok",
            "Mount Rinjani trekking",
            "Traditional Sasak villages",
            "Pink Beach"
        ],
        why_budget_friendly="Local warungs are cheap, homestays are abundant, and many beaches are free to access"
    ),

    Destination(
        name="Belitung",
        country="Indonesia",
        region="domestic",
        description="Island paradise with unique granite beaches and clear waters",
        budget_category=BudgetCategory.AFFORDABLE,
        travel_types=[TravelType.BEACH, TravelType.NATURE, TravelType.FOODIE],
        best_season=Season.DRY_SEASON,
        estimated_daily_cost={
            "accommodation": 250000,
            "food": 100000,
            "activities": 150000,
            "transport": 100000
        },
        highlights=[
            "Tanjung Kelayang Beach",
            "Lengkuas Island lighthouse",
            "Kaolin Lake",
            "Traditional seafood cuisine",
            "Island hopping tours"
        ],
        why_budget_friendly="Fresh seafood is affordable, local tour prices are reasonable, and public beaches"
    ),

    Destination(
        name="Bandung",
        country="Indonesia",
        region="domestic",
        description="Cool climate city with factory outlets, culinary scene, and volcanic landscapes",
        budget_category=BudgetCategory.BUDGET,
        travel_types=[TravelType.CITY, TravelType.FOODIE, TravelType.SHOPPING, TravelType.NATURE],
        best_season=Season.ALL_YEAR,
        estimated_daily_cost={
            "accommodation": 200000,
            "food": 100000,
            "activities": 75000,
            "transport": 50000
        },
        highlights=[
            "Factory outlet shopping",
            "Tangkuban Perahu volcano",
            "Ciater hot springs",
            "Farmhouse Lembang",
            "Sundanese cuisine"
        ],
        why_budget_friendly="Cheap accommodation, affordable local food, and many free natural attractions"
    ),

    Destination(
        name="Malang",
        country="Indonesia",
        region="domestic",
        description="Cool mountain town with apple orchards, waterfalls, and colonial architecture",
        budget_category=BudgetCategory.BUDGET,
        travel_types=[TravelType.NATURE, TravelType.CULTURAL, TravelType.FOODIE],
        best_season=Season.ALL_YEAR,
        estimated_daily_cost={
            "accommodation": 150000,
            "food": 75000,
            "activities": 50000,
            "transport": 50000
        },
        highlights=[
            "Bromo Tengger Semeru National Park",
            "Apple orchards in Batu",
            "Coban Rondo waterfall",
            "Colonial architecture tours",
            "Local coffee plantations"
        ],
        why_budget_friendly="Very cheap food, budget homestays, and many natural attractions with minimal entry fees"
    ),

    # International Destinations (Budget-Friendly)
    Destination(
        name="Kuala Lumpur",
        country="Malaysia",
        region="international",
        description="Modern city with iconic Petronas Towers, diverse cuisine, and affordable shopping",
        budget_category=BudgetCategory.AFFORDABLE,
        travel_types=[TravelType.CITY, TravelType.FOODIE, TravelType.SHOPPING],
        best_season=Season.ALL_YEAR,
        estimated_daily_cost={
            "accommodation": 400000,
            "food": 150000,
            "activities": 100000,
            "transport": 75000
        },
        highlights=[
            "Petronas Twin Towers",
            "Batu Caves",
            "Central Market",
            "Jalan Alor food street",
            "Affordable shopping at Bukit Bintang"
        ],
        why_budget_friendly="Cheap street food, free attractions like parks and temples, and budget hostels"
    ),

    Destination(
        name="Ho Chi Minh City",
        country="Vietnam",
        region="international",
        description="Vibrant city with French colonial architecture, amazing street food, and rich history",
        budget_category=BudgetCategory.BUDGET,
        travel_types=[TravelType.CITY, TravelType.FOODIE, TravelType.CULTURAL],
        best_season=Season.DRY_SEASON,
        estimated_daily_cost={
            "accommodation": 250000,
            "food": 100000,
            "activities": 75000,
            "transport": 50000
        },
        highlights=[
            "War Remnants Museum",
            "Cu Chi Tunnels",
            "Ben Thanh Market",
            "French Quarter architecture",
            "Amazing pho and banh mi"
        ],
        why_budget_friendly="Extremely cheap street food, budget accommodations, and low transportation costs"
    ),

    Destination(
        name="Chiang Mai",
        country="Thailand",
        region="international",
        description="Ancient city in mountains with temples, night markets, and ethical elephant sanctuaries",
        budget_category=BudgetCategory.AFFORDABLE,
        travel_types=[TravelType.CULTURAL, TravelType.NATURE, TravelType.FOODIE],
        best_season=Season.WINTER,
        estimated_daily_cost={
            "accommodation": 300000,
            "food": 125000,
            "activities": 100000,
            "transport": 75000
        },
        highlights=[
            "Doi Suthep temple",
            "Sunday night market",
            "Elephant Nature Park",
            "Old City temples tour",
            "Thai cooking classes"
        ],
        why_budget_friendly="Cheap local food, affordable guesthouses, and many free temples to explore"
    ),

    Destination(
        name="Siem Reap",
        country="Cambodia",
        region="international",
        description="Gateway to Angkor Wat with charming French-inspired town and affordable living",
        budget_category=BudgetCategory.BUDGET,
        travel_types=[TravelType.CULTURAL, TravelType.NATURE, TravelType.FOODIE],
        best_season=Season.DRY_SEASON,
        estimated_daily_cost={
            "accommodation": 200000,
            "food": 100000,
            "activities": 100000,
            "transport": 75000
        },
        highlights=[
            "Angkor Wat sunrise",
            "Angkor Thom and Bayon",
            "Tonlé Sap lake",
            "Pub Street night market",
            "Traditional Apsara dance shows"
        ],
        why_budget_friendly="Very cheap accommodation and food, affordable multi-day temple passes"
    ),

    Destination(
        name="Penang",
        country="Malaysia",
        region="international",
        description="Street food capital of Malaysia with George Town's UNESCO heritage sites",
        budget_category=BudgetCategory.AFFORDABLE,
        travel_types=[TravelType.FOODIE, TravelType.CULTURAL, TravelType.CITY],
        best_season=Season.ALL_YEAR,
        estimated_daily_cost={
            "accommodation": 350000,
            "food": 150000,
            "activities": 100000,
            "transport": 75000
        },
        highlights=[
            "George Town street art",
            "Penang Hill funicular",
            "Kek Lok Si temple",
            "Gurney Drive hawker food",
            "Batu Ferringhi beaches"
        ],
        why_budget_friendly="Famous affordable street food, cheap public transport, and free heritage walking tours"
    ),

    Destination(
        name="Vientiane",
        country="Laos",
        region="international",
        description="Relaxed capital with Buddhist temples, French colonial architecture, and Mekong riverside",
        budget_category=BudgetCategory.BUDGET,
        travel_types=[TravelType.CULTURAL, TravelType.CITY, TravelType.NATURE],
        best_season=Season.DRY_SEASON,
        estimated_daily_cost={
            "accommodation": 250000,
            "food": 100000,
            "activities": 75000,
            "transport": 50000
        },
        highlights=[
            "Pha That Luang golden stupa",
            "Buddha Park",
            "Mekong riverside sunset",
            "Morning Market shopping",
            "French colonial cafes"
        ],
        why_budget_friendly="Very low cost of living, cheap accommodation, and affordable local food"
    ),

    # Japan Destinations
    Destination(
        name="Tokyo",
        country="Japan",
        region="international",
        description="Vibrant metropolis blending ultra-modern with traditional culture, amazing food, and efficient transport",
        budget_category=BudgetCategory.AFFORDABLE,
        travel_types=[TravelType.CITY, TravelType.CULTURAL, TravelType.FOODIE],
        best_season=Season.SPRING,  # Cherry blossom season
        estimated_daily_cost={
            "accommodation": 600000,
            "food": 200000,
            "activities": 150000,
            "transport": 100000
        },
        highlights=[
            "Senso-ji Temple in Asakusa",
            "Shibuya Crossing",
            "Tokyo Skytree or Tokyo Tower",
            "Tsukiji Outer Market food",
            "Akihabara electronics district"
        ],
        why_budget_friendly="Free temples and parks, affordable convenience store meals, excellent public transport"
    ),

    Destination(
        name="Osaka",
        country="Japan",
        region="international",
        description="Food capital of Japan with vibrant street life, historic castle, and easy access to Kyoto",
        budget_category=BudgetCategory.AFFORDABLE,
        travel_types=[TravelType.CITY, TravelType.FOODIE, TravelType.CULTURAL],
        best_season=Season.SPRING,
        estimated_daily_cost={
            "accommodation": 550000,
            "food": 180000,
            "activities": 120000,
            "transport": 80000
        },
        highlights=[
            "Osaka Castle",
            "Dotonbori entertainment district",
            "Kuromon Ichiba Market",
            "Universal Studios Japan",
            "Shitennoji Temple"
        ],
        why_budget_friendly="Amazing street food (takoyaki, okonomiyaki), free attractions, cheap day trips to Kyoto"
    ),

    Destination(
        name="Kyoto",
        country="Japan",
        region="international",
        description="Ancient capital with thousands of temples, traditional architecture, and beautiful gardens",
        budget_category=BudgetCategory.AFFORDABLE,
        travel_types=[TravelType.CULTURAL, TravelType.NATURE, TravelType.CITY],
        best_season=Season.SPRING,
        estimated_daily_cost={
            "accommodation": 500000,
            "food": 180000,
            "activities": 100000,
            "transport": 70000
        },
        highlights=[
            "Fushimi Inari Shrine (thousands of torii gates)",
            "Kinkaku-ji (Golden Pavilion)",
            "Arashiyama Bamboo Grove",
            "Gion district (geisha area)",
            "Kiyomizu-dera Temple"
        ],
        why_budget_friendly="Many free temples and gardens, affordable vegetarian Buddhist cuisine, walkable city center"
    ),

    Destination(
        name="Fukuoka",
        country="Japan",
        region="international",
        description="Gateway to Kyushu with amazing ramen, beaches, and close to South Korea",
        budget_category=BudgetCategory.BUDGET,
        travel_types=[TravelType.CITY, TravelType.FOODIE, TravelType.NATURE],
        best_season=Season.SPRING,
        estimated_daily_cost={
            "accommodation": 400000,
            "food": 150000,
            "activities": 80000,
            "transport": 60000
        },
        highlights=[
            "Fukuoka Tower",
            "Ohori Park",
            "Canal City Hakata",
            "Yanagibashi Rengo Market",
            "Uminonakamichi Seaside Park"
        ],
        why_budget_friendly="Affordable ramen and street food, compact walkable city, cheap beach access"
    )
]

def get_all_destinations() -> List[Destination]:
    """Return all destinations"""
    return DESTINATIONS

def get_destinations_by_budget(budget: BudgetCategory) -> List[Destination]:
    """Filter destinations by budget category"""
    return [d for d in DESTINATIONS if d.budget_category.value == budget.value]

def get_destinations_by_travel_type(travel_type: TravelType) -> List[Destination]:
    """Filter destinations by travel type"""
    return [d for d in DESTINATIONS if travel_type in d.travel_types]

def get_destinations_by_region(region: str) -> List[Destination]:
    """Filter destinations by region (domestic/international)"""
    return [d for d in DESTINATIONS if d.region == region]

def recommend_destinations(
    budget: Optional[BudgetCategory] = None,
    travel_types: Optional[List[TravelType]] = None,
    region: Optional[str] = None,
    season: Optional[Season] = None,
    max_results: int = 5
) -> List[Destination]:
    """
    Get personalized destination recommendations based on preferences

    Args:
        budget: Preferred budget category
        travel_types: List of preferred travel types
        region: 'domestic' or 'international'
        season: Preferred travel season
        max_results: Maximum number of recommendations to return

    Returns:
        List of matching destinations sorted by relevance
    """
    matching_destinations = []

    for destination in DESTINATIONS:
        score = 0

        # Budget match (highest priority)
        if budget and destination.budget_category == budget:
            score += 3
        elif budget and destination.budget_category.value == "affordable" and budget.value == "budget":
            score += 2  # Close budget match

        # Travel type matches
        if travel_types:
            for t in travel_types:
                if t in destination.travel_types:
                    score += 2

        # Region match
        if region and destination.region == region:
            score += 1

        # Season match
        if season and destination.best_season == season:
            score += 1
        elif season and destination.best_season == Season.ALL_YEAR:
            score += 1  # All year destinations always match

        if score > 0:
            matching_destinations.append((destination, score))

    # Sort by score and return top matches
    matching_destinations.sort(key=lambda x: x[1], reverse=True)
    return [d[0] for d in matching_destinations[:max_results]]


def format_destination_recommendation(destinations: List[Destination]) -> str:
    """
    Format destination recommendations into a user-friendly string

    Args:
        destinations: List of recommended destinations

    Returns:
        Formatted recommendation string with budget breakdowns
    """
    if not destinations:
        return "Maaf, belum menemukan destinasi yang cocok. Coba ubah preferensi Anda ya!"

    formatted = "\n\n" + "="*60 + "\n"
    formatted += "💰 REKOMENDASI DESTINASI BUDGET-FRIENDLY 💰\n"
    formatted += "="*60 + "\n\n"

    for i, dest in enumerate(destinations, 1):
        # Calculate total estimated daily cost
        total_daily = sum(dest.estimated_daily_cost.values())

        formatted += f"\n{i}. {dest.name}, {dest.country}\n"
        formatted += f"   📝 {dest.description}\n"
        formatted += f"   🏷️  Kategori Budget: {dest.budget_category.value.title()}\n"
        formatted += f"   💸 Estimasi Biaya/Hari: Rp {total_daily:,.0f}\n"
        formatted += f"      └─ Akomodasi: Rp {dest.estimated_daily_cost['accommodation']:,.0f} | "
        formatted += f"Makan: Rp {dest.estimated_daily_cost['food']:,.0f} | "
        formatted += f"Transport: Rp {dest.estimated_daily_cost['transport']:,.0f} | "
        formatted += f"Aktivitas: Rp {dest.estimated_daily_cost['activities']:,.0f}\n"
        formatted += f"   🎯 Tipe Liburan: {', '.join([t.value.title() for t in dest.travel_types])}\n"
        formatted += f"   ✨ Highlights:\n"
        for highlight in dest.highlights[:3]:  # Show top 3 highlights
            formatted += f"      • {highlight}\n"
        formatted += f"   💡 Kenapa Worth-It: {dest.why_budget_friendly}\n"

        if i < len(destinations):
            formatted += "\n" + "-"*60

    formatted += "\n\n💡 **Budget Tip**: Destinasi di atas dipilih berdasarkan nilai terbaik untuk setiap rupiah!"
    formatted += "\n🎯 **Next Step**: Mau cari penerbangan ke salah satu destinasi ini?"

    return formatted


def detect_travel_preferences(text: str) -> Dict:
    """
    Detect travel preferences from user text

    Args:
        text: User input text

    Returns:
        Dictionary with detected preferences
    """
    preferences = {}
    text_lower = text.lower()

    # Detect travel types
    travel_type_keywords = {
        TravelType.BEACH: ['pantai', 'beach', 'pula', 'gili', 'snorkeling', 'diving', 'laut'],
        TravelType.MOUNTAIN: ['gunung', 'mountain', 'hiking', 'trekking', 'naik gunung', 'pendakian'],
        TravelType.CULTURAL: ['budaya', 'cultural', 'sejarah', 'temple', 'candi', 'museum', 'keraton'],
        TravelType.CITY: ['kota', 'city', 'urban', 'mall', 'shopping', 'kuliner', 'jajan'],
        TravelType.ADVENTURE: ['adventure', 'petualangan', 'extreme', 'rafting', 'paralayang', 'offroad'],
        TravelType.NATURE: ['alam', 'nature', 'air terjun', 'waterfall', 'forest', 'hutan'],
        TravelType.FOODIE: ['kuliner', 'food', 'makanan', 'jajan', 'kulineran', 'wisata kuliner'],
        TravelType.SHOPPING: ['shopping', 'belanja', 'mall', 'outlet', 'oleh-oleh']
    }

    detected_types = []
    for travel_type, keywords in travel_type_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            detected_types.append(travel_type)

    if detected_types:
        preferences['travel_types'] = detected_types

    # Detect budget category
    budget_keywords = {
        BudgetCategory.BUDGET: ['murah', 'budget', 'hemat', 'irit', 'minimal', 'dibawah 500k', 'di bawah 500k'],
        BudgetCategory.AFFORDABLE: ['sedang', 'affordable', 'reasonable', '1 jutaan', '1jutaan', 'sejutaan'],
        BudgetCategory.MODERATE: ['menengah', 'moderate', '2 jutaan', '2jutaan'],
        BudgetCategory.SPLURGE: ['mahal', 'luxury', 'premium', 'mewah']
    }

    for budget_cat, keywords in budget_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            preferences['budget'] = budget_cat
            break

    # Detect region preference
    if any(word in text_lower for word in ['luar negeri', 'international', 'malaysia', 'thailand', 'vietnam']):
        preferences['region'] = 'international'
    elif any(word in text_lower for word in ['dalam negeri', 'indonesia', 'lokal', 'domestik']):
        preferences['region'] = 'domestic'

    return preferences