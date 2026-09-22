"""Name mappings shared by the loaders, the feature builder and the notebooks.

Everything that renames or groups a category or a counterpart lives here, so a
decision is made once and every notebook sees the same names.
"""

# --------------------------------------------------------------------------- categories
# The SoW files carry a few categories in a second spelling (capitalised, sometimes
# German). They hold a few hundred CHF a month and belong to an existing category.
CATEGORY_ALIASES = {
    "lebensmittel": "groceries",
    "restaurant": "restaurants",
    "hotel": "holidays",
    "fitness": "wellness",
}

# The same duplicates exist as columns in customer_data.csv.
CUSTOMER_COLUMN_MERGES = {
    "cat_lebensmittel": "cat_groceries",
    "cat_restaurant": "cat_restaurants",
    "cat_hotel": "cat_holidays",
    "cat_fitness": "cat_wellness",
}

# --------------------------------------------------------------------------- counterparts
# Same merchant, two spellings in the card descriptor.
COUNTERPART_ALIASES = {
    "brezelkönig": "brezelkonig",
    "mcdonald's": "mcdonalds",
    "amzn": "amazon",
    "netflix.com": "netflix",
}

# Counterparts that are not merchants. A "sumup" transaction is a small shop or
# restaurant using a SumUp terminal, "paypal" is a wallet in front of an unknown
# merchant, "twint" is a P2P transfer or a wallet payment.
PAYMENT_PROVIDERS = {"sumup", "paypal", "twint"}

# Counterparts that are other financial providers: money leaving the bank.
FINANCIAL_PROVIDERS = {"revolut", "binance", "coinbase", "postfinance", "ubs", "kantonalbank"}


def counterpart_type(name: str) -> str:
    if name == "other":
        return "other"
    if name in PAYMENT_PROVIDERS:
        return "payment_provider"
    if name in FINANCIAL_PROVIDERS:
        return "financial_provider"
    return "merchant"


# --------------------------------------------------------------------------- groups per category
# Used for the share-of-wallet charts. Anything not listed falls into "other".
LEAKAGE_GROUPS = {
    "revolut": "revolut",
    "binance": "crypto exchanges",
    "coinbase": "crypto exchanges",
    "postfinance": "traditional banks",
    "ubs": "traditional banks",
    "kantonalbank": "traditional banks",
    "twint": "twint",
}

GROCERY_GROUPS = {
    "coop": "coop",
    "migros": "migros",
    "lidl": "discounter",
    "aldi": "discounter",
    "denner": "discounter",
    "volg": "regional",
    "spar": "regional",
    "avec": "convenience",
    "migrolino": "convenience",
    "kkiosk": "convenience",
    "selecta": "convenience",
}

TRANSPORT_GROUPS = {
    **{k: "fuel" for k in ["avia", "migrol", "shell", "agrola", "socar", "eni", "tamoil", "coop", "landi"]},
    **{k: "public transport" for k in ["sbb", "fairtiq", "zvv", "vbz"]},
    **{k: "micromobility" for k in ["lime", "tier", "voi"]},
    **{k: "ride hailing" for k in ["uber", "bolt"]},
    **{k: "parking" for k in ["parkingpay", "easypark"]},
}

ENTERTAINMENT_GROUPS = {
    **{k: "gambling" for k in ["interwetten", "swiss casinos", "mycasino.ch", "swisslos", "jackpots.ch"]},
    **{k: "streaming" for k in ["netflix", "youtube", "google"]},
    **{k: "gaming" for k in ["steam", "playstationnetwork", "microsoft"]},
}

COUNTERPART_GROUPS = {
    "cash": LEAKAGE_GROUPS,
    "savings": LEAKAGE_GROUPS,
    "groceries": GROCERY_GROUPS,
    "transport": TRANSPORT_GROUPS,
    "entertainment": ENTERTAINMENT_GROUPS,
}


def counterpart_group(category: str, name: str) -> str:
    return COUNTERPART_GROUPS.get(category, {}).get(name, "other")
