"""The app dev workspace's world data (a6431): devices, the preview's icons, the sample app's places.

Device sizes are CSS pixels, the viewport a page gets: vw and vh (w and h are the desk's own size of an appearance). iPhone 15: 393 x 852, safe insets 59 top and 34 bottom upright,
59 left and right and 21 bottom turned, the Dynamic Island (recalled from Apple's published sizes, not measured here).
A small Android: 360 x 800, a 24 px status bar, a punch-hole camera, a 16 px gesture bar (a typical phone; recalled).
iPad (10th generation): 820 x 1180, a 24 px status bar and a 20 px home bar, no cutout (recalled).
"""
G = "<svg viewBox='0 0 24 24'><g fill='none' stroke='currentColor' stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round'>{}</g></svg>"

DEVICES = [
    ("iPhone 15", dict(order=1, vw=393, vh=852, safe="safe 59 0 34 0 cutout island", wide="safe 0 59 21 59 cutout island"),
     G.format("<rect x='7' y='2.5' width='10' height='19' rx='2.6'/><path d='M10.6 4.6h2.8'/>")),
    ("Small Android", dict(order=2, vw=360, vh=800, safe="safe 24 0 16 0 cutout hole", wide="safe 24 0 16 32 cutout hole"),
     G.format("<rect x='7.5' y='3.5' width='9' height='17' rx='1.4'/><circle cx='12' cy='5.6' r='0.5'/>")),
    ("iPad", dict(order=3, vw=820, vh=1180, safe="safe 24 0 20 0", wide="safe 24 0 20 0"),
     G.format("<rect x='4' y='3' width='16' height='18' rx='2.2'/><path d='M11 18.4h2'/>")),
]

ICONS = [
    ("Turn", "turn", G.format("<rect x='8.5' y='3' width='7' height='11' rx='1.4'/><path d='M4 13.5a8 8 0 0 0 7.5 7'/><path d='M4 17.2v-3.7h3.7'/>")),
    ("Safe area", "safe", G.format("<rect x='6' y='2.5' width='12' height='19' rx='2.6'/><path d='M10 4.8h4'/><path d='M6 7.4h12M6 17.6h12' stroke-dasharray='1.4 1.6'/>")),
    ("Point", "inspect", G.format("<path d='M5.5 3.5l5.8 15.2 2.1-6.2 6.2-2.1z'/><path d='M14 14l5 5'/>")),
]

PLACES = [
    ("Pier Café", "North pier", "7–16", "4.6 ★", "Coffee and cinnamon buns at the end of the north pier. Sit outside when the wind is down; the gulls know the buns."),
    ("The Net Loft", "Old harbour", "11–22", "4.4 ★", "Fish soup in a loft where the nets were mended. The window tables look over the moorings."),
    ("Lighthouse Steps", "Breakwater", "Always", "4.8 ★", "Ninety-two steps up the old light. On a clear evening you can see the islands."),
    ("Harbour Baths", "South quay", "6–20", "4.5 ★", "A sea pool with a heated corner and a sauna on the jetty. Bring a coin for the lockers."),
    ("Rope & Anchor", "Old harbour", "16–01", "4.2 ★", "A small pub with a long bar and a longer memory. Quiz on Thursdays."),
    ("Fish Market", "East quay", "5–11", "4.7 ★", "The morning catch on ice, sold off the boats. Come early for the crab."),
    ("Boatyard Gallery", "Slipway", "12–18", "4.3 ★", "Paintings and prints in the shed where the ferries are scraped each spring."),
    ("Seawall Walk", "Promenade", "Always", "4.6 ★", "Two kilometres along the wall from the baths to the light. Flat, windy, good."),
    ("Ferry Terminal", "West quay", "5–23", "3.9 ★", "Boats to the islands every hour in summer, every two in winter."),
    ("Kelp Kitchen", "North pier", "17–23", "4.5 ★", "Seaweed, shellfish and bread baked in the old smokehouse. Book ahead."),
    ("Chandlery", "Slipway", "8–17", "4.1 ★", "Rope, paint, charts and good advice. The owner has sailed round twice."),
    ("Tide Garden", "Breakwater", "Always", "4.4 ★", "Rock pools and sea pinks behind the breakwater. Best at low tide."),
]
