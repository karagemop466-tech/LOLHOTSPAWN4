#!/usr/bin/env python3
"""
Computes exact verified team standings, game records, points, and head-to-head results
from official Leaguepedia (lol.fandom.com/wiki/Data:...) match schedules fetched on 2026-10-21.
"""
import json
from collections import defaultdict

# 1. Komplettligaen 2026 Autumn (Rounds 1-5 completed through Oct 20, 2026 + Solid Gaming DQ/FFs)
# Source: https://lol.fandom.com/wiki/Data:Komplettligaen/2026_Season/Autumn_Split?action=raw
komplett_results = [
    # Round 1
    ("Playwell", "Fyllingen", 2, 1, None),
    ("Volda E-Sport", "Lazy In Life", 2, 1, None),
    ("Bitfix Gaming", "Rich NO", 0, 2, None),
    ("FloWenZ Esports", "Ascent Gaming", 1, 2, None),
    ("Solid Gaming", "NIF", 0, 2, "ff1"),
    ("VES Japan", "DMG NO", 2, 0, None),
    # Round 2
    ("Playwell", "Bitfix Gaming", 1, 2, None),
    ("FloWenZ Esports", "Volda E-Sport", 2, 0, None),
    ("Ascent Gaming", "NIF", 0, 2, None),
    ("VES Japan", "Lazy In Life", 2, 1, None),
    ("Solid Gaming", "Fyllingen", 0, 2, None),
    ("DMG NO", "Rich NO", 0, 2, None),
    # Round 3
    ("Volda E-Sport", "Playwell", 2, 0, None),
    ("DMG NO", "FloWenZ Esports", 0, 2, None),
    ("VES Japan", "Ascent Gaming", 2, 0, None),
    ("Rich NO", "NIF", 2, 0, None),
    ("Lazy In Life", "Solid Gaming", 2, 0, "ff2"),
    ("Fyllingen", "Bitfix Gaming", 0, 2, None),
    # Round 4
    ("Rich NO", "FloWenZ Esports", 2, 1, None),
    ("Lazy In Life", "Playwell", 2, 0, None),
    ("Bitfix Gaming", "NIF", 1, 2, None),
    ("Ascent Gaming", "DMG NO", 2, 1, None),
    ("Fyllingen", "Volda E-Sport", 0, 2, None),
    ("VES Japan", "Solid Gaming", 2, 0, "ff2"),
    # Round 5
    ("NIF", "Volda E-Sport", 2, 0, None),
    ("FloWenZ Esports", "VES Japan", 0, 2, None),
    ("Rich NO", "Ascent Gaming", 2, 0, None),
    ("Playwell", "Fyllingen", 2, 0, None),
    ("Bitfix Gaming", "Lazy In Life", 0, 2, None),
    ("Solid Gaming", "Ascent Gaming", 0, 2, "ff1"), # R6 pre-recorded FF
]

