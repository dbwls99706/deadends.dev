"""Enriched country metadata: currency, emergency numbers, languages, embassies.

Complements SUPPORTED_COUNTRIES in country_canon_template.py. Used by the
country-aggregate JSON API and per-country llms.txt to carry structured
country-entity data that AI agents can consume directly (without a
separate lookup round-trip).

Sources: ISO 4217 (currency), national emergency service pages, ISO 639
(languages), home-country state-department listings (embassies URL).
"""

from __future__ import annotations

# ISO 4217 currencies + symbol + ISO 639 languages + emergency numbers
# + canonical government / tourist information URL. Keys are ISO 3166-1
# alpha-2 codes (lowercase). Only countries with country-scoped canons
# need an entry here; others fall back to empty metadata.

COUNTRY_METADATA: dict[str, dict] = {
    "ae": {
        "currency": {"code": "AED", "symbol": "د.إ", "name": "UAE Dirham"},
        "languages": ["ar", "en"],
        "emergency": {"police": "999", "ambulance": "998", "fire": "997"},
        "gov_url": "https://u.ae/en",
        "tourism_url": "https://www.visitdubai.com/en",
    },
    "ar": {
        "currency": {"code": "ARS", "symbol": "$", "name": "Argentine Peso"},
        "languages": ["es"],
        "emergency": {"police": "911", "ambulance": "107", "fire": "100"},
        "gov_url": "https://www.argentina.gob.ar/",
        "tourism_url": "https://www.argentina.travel/en",
    },
    "at": {
        "currency": {"code": "EUR", "symbol": "€", "name": "Euro"},
        "languages": ["de"],
        "emergency": {"police": "133", "ambulance": "144", "fire": "122", "unified": "112"},
        "gov_url": "https://www.bka.gv.at/en/home",
        "tourism_url": "https://www.austria.info/en",
    },
    "au": {
        "currency": {"code": "AUD", "symbol": "A$", "name": "Australian Dollar"},
        "languages": ["en"],
        "emergency": {"unified": "000", "non_emergency_police": "131444"},
        "gov_url": "https://www.australia.gov.au/",
        "tourism_url": "https://www.australia.com/en",
    },
    "bd": {
        "currency": {"code": "BDT", "symbol": "৳", "name": "Bangladesh Taka"},
        "languages": ["bn", "en"],
        "emergency": {"unified": "999"},
        "gov_url": "https://www.bangladesh.gov.bd/",
        "tourism_url": "https://tourism.gov.bd/",
    },
    "be": {
        "currency": {"code": "EUR", "symbol": "€", "name": "Euro"},
        "languages": ["nl", "fr", "de"],
        "emergency": {"unified": "112", "police": "101"},
        "gov_url": "https://www.belgium.be/en",
        "tourism_url": "https://visitbelgium.com/",
    },
    "br": {
        "currency": {"code": "BRL", "symbol": "R$", "name": "Brazilian Real"},
        "languages": ["pt"],
        "emergency": {"police": "190", "ambulance": "192", "fire": "193"},
        "gov_url": "https://www.gov.br/en/government",
        "tourism_url": "https://visitbrasil.com/",
    },
    "ca": {
        "currency": {"code": "CAD", "symbol": "C$", "name": "Canadian Dollar"},
        "languages": ["en", "fr"],
        "emergency": {"unified": "911"},
        "gov_url": "https://www.canada.ca/en.html",
        "tourism_url": "https://travel.destinationcanada.com/",
    },
    "ch": {
        "currency": {"code": "CHF", "symbol": "CHF", "name": "Swiss Franc"},
        "languages": ["de", "fr", "it", "rm"],
        "emergency": {"police": "117", "ambulance": "144", "fire": "118", "unified": "112"},
        "gov_url": "https://www.admin.ch/gov/en/start.html",
        "tourism_url": "https://www.myswitzerland.com/en-ch/",
    },
    "cl": {
        "currency": {"code": "CLP", "symbol": "$", "name": "Chilean Peso"},
        "languages": ["es"],
        "emergency": {"police": "133", "ambulance": "131", "fire": "132"},
        "gov_url": "https://www.gob.cl/",
        "tourism_url": "https://chile.travel/en/",
    },
    "cn": {
        "currency": {"code": "CNY", "symbol": "¥", "name": "Chinese Yuan Renminbi"},
        "languages": ["zh"],
        "emergency": {"police": "110", "ambulance": "120", "fire": "119"},
        "gov_url": "https://english.www.gov.cn/",
        "tourism_url": "https://en.cnta.gov.cn/",
    },
    "co": {
        "currency": {"code": "COP", "symbol": "$", "name": "Colombian Peso"},
        "languages": ["es"],
        "emergency": {"unified": "123"},
        "gov_url": "https://www.colombia.co/en/",
        "tourism_url": "https://www.colombia.travel/en",
    },
    "de": {
        "currency": {"code": "EUR", "symbol": "€", "name": "Euro"},
        "languages": ["de"],
        "emergency": {"unified": "112", "police": "110"},
        "gov_url": "https://www.bundesregierung.de/breg-en",
        "tourism_url": "https://www.germany.travel/en",
    },
    "dk": {
        "currency": {"code": "DKK", "symbol": "kr", "name": "Danish Krone"},
        "languages": ["da"],
        "emergency": {"unified": "112", "non_emergency_police": "114"},
        "gov_url": "https://www.denmark.dk/",
        "tourism_url": "https://www.visitdenmark.com/",
    },
    "eg": {
        "currency": {"code": "EGP", "symbol": "£", "name": "Egyptian Pound"},
        "languages": ["ar"],
        "emergency": {"police": "122", "ambulance": "123", "fire": "180"},
        "gov_url": "https://www.egypt.gov.eg/",
        "tourism_url": "https://egypt.travel/en/",
    },
    "es": {
        "currency": {"code": "EUR", "symbol": "€", "name": "Euro"},
        "languages": ["es", "ca", "gl", "eu"],
        "emergency": {"unified": "112"},
        "gov_url": "https://www.lamoncloa.gob.es/lang/en/Paginas/index.aspx",
        "tourism_url": "https://www.spain.info/en/",
    },
    "et": {
        "currency": {"code": "ETB", "symbol": "Br", "name": "Ethiopian Birr"},
        "languages": ["am", "en"],
        "emergency": {"police": "991", "ambulance": "907", "fire": "939"},
        "gov_url": "https://www.ethiopia.gov.et/",
        "tourism_url": "https://www.tourismethiopia.gov.et/",
    },
    "fi": {
        "currency": {"code": "EUR", "symbol": "€", "name": "Euro"},
        "languages": ["fi", "sv"],
        "emergency": {"unified": "112"},
        "gov_url": "https://valtioneuvosto.fi/en/frontpage",
        "tourism_url": "https://www.visitfinland.com/en/",
    },
    "fr": {
        "currency": {"code": "EUR", "symbol": "€", "name": "Euro"},
        "languages": ["fr"],
        "emergency": {"unified": "112", "police": "17", "ambulance": "15", "fire": "18"},
        "gov_url": "https://www.gouvernement.fr/en",
        "tourism_url": "https://www.france.fr/en",
    },
    "gr": {
        "currency": {"code": "EUR", "symbol": "€", "name": "Euro"},
        "languages": ["el"],
        "emergency": {"unified": "112", "police": "100", "ambulance": "166", "fire": "199"},
        "gov_url": "https://government.gov.gr/en/",
        "tourism_url": "https://www.visitgreece.gr/",
    },
    "hk": {
        "currency": {"code": "HKD", "symbol": "HK$", "name": "Hong Kong Dollar"},
        "languages": ["zh", "en"],
        "emergency": {"unified": "999", "non_emergency_police": "999"},
        "gov_url": "https://www.gov.hk/en/residents/",
        "tourism_url": "https://www.discoverhongkong.com/eng/",
    },
    "id": {
        "currency": {"code": "IDR", "symbol": "Rp", "name": "Indonesian Rupiah"},
        "languages": ["id"],
        "emergency": {"unified": "112", "police": "110", "ambulance": "118", "fire": "113"},
        "gov_url": "https://www.indonesia.go.id/",
        "tourism_url": "https://www.indonesia.travel/id/en",
    },
    "ie": {
        "currency": {"code": "EUR", "symbol": "€", "name": "Euro"},
        "languages": ["en", "ga"],
        "emergency": {"unified": "112", "alt": "999"},
        "gov_url": "https://www.gov.ie/en/",
        "tourism_url": "https://www.ireland.com/en-us/",
    },
    "il": {
        "currency": {"code": "ILS", "symbol": "₪", "name": "Israeli New Shekel"},
        "languages": ["he", "ar"],
        "emergency": {"police": "100", "ambulance": "101", "fire": "102"},
        "gov_url": "https://www.gov.il/en",
        "tourism_url": "https://www.goisrael.com/",
    },
    "in": {
        "currency": {"code": "INR", "symbol": "₹", "name": "Indian Rupee"},
        "languages": ["hi", "en"],
        "emergency": {"unified": "112", "police": "100", "ambulance": "108", "fire": "101"},
        "gov_url": "https://www.india.gov.in/",
        "tourism_url": "https://incredibleindia.gov.in/",
    },
    "it": {
        "currency": {"code": "EUR", "symbol": "€", "name": "Euro"},
        "languages": ["it"],
        "emergency": {"unified": "112"},
        "gov_url": "https://www.governo.it/en",
        "tourism_url": "https://www.italia.it/en",
    },
    "jp": {
        "currency": {"code": "JPY", "symbol": "¥", "name": "Japanese Yen"},
        "languages": ["ja"],
        "emergency": {"police": "110", "ambulance": "119", "fire": "119"},
        "gov_url": "https://www.japan.go.jp/",
        "tourism_url": "https://www.japan.travel/en/",
    },
    "ke": {
        "currency": {"code": "KES", "symbol": "KSh", "name": "Kenyan Shilling"},
        "languages": ["en", "sw"],
        "emergency": {"unified": "999", "alt": "112"},
        "gov_url": "https://www.mygov.go.ke/",
        "tourism_url": "https://magicalkenya.com/",
    },
    "kr": {
        "currency": {"code": "KRW", "symbol": "₩", "name": "South Korean Won"},
        "languages": ["ko"],
        "emergency": {"police": "112", "ambulance": "119", "fire": "119"},
        "gov_url": "https://www.korea.kr/eng/",
        "tourism_url": "https://english.visitkorea.or.kr/",
    },
    "ma": {
        "currency": {"code": "MAD", "symbol": "DH", "name": "Moroccan Dirham"},
        "languages": ["ar", "fr", "ber"],
        "emergency": {"police": "19", "ambulance": "15", "fire": "150"},
        "gov_url": "https://www.maroc.ma/en/",
        "tourism_url": "https://www.visitmorocco.com/en",
    },
    "mx": {
        "currency": {"code": "MXN", "symbol": "$", "name": "Mexican Peso"},
        "languages": ["es"],
        "emergency": {"unified": "911"},
        "gov_url": "https://www.gob.mx/",
        "tourism_url": "https://www.visitmexico.com/",
    },
    "my": {
        "currency": {"code": "MYR", "symbol": "RM", "name": "Malaysian Ringgit"},
        "languages": ["ms", "en"],
        "emergency": {"unified": "999"},
        "gov_url": "https://www.malaysia.gov.my/portal/index",
        "tourism_url": "https://www.malaysia.travel/",
    },
    "ng": {
        "currency": {"code": "NGN", "symbol": "₦", "name": "Nigerian Naira"},
        "languages": ["en"],
        "emergency": {"unified": "112"},
        "gov_url": "https://nigeria.gov.ng/",
        "tourism_url": "https://tourism.gov.ng/",
    },
    "nl": {
        "currency": {"code": "EUR", "symbol": "€", "name": "Euro"},
        "languages": ["nl"],
        "emergency": {"unified": "112", "non_emergency_police": "0900-8844"},
        "gov_url": "https://www.government.nl/",
        "tourism_url": "https://www.holland.com/global/tourism.htm",
    },
    "no": {
        "currency": {"code": "NOK", "symbol": "kr", "name": "Norwegian Krone"},
        "languages": ["no"],
        "emergency": {"police": "112", "ambulance": "113", "fire": "110"},
        "gov_url": "https://www.regjeringen.no/en/id4/",
        "tourism_url": "https://www.visitnorway.com/",
    },
    "nz": {
        "currency": {"code": "NZD", "symbol": "NZ$", "name": "New Zealand Dollar"},
        "languages": ["en", "mi"],
        "emergency": {"unified": "111"},
        "gov_url": "https://www.govt.nz/",
        "tourism_url": "https://www.newzealand.com/int/",
    },
    "pe": {
        "currency": {"code": "PEN", "symbol": "S/", "name": "Peruvian Sol"},
        "languages": ["es", "qu", "ay"],
        "emergency": {"police": "105", "ambulance": "106", "fire": "116"},
        "gov_url": "https://www.gob.pe/",
        "tourism_url": "https://www.peru.travel/en",
    },
    "ph": {
        "currency": {"code": "PHP", "symbol": "₱", "name": "Philippine Peso"},
        "languages": ["tl", "en"],
        "emergency": {"unified": "911"},
        "gov_url": "https://www.gov.ph/",
        "tourism_url": "https://itsmorefuninthephilippines.com/",
    },
    "pk": {
        "currency": {"code": "PKR", "symbol": "₨", "name": "Pakistani Rupee"},
        "languages": ["ur", "en"],
        "emergency": {"police": "15", "ambulance": "115", "fire": "16"},
        "gov_url": "https://www.pakistan.gov.pk/",
        "tourism_url": "https://www.tourism.gov.pk/",
    },
    "pl": {
        "currency": {"code": "PLN", "symbol": "zł", "name": "Polish Złoty"},
        "languages": ["pl"],
        "emergency": {"unified": "112"},
        "gov_url": "https://www.gov.pl/en",
        "tourism_url": "https://www.poland.travel/en/",
    },
    "pt": {
        "currency": {"code": "EUR", "symbol": "€", "name": "Euro"},
        "languages": ["pt"],
        "emergency": {"unified": "112"},
        "gov_url": "https://www.portugal.gov.pt/en/gc24",
        "tourism_url": "https://www.visitportugal.com/en",
    },
    "ru": {
        "currency": {"code": "RUB", "symbol": "₽", "name": "Russian Ruble"},
        "languages": ["ru"],
        "emergency": {"unified": "112", "police": "102", "ambulance": "103", "fire": "101"},
        "gov_url": "http://government.ru/en/",
        "tourism_url": "https://russia.travel/en/",
    },
    "sa": {
        "currency": {"code": "SAR", "symbol": "﷼", "name": "Saudi Riyal"},
        "languages": ["ar"],
        "emergency": {"police": "999", "ambulance": "997", "fire": "998"},
        "gov_url": "https://www.my.gov.sa/wps/portal/snp/main",
        "tourism_url": "https://www.visitsaudi.com/en",
    },
    "se": {
        "currency": {"code": "SEK", "symbol": "kr", "name": "Swedish Krona"},
        "languages": ["sv"],
        "emergency": {"unified": "112", "non_emergency_police": "114-14"},
        "gov_url": "https://www.government.se/",
        "tourism_url": "https://visitsweden.com/",
    },
    "sg": {
        "currency": {"code": "SGD", "symbol": "S$", "name": "Singapore Dollar"},
        "languages": ["en", "zh", "ms", "ta"],
        "emergency": {"police": "999", "ambulance": "995", "fire": "995"},
        "gov_url": "https://www.gov.sg/",
        "tourism_url": "https://www.visitsingapore.com/",
    },
    "th": {
        "currency": {"code": "THB", "symbol": "฿", "name": "Thai Baht"},
        "languages": ["th"],
        "emergency": {
            "police": "191", "ambulance": "1669",
            "fire": "199", "tourist_police": "1155",
        },
        "gov_url": "https://www.thaigov.go.th/main/contents/index",
        "tourism_url": "https://www.tourismthailand.org/",
    },
    "tr": {
        "currency": {"code": "TRY", "symbol": "₺", "name": "Turkish Lira"},
        "languages": ["tr"],
        "emergency": {"unified": "112"},
        "gov_url": "https://www.turkiye.gov.tr/en",
        "tourism_url": "https://goturkiye.com/",
    },
    "tw": {
        "currency": {"code": "TWD", "symbol": "NT$", "name": "New Taiwan Dollar"},
        "languages": ["zh"],
        "emergency": {"police": "110", "ambulance": "119", "fire": "119"},
        "gov_url": "https://www.taiwan.gov.tw/",
        "tourism_url": "https://eng.taiwan.net.tw/",
    },
    "uk": {
        "currency": {"code": "GBP", "symbol": "£", "name": "Pound Sterling"},
        "languages": ["en"],
        "emergency": {
            "unified": "999", "alt": "112",
            "non_emergency_police": "101",
            "non_emergency_medical": "111",
        },
        "gov_url": "https://www.gov.uk/",
        "tourism_url": "https://www.visitbritain.com/",
    },
    "us": {
        "currency": {"code": "USD", "symbol": "$", "name": "US Dollar"},
        "languages": ["en"],
        "emergency": {"unified": "911"},
        "gov_url": "https://www.usa.gov/",
        "tourism_url": "https://www.visittheusa.com/",
    },
    "vn": {
        "currency": {"code": "VND", "symbol": "₫", "name": "Vietnamese Dong"},
        "languages": ["vi"],
        "emergency": {"police": "113", "ambulance": "115", "fire": "114"},
        "gov_url": "https://chinhphu.vn/en",
        "tourism_url": "https://vietnam.travel/",
    },
    "za": {
        "currency": {"code": "ZAR", "symbol": "R", "name": "South African Rand"},
        "languages": ["en", "af", "zu", "xh", "st"],
        "emergency": {"police": "10111", "ambulance": "10177", "unified": "112"},
        "gov_url": "https://www.gov.za/",
        "tourism_url": "https://www.southafrica.net/",
    },
}


def get_country_metadata(country_code: str) -> dict:
    """Return enrichment metadata for an ISO alpha-2 country code.

    Returns an empty dict if the country has no known metadata (so the
    caller can merge without KeyError).
    """
    return COUNTRY_METADATA.get(country_code.lower(), {})
