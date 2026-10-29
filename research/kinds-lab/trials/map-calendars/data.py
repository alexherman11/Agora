"""Realistic data for the map-calendars trial: spots around Seabright, Seabright board events, an imported public
calendar feed with iCal words, and Alex's own meetings with his own words. Deterministic (seeded).

Coordinates are approximate (imagined from memory of Santa Cruz, not surveyed); they only need to be plausible."""
import random

SPOTS = [
    ("Seabright Beach", 36.9628, -122.0115), ("Castle Beach", 36.9619, -122.0123),
    ("Santa Cruz Harbor", 36.9636, -122.0025), ("Crow's Nest", 36.9618, -122.0017),
    ("Museum of Natural History", 36.9636, -122.0097), ("Twin Lakes Beach", 36.9625, -121.9985),
    ("Arana Gulch", 36.9725, -122.0035), ("Murray St Bridge", 36.9654, -122.0030),
    ("Mission Plaza", 36.9774, -122.0297), ("Abbott Square", 36.9744, -122.0262),
    ("Boardwalk", 36.9643, -122.0175), ("Lighthouse Field", 36.9535, -122.0237),
    ("Natural Bridges", 36.9513, -122.0573), ("Pleasure Point", 36.9561, -121.9708),
    ("Harvey West Park", 36.9877, -122.0393), ("San Lorenzo Park", 36.9739, -122.0207),
    ("Kaiser Arena", 36.9631, -122.0153), ("Downtown Library", 36.9755, -122.0264),
    ("City Hall", 36.9758, -122.0258), ("Santa Cruz Wharf", 36.9590, -122.0215),
    ("Cowell Beach", 36.9617, -122.0221), ("Jessie St Marsh", 36.9733, -122.0167),
    ("Frederick St Park", 36.9715, -122.0069), ("Seabright Station", 36.9664, -122.0082),
    ("Branciforte Library", 36.9790, -122.0106), ("Ocean St Bridge", 36.9712, -122.0215),
    ("East Cliff Overlook", 36.9606, -122.0072), ("Yacht Harbor Boat Ramp", 36.9660, -122.0011),
    ("Live Oak Grange", 36.9770, -121.9840), ("Garfield Park Library", 36.9645, -122.0430),
    # two spots share a name (a real neighbourhood has two community gardens), and one is just "Library"
    ("Community garden", 36.9718, -122.0072), ("Community garden", 36.9682, -122.0198),
    ("Library", 36.9755, -122.0263),
]
GENERIC = ["Bench on East Cliff", "Stairs to the beach", "Little free library", "Bus stop on Soquel",
           "Mural on Seabright Ave", "Picnic tables", "Bike rack by the cafe", "Tide pool steps",
           "Dog run", "Lookout point", "Kayak launch", "Basketball court", "Corner shop", "Food truck lot",
           "Skate spot", "Bocce court", "Rose garden"]

BOARD_TITLES = ["Beach cleanup", "Tide pool walk", "Seabright neighbours meeting", "Garden workday", "Potluck",
                "Harbor kayak meetup", "Book swap", "Kids' story time", "Bike repair clinic", "Night sky watch",
                "Surf lesson for beginners", "Dog beach meetup", "Council prep", "Mural painting", "Bird count",
                "Stair repair crew", "Coffee and planning", "Seed swap", "Sunset yoga", "Walking group"]
BOARD_TEXTS = ["Bring gloves and a bucket if you have one.", "Meet by the steps, we will go when the tide is low.",
               "All welcome, no need to RSVP but it helps with snacks.", "We need hands for the beds by the fence.",
               "Bring a dish to share. Plates provided.", "Wetsuits recommended, the water is cold.",
               "Kids welcome with a grown-up.", "Rain cancels; check the board that morning."]
BOARD_LOCS = ["Seabright Beach by the lifeguard tower", "Seabright Beach", "Corner of Seabright & Murray",
              "Seabright & Murray", "the harbor parking lot", "Frederick St Park", "Zoom", "my place (DM for address)",
              "TBD", "Museum of Natural History, 1305 E Cliff Dr", "Crow's Nest upstairs room"]

FEED_SOURCES = ["Santa Cruz Public Libraries", "City of Santa Cruz Parks", "UCSC Arboretum", "Museum of Natural History"]
FEED_SUMMARIES = ["Storytime for toddlers", "Teen coding club", "Docent-led tide walk", "Native plant sale",
                  "Author talk", "Free tax help", "Citizenship class", "Monarch count", "Board game afternoon",
                  "Parks commission meeting", "Volunteer trail day", "Fossil family day", "Knitting circle",
                  "ESL conversation", "Film night"]
FEED_LOCS = ["Downtown Library, 224 Church St, Santa Cruz, CA 95060",
             "Museum of Natural History, 1305 E Cliff Dr, Santa Cruz, CA 95062",
             "Garfield Park Branch Library, 705 Woodrow Ave, Santa Cruz, CA 95060",
             "Harvey West Park, Santa Cruz", "UCSC Arboretum, 1156 High St, Santa Cruz, CA 95064",
             "Santa Cruz Wharf", "Online", "Branciforte Branch Library, 230 Gault St, Santa Cruz, CA 95062"]