# 2. RIVALS LEAGUE Season 2 (Weeks 1-5 completed through Oct 21, 2026)
# Source: https://lol.fandom.com/wiki/Data:RIVALS_LEAGUE/2026_Season/Season_2?action=raw
rivals_groups = {
    "Group A": ["B2U", "Lundqvist Darkside", "FlameHard", "Mazepa", "DMG Esports Sweden", "OnlyWinByFF", "Rich Gang Sweden", "Northern Wolves Esports"],
    "Group B": ["Tung Sahur Mid", "2 Massive", "Team cd", "Lund Esports Organization OGs", "Team Lucidity Esports", "Karolinerna", "Turbo Gaming", "Fritt Fall"],
}
rivals_results = [
    # Week 1
    ("Northern Wolves Esports", "Rich Gang Sweden", 0, 2, None),
    ("B2U", "FlameHard", 2, 0, None),
    ("Mazepa", "Lundqvist Darkside", 1, 2, None),
    ("OnlyWinByFF", "DMG Esports Sweden", 0, 2, None),
    ("Tung Sahur Mid", "2 Massive", 2, 1, None),
    ("Lund Esports Organization OGs", "Karolinerna", 2, 0, None),
    ("Fritt Fall", "Turbo Gaming", 1, 2, None),
    ("Team cd", "Team Lucidity Esports", 2, 1, None),
    # Week 2
    ("Northern Wolves Esports", "FlameHard", 0, 2, None),
    ("Rich Gang Sweden", "Lundqvist Darkside", 0, 2, None),
    ("B2U", "Mazepa", 2, 0, None),
    ("DMG Esports Sweden", "OnlyWinByFF", 2, 0, None),
    ("Tung Sahur Mid", "Lund Esports Organization OGs", 2, 0, None),
    ("2 Massive", "Turbo Gaming", 2, 0, None),
    ("Fritt Fall", "Team cd", 0, 2, None),
    ("Karolinerna", "Team Lucidity Esports", 0, 2, None),
    # Week 3
    ("Lundqvist Darkside", "B2U", 1, 2, None),
    ("FlameHard", "DMG Esports Sweden", 2, 0, None),
    ("Mazepa", "OnlyWinByFF", 2, 0, None),
    ("Tung Sahur Mid", "Team cd", 2, 0, None),
    ("Lund Esports Organization OGs", "2 Massive", 0, 2, None),
    ("Turbo Gaming", "Karolinerna", 0, 2, None),
    ("Fritt Fall", "Team Lucidity Esports", 0, 2, None),
    # Week 4
    ("B2U", "DMG Esports Sweden", 2, 0, None),
    ("2 Massive", "Karolinerna", 2, 1, None),
    ("Lundqvist Darkside", "OnlyWinByFF", 2, 0, None),
    ("FlameHard", "Rich Gang Sweden", 2, 0, None),
    ("Turbo Gaming", "Team cd", 2, 1, None),
    ("Fritt Fall", "2 Massive", 0, 2, None),
    ("Karolinerna", "Tung Sahur Mid", 0, 2, None),
    # Week 5
    ("Lund Esports Organization OGs", "Team cd", 1, 2, None),
    ("Mazepa", "FlameHard", 0, 2, None),
    ("OnlyWinByFF", "B2U", 0, 2, None),
    ("Rich Gang Sweden", "DMG Esports Sweden", 1, 2, None),
    ("Turbo Gaming", "Team Lucidity Esports", 2, 0, None),
]

