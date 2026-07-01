"""
Simplified Ashtakoot Guna Milan (Kundli Matching) Engine.

This implements the classical 8-fold ("Ashtakoot") compatibility scoring used
in Vedic astrology, based on Rashi (moon sign) and Nakshatra (birth star) —
the two data points collected during registration. Full-chart (Navamsa /
Dasha) analysis requires precise birth-time ephemeris calculation and is
outside the scope of this automated screening tool; results here are a
standard first-pass compatibility screen, as commonly offered by matrimonial
platforms, and should be confirmed with a qualified astrologer (Pandit)
before finalising any match.
"""

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

RASHIS = [
    "Mesha (Aries)", "Vrishabha (Taurus)", "Mithuna (Gemini)", "Karka (Cancer)",
    "Simha (Leo)", "Kanya (Virgo)", "Tula (Libra)", "Vrishchika (Scorpio)",
    "Dhanu (Sagittarius)", "Makara (Capricorn)", "Kumbha (Aquarius)", "Meena (Pisces)",
]

# Gana classification per nakshatra (Deva / Manushya / Rakshasa)
GANA = {
    "Ashwini": "Deva", "Bharani": "Manushya", "Krittika": "Rakshasa", "Rohini": "Manushya",
    "Mrigashira": "Deva", "Ardra": "Manushya", "Punarvasu": "Deva", "Pushya": "Deva",
    "Ashlesha": "Rakshasa", "Magha": "Rakshasa", "Purva Phalguni": "Manushya",
    "Uttara Phalguni": "Manushya", "Hasta": "Deva", "Chitra": "Rakshasa", "Swati": "Deva",
    "Vishakha": "Rakshasa", "Anuradha": "Deva", "Jyeshtha": "Rakshasa", "Mula": "Rakshasa",
    "Purva Ashadha": "Manushya", "Uttara Ashadha": "Manushya", "Shravana": "Deva",
    "Dhanishta": "Rakshasa", "Shatabhisha": "Rakshasa", "Purva Bhadrapada": "Manushya",
    "Uttara Bhadrapada": "Manushya", "Revati": "Deva",
}

# Nadi classification (Aadi / Madhya / Antya)
NADI = {
    "Ashwini": "Aadi", "Bharani": "Madhya", "Krittika": "Antya", "Rohini": "Aadi",
    "Mrigashira": "Madhya", "Ardra": "Antya", "Punarvasu": "Aadi", "Pushya": "Madhya",
    "Ashlesha": "Antya", "Magha": "Aadi", "Purva Phalguni": "Madhya", "Uttara Phalguni": "Antya",
    "Hasta": "Aadi", "Chitra": "Madhya", "Swati": "Antya", "Vishakha": "Aadi",
    "Anuradha": "Madhya", "Jyeshtha": "Antya", "Mula": "Aadi", "Purva Ashadha": "Madhya",
    "Uttara Ashadha": "Antya", "Shravana": "Aadi", "Dhanishta": "Madhya", "Shatabhisha": "Antya",
    "Purva Bhadrapada": "Aadi", "Uttara Bhadrapada": "Madhya", "Revati": "Antya",
}

# Yoni (animal symbol) classification
YONI = {
    "Ashwini": "Horse", "Bharani": "Elephant", "Krittika": "Goat", "Rohini": "Serpent",
    "Mrigashira": "Serpent", "Ardra": "Dog", "Punarvasu": "Cat", "Pushya": "Goat",
    "Ashlesha": "Cat", "Magha": "Rat", "Purva Phalguni": "Rat", "Uttara Phalguni": "Cow",
    "Hasta": "Buffalo", "Chitra": "Tiger", "Swati": "Buffalo", "Vishakha": "Tiger",
    "Anuradha": "Deer", "Jyeshtha": "Deer", "Mula": "Dog", "Purva Ashadha": "Monkey",
    "Uttara Ashadha": "Mongoose", "Shravana": "Monkey", "Dhanishta": "Lion",
    "Shatabhisha": "Horse", "Purva Bhadrapada": "Lion", "Uttara Bhadrapada": "Cow", "Revati": "Elephant",
}

MAX_GUNA = {"Varna": 1, "Vashya": 2, "Tara": 3, "Yoni": 4, "Graha_Maitri": 5, "Gana": 6, "Bhakoot": 7, "Nadi": 8}
MAX_TOTAL = sum(MAX_GUNA.values())  # 36


def _index(lst, value):
    try:
        return lst.index(value)
    except (ValueError, AttributeError):
        return None


def _score_varna(rashi_bride, rashi_groom):
    # Simplified varna by rashi group; always grants baseline points unless data missing
    return MAX_GUNA["Varna"] if rashi_bride and rashi_groom else 0


def _score_tara(nak_bride, nak_groom):
    ib, ig = _index(NAKSHATRAS, nak_bride), _index(NAKSHATRAS, nak_groom)
    if ib is None or ig is None:
        return 0
    diff = (ig - ib) % 27
    tara = (diff % 9)
    return MAX_GUNA["Tara"] if tara not in (2, 4, 6, 8) else 1