FEED_GEO = {"Downtown Library": "36.9755;-122.0264", "Museum of Natural History": "36.9636;-122.0097",
            "Harvey West Park": "36.9877;-122.0393", "Santa Cruz Wharf": "36.9590;-122.0215"}

MEETING_WHO = ["Sam", "Priya", "Jordan", "Mo", "Kai", "the landlord", "Dr. Ortiz", "Bea", "the bike shop", "Lena"]
MEETING_WHAT = ["1:1 with {w}", "Coffee with {w}", "Call {w}", "Lunch with {w}", "Catch up with {w}",
                "Dentist", "Review lease with {w}", "Planning with {w}"]


def board_events(rng, n, spot_ids, spot_names):
    out = []
    for i in range(n):
        day, hour, minute = rng.randint(1, 30), rng.choice([9, 10, 11, 13, 16, 17, 18, 19]), rng.choice([0, 0, 30])
        kv = {"post_kind": "event", "text": rng.choice(BOARD_TEXTS), "seats": str(rng.choice([8, 10, 12, 20, 30, 50]))}
        if rng.random() < 0.65:
            kv["title"] = rng.choice(BOARD_TITLES)
        r = rng.random()
        if r < 0.85:
            kv["start"] = f"2026-11-{day:02d}T{hour:02d}:{minute:02d}Z"
        elif r < 0.95:
            kv["start"] = f"2026-11-{day:02d}"                       # all-day: a date (the board allows it)
        else:
            kv["start"] = f"2026-11-{day:02d}T{hour:02d}:{minute:02d}-08:00"
        if rng.random() < 0.4:
            kv["end"] = f"2026-11-{day:02d}T{min(hour + 2, 23):02d}:{minute:02d}Z"
        r = rng.random()
        if r < 0.45:
            kv["location"] = rng.choice(BOARD_LOCS)
        elif r < 0.65:
            kv["place"] = rng.choice(spot_ids)                       # "Link to a place": a spot's id
        elif r < 0.75:
            kv["place"] = rng.choice(spot_names)                     # field_types says place is text: a name
        if rng.random() < 0.05:
            kv["closes"] = f"2026-11-{max(day - 1, 1):02d}T12:00Z"
        out.append(kv)
    return out


def feed_items(rng, n):
    out = []
    for i in range(n):
        day, hour = rng.randint(1, 30), rng.choice([10, 11, 14, 15, 16, 18, 19])
        src = rng.choice(FEED_SOURCES)
        kv = {"uid": f"evt-{rng.randrange(16**8):08x}@{src.split()[0].lower()}.example",
              "summary": rng.choice(FEED_SUMMARIES), "source": src,
              "url": f"https://events.example/{src.split()[0].lower()}/{i}",
              "description": "Free. Drop in.", "categories": rng.choice(["Kids", "Adults", "Nature", "Civic"])}
        r = rng.random()
        if r < 0.70:
            from datetime import datetime, timedelta
            local = datetime(2026, 11, day, hour)
            kv["dtstart"] = (local + timedelta(hours=8)).strftime("%Y%m%dT%H%M%SZ")   # UTC, iCal basic format
            if rng.random() < 0.8:
                kv["dtend"] = (local + timedelta(hours=9, minutes=30)).strftime("%Y%m%dT%H%M%SZ")
        elif r < 0.90:
            kv["dtstart"] = f"202611{day:02d}"                       # VALUE=DATE
            kv["dtend"] = f"202611{min(day + 1, 30):02d}"
        else:
            kv["dtstart"] = f"202611{day:02d}T{hour:02d}0000"        # floating, with TZID
            kv["tzid"] = "America/Los_Angeles"
        r = rng.random()
        if r < 0.75:
            loc = rng.choice(FEED_LOCS)
            kv["location"] = loc
            for key, geo in FEED_GEO.items():
                if loc.startswith(key) and rng.random() < 0.6:
                    kv["geo"] = geo                                  # iCal GEO: lat;lon
        kv["status"] = rng.choices(["CONFIRMED", "TENTATIVE", "CANCELLED"], [85, 10, 5])[0]
        out.append(kv)
    return out


def meetings(rng, n, spot_ids, spot_names):
    out = []
    for i in range(n):
        who = rng.choice(MEETING_WHO)
        day, hour = rng.randint(1, 30), rng.choice([8, 9, 10, 12, 15, 16])
        kv = {"name": rng.choice(MEETING_WHAT).format(w=who), "with": who,
              "status": rng.choice(["confirmed", "confirmed", "tentative", "done", "cancelled"]),
              "duration": rng.choice(["30m", "45m", "1h"])}
        r = rng.random()
        if r < 0.70:
            kv["when"] = f"2026-11-{day:02d} {hour:02d}:00"          # local, no zone: how Alex types it
        elif r < 0.90:
            kv["when"] = f"2026-11-{day:02d}T{hour:02d}:00-08:00"
        else:
            kv["when"] = rng.choice(["Thu 3pm", "next Monday 10am", "tomorrow after lunch"])
        r = rng.random()
        if r < 0.50:
            kv["where"] = rng.choice(spot_ids)
        elif r < 0.75:
            kv["where"] = "Zoom"
        elif r < 0.85:
            kv["where"] = f"{who}'s place"
        elif r < 0.92:
            kv["where"] = rng.choice(spot_names)
        out.append(kv)
    return out