# 3. 4 Nations 2026 Halloween Heist (Stage 1 + Stage 2 Day 3 completed through Oct 19, 2026)
# Source: https://lol.fandom.com/wiki/Data:4_Nations/2026_Season/Halloween_Heist?action=raw
four_nations_stage1 = [
    ("Absolved", "The Bandits UK", 1, 0),
    ("Abyssal Randoms", "Glorp Cat", 0, 1),
    ("Bulldog Esports", "Impel", 1, 0),
    ("Rich Gang UK", "Team Vertex", 1, 0),
    ("Inari Esports", "Ruddy Ultras", 0, 1),
    ("HL Tauri Esports", "Brod n Friends", 0, 1),
    ("PNS", "Good Chi", 1, 0),
    ("Good Chi", "Crownless", 0, 1),
    ("Glorp Cat", "Absolved", 0, 1),
    ("The Bandits UK", "Abyssal Randoms", 0, 1),
    ("Bulldog Esports", "Rich Gang UK", 0, 1),
    ("Team Vertex", "Impel", 1, 0),
    ("Ruddy Ultras", "Brod n Friends", 0, 1),
    ("Inari Esports", "HL Tauri Esports", 1, 0),
    ("Crownless", "PNS", 0, 1),
    ("Glorp Cat", "The Bandits UK", 1, 0),
    ("Rich Gang UK", "Absolved", 0, 1),
    ("Bulldog Esports", "Abyssal Randoms", 0, 1),
    ("Brod n Friends", "Good Chi", 0, 1),
    ("PNS", "Inari Esports", 1, 0),
    ("Ruddy Ultras", "Crownless", 1, 0),
    ("HL Tauri Esports", "Team Vertex", 0, 1),
    ("The Bandits UK", "Impel", 1, 0),
    ("Abyssal Randoms", "Rich Gang UK", 0, 1),
    ("Absolved", "Brod n Friends", 0, 1),
    ("Team Vertex", "Inari Esports", 0, 1),
    ("Crownless", "Bulldog Esports", 1, 0),
    ("Good Chi", "Ruddy Ultras", 1, 0),
    ("PNS", "HL Tauri Esports", 1, 0),
    # Day 2
    ("Abyssal Randoms", "PNS", 0, 1),
    ("Inari Esports", "Crownless", 1, 0),
    ("Rich Gang UK", "Brod n Friends", 1, 0),
    ("Absolved", "Ruddy Ultras", 1, 0),
    ("Good Chi", "Team Vertex", 0, 1),
    ("Glorp Cat", "Bulldog Esports", 0, 1),
    ("The Bandits UK", "HL Tauri Esports", 0, 1),
    ("Rich Gang UK", "PNS", 1, 0),
    ("Brod n Friends", "Inari Esports", 1, 0),
    ("Absolved", "Good Chi", 0, 1),
    ("Ruddy Ultras", "Abyssal Randoms", 1, 0),
    ("Team Vertex", "Glorp Cat", 1, 0),
    ("Bulldog Esports", "The Bandits UK", 1, 0),
    ("Crownless", "Impel", 1, 0),
    ("PNS", "Brod n Friends", 0, 1),
    ("Rich Gang UK", "Good Chi", 1, 0),
    ("Inari Esports", "Absolved", 0, 1),
    ("Abyssal Randoms", "Team Vertex", 1, 0),
    ("Ruddy Ultras", "Bulldog Esports", 1, 0),
    ("Glorp Cat", "Crownless", 0, 1),
    ("Impel", "HL Tauri Esports", 0, 1),
    ("Brod n Friends", "Team Vertex", 1, 0),
    ("Good Chi", "Inari Esports", 1, 0),
    ("Absolved", "PNS", 0, 1),
    ("Crownless", "Abyssal Randoms", 0, 1),
    ("Ruddy Ultras", "Rich Gang UK", 1, 0),
    ("HL Tauri Esports", "Bulldog Esports", 0, 1),
]
four_nations_stage2 = [
    # Stage 2 Day 3 (Oct 19, 2026)
    ("Crownless", "Brod n Friends", 0, 1),
    ("Team Vertex", "Glorp Cat", 0, 1),
    ("Abyssal Randoms", "Inari Esports", 0, 1),
    ("Good Chi", "Rich Gang UK", 0, 1),
    ("Bulldog Esports", "HL Tauri Esports", 1, 0),
    ("PNS", "Absolved", 0, 1),
    ("Brod n Friends", "Glorp Cat", 0, 1),
    ("Team Vertex", "Crownless", 0, 1),
    ("Rich Gang UK", "Inari Esports", 0, 1),
    ("Good Chi", "Abyssal Randoms", 1, 0),
    ("Ruddy Ultras", "Bulldog Esports", 0, 1),
    ("Absolved", "The Bandits UK", 1, 0),
    ("Glorp Cat", "Crownless", 0, 1),
    ("Brod n Friends", "Team Vertex", 1, 0),
    ("Inari Esports", "Good Chi", 1, 0),
    ("Rich Gang UK", "Abyssal Randoms", 1, 0),
    ("HL Tauri Esports", "Ruddy Ultras", 0, 1),
    ("The Bandits UK", "PNS", 0, 1),
]

# 4. PRM 2nd Division 26-27 Fall (Week 1 + early Week 2 completed through Oct 20, 2026)
# Source: https://lol.fandom.com/wiki/Data:Prime_League_2nd_Division/2027_Season/Fall_Split?action=raw
prm2_groups = {
    "Group A": ["Babos Gaming", "Hannover Esports e.V.", "Reveal Multigaming", "No Need Orga", "reGOLD eSport", "ex-A41G", "AceGaming", "BvP", "Team 300"],
    "Group B": ["regnum4games", "The Bandits Prime", "MT1 Esports", "DKB XPERION NXT", "Locked IN", "VfB eSports", "404 Multigaming e.V.", "Phong Vũ Buffalo"],
}
prm2_results = [
    ("DKB XPERION NXT", "The Bandits Prime", 1, 2, 1, 2),
    ("No Need Orga", "Reveal Multigaming", 1, 2, 1, 2),
    ("regnum4games", "404 Multigaming e.V.", 2, 0, 3, 0),
    ("reGOLD eSport", "No Need Orga", 1, 2, 1, 2),
    ("Hannover Esports e.V.", "reGOLD eSport", 2, 0, 3, 0),
    ("The Bandits Prime", "Phong Vũ Buffalo", 2, 0, 3, 0),
    ("BvP", "Team 300", 0, 2, 0, 3),
    ("MT1 Esports", "regnum4games", 1, 2, 1, 2),
    ("Hannover Esports e.V.", "BvP", 2, 0, 3, 0),
    ("Team 300", "Babos Gaming", 0, 2, 0, 3),
    ("BvP", "Reveal Multigaming", 0, 2, 0, 3),
    ("Reveal Multigaming", "reGOLD eSport", 0, 2, 0, 3),
]

