"""Nearby Transit Service — maps travel destinations without direct commercial airports
to their nearest airport and railway station gateways.
"""
from typing import Any

# Registry of destinations that do not have their own commercial airport,
# with verified distance, transfer tip, and nearest railway station.
NEARBY_TRANSIT_REGISTRY: dict[str, dict[str, Any]] = {
    "hampi": {
        "has_direct_airport": False,
        "destination_name": "Hampi",
        "nearby_airport": {
            "name": "Jindal Vijayanagar Airport (VDY) / Hubli Airport (HBX)",
            "code": "VDY",
            "alt_code": "HBX",
            "distance": "~35 km (VDY) • ~145 km (HBX)",
            "transfer_tip": "Prepaid cabs, local taxis, and KSRTC buses operate regularly to Hampi ruins.",
        },
        "nearby_railway": {
            "name": "Hospet Junction (HPT)",
            "code": "HPT",
            "distance": "~13 km (20 mins drive)",
            "transfer_tip": "Auto-rickshaws, shared cabs, and local buses connect Hospet station directly to Hampi bazaar.",
        },
        "notice": "Hampi does not have its own commercial airport. Flights land at Jindal Vijayanagar (VDY, ~35 km) or Hubli (HBX). Nearest railhead is Hospet Junction (HPT, ~13 km).",
    },
    "manali": {
        "has_direct_airport": False,
        "destination_name": "Manali",
        "nearby_airport": {
            "name": "Kullu-Bhuntar Airport (KUU) / Chandigarh International (IXC)",
            "code": "KUU",
            "alt_code": "IXC",
            "distance": "~50 km (KUU) • ~280 km (IXC)",
            "transfer_tip": "Mountain taxis run from Bhuntar (1.5 hrs). HRTC Volvo luxury overnight buses run continuously from Chandigarh.",
        },
        "nearby_railway": {
            "name": "Chandigarh Junction (CDG) / Kalka (KLK)",
            "code": "CDG",
            "distance": "~280 km (approx. 7–8 hrs scenic drive via Kiratpur-Manali highway)",
            "transfer_tip": "Broad-gauge rail terminus with seamless Volvo coach and private taxi connections.",
        },
        "notice": "Manali does not have its own airport. Flights land at Kullu-Bhuntar (KUU, ~50 km) or Chandigarh (IXC). Nearest broad-gauge railhead is Chandigarh (CDG).",
    },
    "rishikesh": {
        "has_direct_airport": False,
        "destination_name": "Rishikesh",
        "nearby_airport": {
            "name": "Dehradun Jolly Grant Airport (DED)",
            "code": "DED",
            "distance": "~20 km (35–45 mins drive via NH7)",
            "transfer_tip": "Prepaid airport taxis and cabs drive directly to Laxman Jhula, Tapovan, and Ram Jhula.",
        },
        "nearby_railway": {
            "name": "Yog Nagari Rishikesh (YNRK) / Haridwar Junction (HW)",
            "code": "YNRK",
            "distance": "~5 km (YNRK) • ~25 km (HW)",
            "transfer_tip": "Direct express and Vande Bharat trains connect Haridwar and Yog Nagari Rishikesh to Delhi and Mumbai.",
        },
        "notice": "Rishikesh has no commercial airport. Flights arrive at Dehradun Jolly Grant Airport (DED, ~20 km). Direct trains serve Haridwar (HW) and Yog Nagari Rishikesh (YNRK).",
    },
    "ooty": {
        "has_direct_airport": False,
        "destination_name": "Ooty (Udhagamandalam)",
        "nearby_airport": {
            "name": "Coimbatore International Airport (CJB)",
            "code": "CJB",
            "distance": "~85 km (approx. 2.5–3 hrs scenic ghat drive)",
            "transfer_tip": "Prepaid taxis, Nilgiri cabs, and TNSTC buses operate 24/7 from Coimbatore.",
        },
        "nearby_railway": {
            "name": "Mettupalayam (MTP) / Coimbatore Junction (CBE)",
            "code": "CBE",
            "distance": "~50 km (MTP) • ~85 km (CBE)",
            "transfer_tip": "Connect to Ooty via the famous UNESCO Nilgiri Mountain Toy Train from Mettupalayam.",
        },
        "notice": "Ooty does not have an airport. Flights arrive at Coimbatore (CJB, ~85 km). Nearest mainline railway station is Coimbatore (CBE) and toy train link at Mettupalayam (MTP).",
    },
    "munnar": {
        "has_direct_airport": False,
        "destination_name": "Munnar",
        "nearby_airport": {
            "name": "Cochin International Airport (COK)",
            "code": "COK",
            "distance": "~110 km (approx. 3.5 hrs scenic hill drive)",
            "transfer_tip": "Prepaid airport taxis, hill station cabs, and KSRTC buses run through tea-estate hills.",
        },
        "nearby_railway": {
            "name": "Aluva (AWY) / Ernakulam Junction (ERS)",
            "code": "ERS",
            "distance": "~110 km (approx. 3.5 hrs drive)",
            "transfer_tip": "Aluva and Ernakulam have round-the-clock taxi and bus connections to Munnar.",
        },
        "notice": "Munnar has no airport or railway. Fly into Cochin (COK, ~110 km) or take a train to Aluva / Ernakulam (ERS, ~110 km) followed by a road taxi.",
    },
    "coorg": {
        "has_direct_airport": False,
        "destination_name": "Coorg (Kodagu)",
        "nearby_airport": {
            "name": "Kannur International (CNN) / Mangalore (IXE) / Bengaluru (BLR)",
            "code": "CNN",
            "alt_code": "IXE",
            "distance": "~90 km (CNN) • ~140 km (IXE) • ~260 km (BLR)",
            "transfer_tip": "Scenic highway taxis and KSRTC Airavat / Club Class luxury buses operate from Bengaluru and Mysuru.",
        },
        "nearby_railway": {
            "name": "Mysuru Junction (MYS) / Hassan (HAS)",
            "code": "MYS",
            "distance": "~120 km (approx. 2.5 hrs drive)",
            "transfer_tip": "Mysuru is the closest major railhead with continuous bus and cab links to Madikeri and Kushalnagar.",
        },
        "notice": "Coorg has no airport. Nearest airports are Kannur (CNN, ~90 km) and Mangalore (IXE, ~140 km). Nearest railway station is Mysuru (MYS, ~120 km).",
    },
    "gokarna": {
        "has_direct_airport": False,
        "destination_name": "Gokarna",
        "nearby_airport": {
            "name": "Goa International Airport (GOI / GOX)",
            "code": "GOI",
            "alt_code": "GOX",
            "distance": "~140 km (approx. 3 hrs coastal highway drive)",
            "transfer_tip": "Prepaid taxis, coastal rental cars, and KSRTC interstate buses available from Goa.",
        },
        "nearby_railway": {
            "name": "Gokarna Road (GOK) / Kumta (KT) / Ankola (ANKL)",
            "code": "GOK",
            "distance": "~9 km (GOK) • ~30 km (KT)",
            "transfer_tip": "Konkan Railway passenger and express trains halt directly at Gokarna Road station with local autos to Om Beach.",
        },
        "notice": "Gokarna has no commercial airport. Flights arrive at Goa (GOI/GOX, ~140 km). Direct trains arrive at Gokarna Road (GOK, ~9 km) on the Konkan Railway line.",
    },
    "lonavala": {
        "has_direct_airport": False,
        "destination_name": "Lonavala",
        "nearby_airport": {
            "name": "Pune International (PNQ) / Mumbai CSMIA (BOM)",
            "code": "PNQ",
            "alt_code": "BOM",
            "distance": "~70 km (PNQ) • ~90 km (BOM)",
            "transfer_tip": "Fast 1.5–2 hr drive via the Mumbai-Pune Expressway with app cabs and cool-cabs.",
        },
        "nearby_railway": {
            "name": "Lonavala Railway Station (LNL)",
            "code": "LNL",
            "distance": "~1 km (Inside town)",
            "transfer_tip": "Directly connected; every Mumbai–Pune Deccan Queen, Intercity, and Express train stops at Lonavala.",
        },
        "notice": "Lonavala is served by Pune Airport (PNQ, ~70 km) and Mumbai (BOM, ~90 km). Lonavala has its own railway station (LNL) on the central rail corridor.",
    },
    "mount abu": {
        "has_direct_airport": False,
        "destination_name": "Mount Abu",
        "nearby_airport": {
            "name": "Udaipur Maharana Pratap (UDR) / Ahmedabad (AMD)",
            "code": "UDR",
            "alt_code": "AMD",
            "distance": "~185 km (UDR) • ~220 km (AMD)",
            "transfer_tip": "Taxis, RSRTC silver line deluxe buses, and rental cars available from Udaipur and Ahmedabad.",
        },
        "nearby_railway": {
            "name": "Abu Road Railway Station (ABR)",
            "code": "ABR",
            "distance": "~28 km (approx. 45 min ghat ascent)",
            "transfer_tip": "Mountain jeeps, shared taxis, and local state buses run continuously up to Nakki Lake from Abu Road.",
        },
        "notice": "Mount Abu has no airport. Fly into Udaipur (UDR, ~185 km) or Ahmedabad (AMD). Nearest railhead is Abu Road (ABR, ~28 km).",
    },
    "kasol": {
        "has_direct_airport": False,
        "destination_name": "Kasol (Parvati Valley)",
        "nearby_airport": {
            "name": "Kullu-Bhuntar Airport (KUU) / Chandigarh (IXC)",
            "code": "KUU",
            "alt_code": "IXC",
            "distance": "~31 km (KUU) • ~275 km (IXC)",
            "transfer_tip": "Local mountain taxis and HRTC buses run regularly from Bhuntar up Parvati Valley.",
        },
        "nearby_railway": {
            "name": "Chandigarh Junction (CDG)",
            "code": "CDG",
            "distance": "~275 km",
            "transfer_tip": "Overnight Volvo buses operate daily from Delhi / Chandigarh to Bhuntar, then 45 min cab to Kasol.",
        },
        "notice": "Kasol has no airport. Nearest airport is Kullu-Bhuntar (KUU, ~31 km). Nearest major railhead is Chandigarh (CDG, ~275 km).",
    },
    "darjeeling": {
        "has_direct_airport": False,
        "destination_name": "Darjeeling",
        "nearby_airport": {
            "name": "Bagdogra Airport (IXB)",
            "code": "IXB",
            "distance": "~70 km (approx. 2.5–3 hrs hill climb via Rohini)",
            "transfer_tip": "Prepaid airport taxis and shared Sumo cabs operate directly from Bagdogra arrival lounge.",
        },
        "nearby_railway": {
            "name": "New Jalpaiguri Junction (NJP)",
            "code": "NJP",
            "distance": "~75 km",
            "transfer_tip": "Major North-East rail junction connecting Delhi, Kolkata, and Guwahati. UNESCO Toy Train ascends to Darjeeling from NJP.",
        },
        "notice": "Darjeeling has no commercial airport. Flights arrive at Bagdogra (IXB, ~70 km). Nearest broad-gauge railhead is New Jalpaiguri (NJP, ~75 km).",
    },
    "gangtok": {
        "has_direct_airport": False,
        "destination_name": "Gangtok (Sikkim)",
        "nearby_airport": {
            "name": "Pakyong Airport (PYG) / Bagdogra (IXB)",
            "code": "IXB",
            "alt_code": "PYG",
            "distance": "~30 km (PYG) • ~125 km (IXB, approx. 4 hrs via NH10)",
            "transfer_tip": "Shared and private SUV cabs operate continuously from Bagdogra along the scenic Teesta river.",
        },
        "nearby_railway": {
            "name": "New Jalpaiguri Junction (NJP) / Siliguri (SGUJ)",
            "code": "NJP",
            "distance": "~120 km",
            "transfer_tip": "Sikkim Nationalised Transport (SNT) deluxe buses and prepaid cabs connect NJP directly to Gangtok.",
        },
        "notice": "Gangtok is served by Bagdogra Airport (IXB, ~125 km) or Pakyong (PYG). Nearest railhead is New Jalpaiguri (NJP, ~120 km).",
    },
    "pondicherry": {
        "has_direct_airport": False,
        "destination_name": "Puducherry (Pondicherry)",
        "nearby_airport": {
            "name": "Chennai International Airport (MAA) / Puducherry (PNY)",
            "code": "MAA",
            "distance": "~135 km (approx. 2.5 hrs via East Coast Road)",
            "transfer_tip": "Prepaid airport taxis and PRTC express buses drive along the scenic coastal highway.",
        },
        "nearby_railway": {
            "name": "Puducherry Railway Station (PDY) / Villupuram Junction (VM)",
            "code": "PDY",
            "distance": "~1 km (PDY) • ~38 km (VM)",
            "transfer_tip": "Villupuram is a major rail junction with continuous local trains, buses, and cabs to White Town.",
        },
        "notice": "Pondicherry is primarily served by Chennai Airport (MAA, ~135 km). Nearest railhead is Puducherry (PDY) or Villupuram (VM, ~38 km).",
    },
    "alleppey": {
        "has_direct_airport": False,
        "destination_name": "Alleppey (Alappuzha)",
        "nearby_airport": {
            "name": "Cochin International Airport (COK)",
            "code": "COK",
            "distance": "~85 km (approx. 2 hrs drive via NH66)",
            "transfer_tip": "Prepaid airport taxis drive directly to houseboat boarding points at Punnamada Lake.",
        },
        "nearby_railway": {
            "name": "Alappuzha Railway Station (ALLP)",
            "code": "ALLP",
            "distance": "~3 km",
            "transfer_tip": "Auto-rickshaws and cabs connect the station to houseboats and backwater resorts in 10 minutes.",
        },
        "notice": "Alleppey has no airport. Fly into Cochin (COK, ~85 km). Alappuzha has its own railway station (ALLP, ~3 km).",
    },
    "wayanad": {
        "has_direct_airport": False,
        "destination_name": "Wayanad",
        "nearby_airport": {
            "name": "Calicut / Kozhikode International Airport (CCJ) / Kannur (CNN)",
            "code": "CCJ",
            "distance": "~85 km (approx. 2.5 hrs via Thamarassery ghat)",
            "transfer_tip": "Ghat road taxis and KSRTC buses connect Kozhikode directly to Kalpetta and Sulthan Bathery.",
        },
        "nearby_railway": {
            "name": "Kozhikode Railway Station (CLT)",
            "code": "CLT",
            "distance": "~85 km",
            "transfer_tip": "Primary railhead for Wayanad with frequent buses and private tourist vehicles.",
        },
        "notice": "Wayanad has no airport or railway. Nearest airport is Calicut (CCJ, ~85 km) and nearest railway station is Kozhikode (CLT, ~85 km).",
    },
    "kodaikanal": {
        "has_direct_airport": False,
        "destination_name": "Kodaikanal",
        "nearby_airport": {
            "name": "Madurai Airport (IXM) / Coimbatore (CJB)",
            "code": "IXM",
            "distance": "~120 km (approx. 3 hrs hill drive)",
            "transfer_tip": "Tourist cabs and TNSTC buses climb up the Palani hills directly to Kodai Lake.",
        },
        "nearby_railway": {
            "name": "Kodai Road Railway Station (KQN) / Dindigul (DG)",
            "code": "KQN",
            "distance": "~80 km (approx. 2 hrs drive)",
            "transfer_tip": "Taxis and local buses wait at Kodai Road station for all arriving express trains.",
        },
        "notice": "Kodaikanal has no airport. Nearest airport is Madurai (IXM, ~120 km). Nearest railway station is Kodai Road (KQN, ~80 km).",
    },
    "mahabaleshwar": {
        "has_direct_airport": False,
        "destination_name": "Mahabaleshwar",
        "nearby_airport": {
            "name": "Pune International Airport (PNQ)",
            "code": "PNQ",
            "distance": "~120 km (approx. 3 hrs drive)",
            "transfer_tip": "Taxis and MSRTC AC Shivshahi buses operate from Swargate Pune via Wai and Panchgani.",
        },
        "nearby_railway": {
            "name": "Wathar (WTR) / Satara (STR) / Pune Junction (PUNE)",
            "code": "PNQ",
            "distance": "~60 km (Satara) • ~120 km (Pune)",
            "transfer_tip": "Pune and Satara provide 24/7 taxi links up the Western Ghats.",
        },
        "notice": "Mahabaleshwar has no airport. Nearest airport is Pune (PNQ, ~120 km). Nearest major railhead is Pune Junction or Satara.",
    },
    "nainital": {
        "has_direct_airport": False,
        "destination_name": "Nainital",
        "nearby_airport": {
            "name": "Pantnagar Airport (PGH) / Delhi IGI (DEL)",
            "code": "PGH",
            "distance": "~70 km (PGH) • ~300 km (DEL)",
            "transfer_tip": "Mountain taxis and Uttarakhand Roadways Volvo coaches available.",
        },
        "nearby_railway": {
            "name": "Kathgodam Railway Station (KGM)",
            "code": "KGM",
            "distance": "~35 km (approx. 1 hr scenic ascent)",
            "transfer_tip": "Ranikhet Express, Shatabdi, and Kathgodam Express arrive with shared jeeps straight to Mallital.",
        },
        "notice": "Nainital has no airport. Nearest airport is Pantnagar (PGH, ~70 km). Nearest railway station is Kathgodam (KGM, ~35 km).",
    },
    "mussoorie": {
        "has_direct_airport": False,
        "destination_name": "Mussoorie",
        "nearby_airport": {
            "name": "Dehradun Jolly Grant Airport (DED)",
            "code": "DED",
            "distance": "~60 km (approx. 1.5–2 hrs drive)",
            "transfer_tip": "Prepaid airport taxis drive directly up to Picture Palace / Library Chowk.",
        },
        "nearby_railway": {
            "name": "Dehradun Railway Station (DDN)",
            "code": "DDN",
            "distance": "~35 km (approx. 1 hr drive)",
            "transfer_tip": "Taxis and GMVN hill buses depart right outside Dehradun station.",
        },
        "notice": "Mussoorie has no airport. Nearest airport is Dehradun Jolly Grant (DED, ~60 km). Nearest railway station is Dehradun (DDN, ~35 km).",
    },
    "alibaug": {
        "has_direct_airport": False,
        "destination_name": "Alibaug",
        "nearby_airport": {
            "name": "Mumbai CSMIA (BOM)",
            "code": "BOM",
            "distance": "~100 km (or 1 hr speed-boat from Gateway of India)",
            "transfer_tip": "Fastest route: 60-min Ro-Pax or speed-boat ferry from Mumbai Gateway/Bhaucha Dhakka to Mandwa, then 20 min cab.",
        },
        "nearby_railway": {
            "name": "Roha (ROHA) / Panvel Junction (PNVL)",
            "code": "PNVL",
            "distance": "~40 km (Roha) • ~65 km (Panvel)",
            "transfer_tip": "Panvel connects to suburban Mumbai rail; ferry is the preferred travel route.",
        },
        "notice": "Alibaug has no airport. Nearest airport is Mumbai (BOM). Fastest access is the 60-min ferry from Mumbai to Mandwa jetty.",
    },
    "interlaken": {
        "has_direct_airport": False,
        "destination_name": "Interlaken",
        "nearby_airport": {
            "name": "Bern Belp (BRN) / Zurich Airport (ZRH)",
            "code": "ZRH",
            "distance": "~50 km (BRN) • ~135 km (ZRH)",
            "transfer_tip": "Direct SBB Swiss Federal Railways trains connect Zurich Airport directly to Interlaken Ost in 2 hours.",
        },
        "nearby_railway": {
            "name": "Interlaken Ost Railway Station",
            "code": "ZRH",
            "distance": "In town center",
            "transfer_tip": "Primary alpine rail hub connecting Jungfraujoch, Grindelwald, and Lauterbrunnen.",
        },
        "notice": "Interlaken has no commercial airport. Flights land at Zurich (ZRH) or Bern. Direct SBB trains connect directly into Interlaken Ost.",
    },
    "positano": {
        "has_direct_airport": False,
        "destination_name": "Positano (Amalfi Coast)",
        "nearby_airport": {
            "name": "Naples International Airport (NAP) / Rome FCO",
            "code": "NAP",
            "distance": "~60 km (NAP) • ~270 km (FCO)",
            "transfer_tip": "Hydrofoil ferries or Sita coastal buses operate along the cliffside from Salerno and Sorrento.",
        },
        "nearby_railway": {
            "name": "Salerno / Sorrento Railway Station",
            "code": "NAP",
            "distance": "~35 km (Sorrento)",
            "transfer_tip": "Circumvesuviana trains connect Naples to Sorrento, followed by a scenic coastal bus or boat.",
        },
        "notice": "Positano has no airport. Flights land at Naples (NAP, ~60 km). Nearest railway terminals are Sorrento and Salerno.",
    },
    "hallstatt": {
        "has_direct_airport": False,
        "destination_name": "Hallstatt",
        "nearby_airport": {
            "name": "Salzburg Airport (SZG) / Vienna (VIE)",
            "code": "SZG",
            "distance": "~80 km (SZG) • ~290 km (VIE)",
            "transfer_tip": "ÖBB Austrian Federal Railways trains connect via Attnang-Puchheim, followed by a passenger ferry across Lake Hallstatt.",
        },
        "nearby_railway": {
            "name": "Hallstatt Bahnhst (Ferry Station)",
            "code": "SZG",
            "distance": "Across lake (5 min ferry)",
            "transfer_tip": "Iconic passenger boat 'Stefanie' meets every arriving train to ferry travelers across the lake.",
        },
        "notice": "Hallstatt has no airport. Flights land at Salzburg (SZG, ~80 km). Arrive via ÖBB train and cross via the lake ferry.",
    },
}


def get_nearby_transit(destination: str | None) -> dict[str, Any] | None:
    """Inspects if the given destination has no direct airport, returning verified
    nearby airport and railway station transit details.
    """
    if not destination or not str(destination).strip():
        return None

    dest_lower = destination.strip().lower()

    # 1. Exact or substring match in verified registry
    for key, data in NEARBY_TRANSIT_REGISTRY.items():
        if key in dest_lower or dest_lower in key:
            return data

    return None


def resolve_arrival_transit_hub(destination: str | None) -> tuple[str | None, dict[str, Any] | None]:
    """Resolves the best arrival airport code and associated nearby transit metadata.
    If the destination has no direct airport, routes flights to the verified nearby airport.
    """
    if not destination:
        return None, None

    nearby = get_nearby_transit(destination)
    if nearby and nearby.get("nearby_airport"):
        return nearby["nearby_airport"]["code"], nearby

    return None, None