def _score_yoni(nak_bride, nak_groom):
    yb, yg = YONI.get(nak_bride), YONI.get(nak_groom)
    if not yb or not yg:
        return 0
    if yb == yg:
        return MAX_GUNA["Yoni"]
    friendly_pairs = {("Cow", "Buffalo"), ("Horse", "Elephant"), ("Deer", "Monkey")}
    pair = tuple(sorted([yb, yg]))
    if pair in {tuple(sorted(p)) for p in friendly_pairs}:
        return 3
    return 2


def _score_gana(nak_bride, nak_groom):
    gb, gg = GANA.get(nak_bride), GANA.get(nak_groom)
    if not gb or not gg:
        return 0
    if gb == gg:
        return MAX_GUNA["Gana"]
    if {gb, gg} == {"Deva", "Manushya"}:
        return 5
    if {gb, gg} == {"Manushya", "Rakshasa"}:
        return 3
    return 0  # Deva-Rakshasa clash


def _score_nadi(nak_bride, nak_groom):
    nb, ng = NADI.get(nak_bride), NADI.get(nak_groom)
    if not nb or not ng:
        return 0
    return 0 if nb == ng else MAX_GUNA["Nadi"]  # same Nadi = dosha (0 points)


def _score_bhakoot(rashi_bride, rashi_groom):
    ib, ig = _index(RASHIS, rashi_bride), _index(RASHIS, rashi_groom)
    if ib is None or ig is None:
        return 0
    diff = abs(ib - ig) % 12
    bad = {5, 6, 8}  # 6/8 and 2/12 style clashes approximated
    return 0 if diff in bad else MAX_GUNA["Bhakoot"]


def _score_vashya(rashi_bride, rashi_groom):
    if not rashi_bride or not rashi_groom:
        return 0
    return MAX_GUNA["Vashya"] if rashi_bride != rashi_groom else MAX_GUNA["Vashya"]


def _score_graha_maitri(rashi_bride, rashi_groom):
    ib, ig = _index(RASHIS, rashi_bride), _index(RASHIS, rashi_groom)
    if ib is None or ig is None:
        return 0
    diff = abs(ib - ig) % 12
    return MAX_GUNA["Graha_Maitri"] if diff in (0, 3, 4, 7, 9) else 2


def match_profiles(bride_profile, groom_profile):
    """Returns a dict with total score, percentage, per-guna breakdown, doshas and recommendation."""
    nb, ng = bride_profile.nakshatra, groom_profile.nakshatra
    rb, rg = bride_profile.rashi, groom_profile.rashi

    breakdown = {
        "Varna (Ego/Nature)": (_score_varna(rb, rg), MAX_GUNA["Varna"]),
        "Vashya (Dominance)": (_score_vashya(rb, rg), MAX_GUNA["Vashya"]),
        "Tara (Birth Star)": (_score_tara(nb, ng), MAX_GUNA["Tara"]),
        "Yoni (Sexual Compatibility)": (_score_yoni(nb, ng), MAX_GUNA["Yoni"]),
        "Graha Maitri (Mental Compatibility)": (_score_graha_maitri(rb, rg), MAX_GUNA["Graha_Maitri"]),
        "Gana (Temperament)": (_score_gana(nb, ng), MAX_GUNA["Gana"]),
        "Bhakoot (Love & Prosperity)": (_score_bhakoot(rb, rg), MAX_GUNA["Bhakoot"]),
        "Nadi (Health & Genes)": (_score_nadi(nb, ng), MAX_GUNA["Nadi"]),
    }

    total = sum(v[0] for v in breakdown.values())
    percentage = round((total / MAX_TOTAL) * 100, 1)

    doshas = []
    if breakdown["Nadi (Health & Genes)"][0] == 0:
        doshas.append("Nadi Dosha (same Nadi) — may affect health/progeny; often needs remedial review")
    if breakdown["Gana (Temperament)"][0] == 0:
        doshas.append("Gana Dosha (Deva-Rakshasa clash) — possible temperament mismatch")
    if breakdown["Bhakoot (Love & Prosperity)"][0] == 0:
        doshas.append("Bhakoot Dosha — may indicate financial/relationship friction")
    if groom_profile.manglik == "Yes" and bride_profile.manglik != "Yes":
        doshas.append("Manglik Mismatch — groom is Manglik, bride is not")
    if bride_profile.manglik == "Yes" and groom_profile.manglik != "Yes":
        doshas.append("Manglik Mismatch — bride is Manglik, groom is not")

    if percentage >= 75:
        recommendation = "Excellent Match — highly recommended"
    elif percentage >= 55:
        recommendation = "Good Match — recommended with minor considerations"
    elif percentage >= 35:
        recommendation = "Average Match — consult an astrologer before proceeding"
    else:
        recommendation = "Not Recommended — significant doshas present"

    if not (nb and ng and rb and rg):
        recommendation = "Insufficient Kundli data (Rashi/Nakshatra) for one or both profiles"

    return {
        "total_score": total,
        "max_score": MAX_TOTAL,
        "percentage": percentage,
        "breakdown": breakdown,
        "doshas": doshas,
        "recommendation": recommendation,
    }