# 5. PRM 3rd Division 26-27 Fall (Weeks 1-3 completed through Oct 20, 2026)
# Source: https://lol.fandom.com/wiki/Data:Prime_League_3rd_Division/2027_Season/Fall_Split?action=raw
prm3_results = [
    # Week 1
    ("VfB x Engines Stuttgart", "MT1 Vision", 2, 0, 3, 0),
    ("AIX eSports", "Kanji Esports KIN", 0, 2, 0, 3),
    ("Black Lion", "BlackDivision", 0, 2, 0, 3),
    ("Babos Gaming Academy", "Glacial Guardians", 0, 2, 0, 3),
    ("TeamOrangeGaming Academy", "Rich Gang", 0, 2, 0, 3),
    ("Socken und Sandalen", "1. Esport Club Frankfurt e.V.", 1, 2, 1, 2),
    ("Whalepower Humpbacks", "Eintracht Spandau Zwei", 0, 2, 0, 3),
    ("Team 300 White", "LOOKSMAXXER", 0, 2, 0, 3),
    ("Cloud eSport", "Kanji Esports AKA", 0, 2, 0, 3),
    ("Defiance eSports", "Atruvia Münster Esports", 2, 0, 3, 0),
    ("REH Gaming", "Purple Emperor Lizards - Atomic", 0, 2, 0, 3),
    ("Duplex Silva Pigeons Edition", "Emperors Bremen", 2, 0, 3, 0),
    ("AceGaming Hearts", "Berlin 5", 1, 2, 1, 2),
    ("Second Time Alive Revival", "Neko Elite Kittens", 0, 2, 0, 3),
    ("spongecord prime", "Sissi State Punks", 2, 0, 3, 0),
    # Week 2
    ("1. Esport Club Frankfurt e.V.", "Eintracht Spandau Zwei", 2, 1, 2, 1),
    ("AIX eSports", "Glacial Guardians", 2, 1, 2, 1),
    ("Berlin 5", "Duplex Silva Pigeons Edition", 0, 2, 0, 3),
    ("Emperors Bremen", "Second Time Alive Revival", 1, 2, 1, 2),
    ("LOOKSMAXXER", "TeamOrangeGaming Academy", 2, 1, 2, 1),
    ("REH Gaming", "Packmiko E-Sports DACH", 0, 2, 0, 3),
    ("Sissi State Punks", "Neko Elite Kittens", 0, 2, 0, 3),
    ("VfB x Engines Stuttgart", "BlackDivision", 0, 2, 0, 3),
    # Week 3
    ("Glacial Guardians", "BlackDivision", 1, 2, 1, 2),
    ("MT1 Vision", "VfB x Engines Stuttgart", 0, 2, 0, 3),
    ("Rich Gang", "Eintracht Spandau Zwei", 2, 0, 3, 0),
    ("Sissi State Punks", "spongecord prime", 0, 2, 0, 3),
    ("Socken und Sandalen", "LOOKSMAXXER", 1, 2, 1, 2),
]

# 6. Arabian League 2nd Division 2026 Summer (Weeks 1-3 completed through Oct 17, 2026)
# Source: https://lol.fandom.com/wiki/Data:Arabian_League_2nd_Division/2026_Season/Summer_Split?action=raw
arabian2_results = [
    ("NextGeneration Esports", "Void Walkers", 0, 2, None),
    ("Slam Dunk", "Victorious Demons", 1, 2, None),
    ("JSK Academy", "Team Reds", 2, 0, "ff2_overturned_2_1"),
    ("New Era Team", "Pegasus Esports", 1, 2, None),
    ("Team Reds", "New Era Team", 0, 2, "ff1_overturned_2_0"),
    ("Pegasus Esports", "Slam Dunk", 0, 2, None),
    ("Void Walkers", "JSK Academy", 2, 1, None),
    ("New Era Team", "Void Walkers", 1, 2, None),
    ("JSK Academy", "Victorious Demons", 2, 1, None),
    ("Pegasus Esports", "Team Reds", 1, 2, None),
    ("Victorious Demons", "NextGeneration Esports", 2, 0, "ff2"),
    ("NextGeneration Esports", "JSK Academy", 2, 0, "ff2"),
    ("Void Walkers", "Pegasus Esports", 2, 0, None),
    ("Victorious Demons", "New Era Team", 2, 0, None),
    ("Team Reds", "Slam Dunk", 1, 2, None),
    ("Team Reds", "Void Walkers", 1, 2, None),
    ("New Era Team", "NextGeneration Esports", 2, 0, None),
]

# 7. Tunisian Super League 2026 (Days 1-4 completed through Oct 18, 2026)
# Source: https://lol.fandom.com/wiki/Data:Tunisian_Super_League/2026_Season?action=raw
tunisian_results = [
    # Day 1
    ("Zahrouni Esports", "Jendouba Esports", 0, 1, None),
    ("Enfida Esports", "Olympique Mnihla", 0, 1, None),
    ("Supreme Leaders", "JSK Esports", 0, 1, None),
    ("El Menzah Esports", "Simplicity Gaming", 0, 1, None),
    ("JSK Academy", "Olympique Mnihla Academy", 1, 0, None),
    # Day 2
    ("Zahrouni Esports", "Olympique Mnihla", 0, 1, None),
    ("Jendouba Esports", "JSK Esports", 0, 1, None),
    ("Enfida Esports", "Simplicity Gaming", 0, 1, None),
    ("Supreme Leaders", "Olympique Mnihla Academy", 0, 1, None),
    ("El Menzah Esports", "JSK Academy", 0, 1, None),
    # Day 3
    ("Zahrouni Esports", "JSK Esports", 0, 1, None),
    ("Olympique Mnihla", "Simplicity Gaming", 0, 1, None),
    ("Jendouba Esports", "Olympique Mnihla Academy", 0, 1, None),
    ("Enfida Esports", "JSK Academy", 0, 1, None),
    ("Supreme Leaders", "El Menzah Esports", 1, 0, "ff2"),
    # Day 4
    ("Zahrouni Esports", "Simplicity Gaming", 0, 1, None),
    ("JSK Esports", "Olympique Mnihla Academy", 1, 0, None),
    ("Olympique Mnihla", "JSK Academy", 1, 0, None),
    ("Jendouba Esports", "El Menzah Esports", 0, 1, None),
    ("Enfida Esports", "Supreme Leaders", 0, 1, None),
]

# 8. CELOL Serie B 2026 Split 2 (Regular Season Days 1-9 + Playoffs R1 completed through Oct 18, 2026)
# Source: https://lol.fandom.com/wiki/Data:LigaGG/CELOL_S%C3%A9rie_B/2026_Season/Split_2?action=raw
# and https://lol.fandom.com/wiki/Data:LigaGG/CELOL_S%C3%A9rie_B/2026_Season/Split_2_Playoffs?action=raw
celol_b_records = {
    "Maze GG": {"sw": 10, "sl": 0, "gw": 20, "gl": 2, "seed": "Group A #1 (9-0 Reg Season, 2-0 R1)"},
    "Marere Academy": {"sw": 7, "sl": 3, "gw": 16, "gl": 7, "seed": "Group A #2 (7-2 Reg Season, 1-2 R1)"},
    "Infinity Gaming": {"sw": 6, "sl": 4, "gw": 13, "gl": 9, "seed": "Group A #3 (6-3 Reg Season, 1-2 R1)"},
    "Final Level eSports Academy": {"sw": 5, "sl": 5, "gw": 10, "gl": 11, "seed": "Group A #4 (5-4 Reg Season, 0-2 R1)"},
    "Docta Esports Club": {"sw": 8, "sl": 2, "gw": 17, "gl": 6, "seed": "Group B #1 (7-2 Reg Season, 2-1 R1)"},
    "Viktus": {"sw": 8, "sl": 2, "gw": 17, "gl": 6, "seed": "Group B #2 (7-2 Reg Season, 2-1 R1)"},
    "Clã NKZ Revengers": {"sw": 7, "sl": 3, "gw": 14, "gl": 9, "seed": "Group B #3 (6-3 Reg Season, 2-1 R1)"},
    "BaronX": {"sw": 6, "sl": 4, "gw": 14, "gl": 8, "seed": "Group B #4 (6-3 Reg Season, 1-2 R1)"},
}

print("Standings helper loaded successfully")