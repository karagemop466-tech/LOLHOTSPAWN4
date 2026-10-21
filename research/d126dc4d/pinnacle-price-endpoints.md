# Pinnacle public price discovery — correction and source handoff

**Direct publisher retrieval: 2026-10-21 UTC.** This supersedes the first implementation's assertion that there is no public Pinnacle price endpoint. A 404 from a guessed URL only proves that guessed URL failed.

## Working public GET routes, directly checked

| Scope | Official metadata | Official prices | Observed content |
| --- | --- | --- | --- |
| LoL Worlds | <https://guest.api.arcadia.pinnacle.com/0.1/leagues/9587/matchups> | <https://guest.api.arcadia.pinnacle.com/0.1/leagues/9587/markets/straight> | Eight parent matchups and their two-way full-series moneylines, plus separate map markets and outright specials. The latter must be excluded. |
| LoL EMEA Masters | <https://guest.api.arcadia.pinnacle.com/0.1/matchups/1638709103> | <https://guest.api.arcadia.pinnacle.com/0.1/leagues/225201/markets/straight> | Solary home / Galions away, Bo5, pending, not live; full-series line home +105 / away -127 in this retrieval. |
| All esports | <https://guest.api.arcadia.pinnacle.com/0.1/sports/12/matchups> | <https://guest.api.arcadia.pinnacle.com/0.1/sports/12/markets/straight> | Mixed esports, specials and map/handicap/total markets. Much larger; not a LoL-only feed. |

These are ordinary public guest GET responses; no authentication, geographic restriction or paywall was bypassed. Some single-match metadata URLs returned 500 or an authorization notice; the public league response independently contains the metadata. Do not claim a restricted URL succeeded.

## Strict acceptance rules

A price is a candidate series-winner line only when all of these hold:

- `type == "moneyline"`, `period == 0`, `key == "s;0;m"`, `status == "open"`.
- Exactly two prices with distinct `designation` values `home` and `away` (not multi-participant outright specials with `participantId`).
- Join `matchupId` to a parent `type == "matchup"`, not `special`; verify `isLive == false`, pending state, the correct League of Legends league, and explicit participants/start time.
- Treat the native integer prices as American moneylines, convert each to implied probability, and normalize the pair to remove overround. Do not mix a map period with the series period or combine prices from different books/events into one pair.
- Audit participant aliases rather than substring-matching main/academy, national divisions or similarly named teams. Research snapshot rows below keep **Pinnacle's own names**; their alias mapping to Hotspawn is not claimed as verified here.
- Compare the independent event start with Hotspawn, and publish a timing conflict rather than silently overwriting either time. A quote retrieval timestamp is not a provider update timestamp.
- Re-fetch on every refresh; this research snapshot must not be frozen as live input.

## Verified row-by-row research snapshot

Each row's pairing, pending/not-live state, format and start are in the official metadata, and its prices are in the linked official price response with the same matchup ID. Fair probabilities below are **our mathematical de-vig calculation**, not a provider-confirmed true chance. Exact provider quote timestamps were not exposed and remain blank in the accompanying JSON.

| Matchup ID | Publisher home / away | Publisher start UTC | Native American home / away | Derived fair home / away | Official metadata / prices |
| --- | --- | --- | --- | --- | --- |
| 1638709103 | Solary / Galions | 2026-10-22 16:00 | +105 / -127 | 46.578% / 53.422% | [Metadata](https://guest.api.arcadia.pinnacle.com/0.1/matchups/1638709103) · [Prices](https://guest.api.arcadia.pinnacle.com/0.1/leagues/225201/markets/straight) |
| 1638748200 | Gen.G / Invictus | 2026-10-23 17:00 | -435 / +323 | 77.474% / 22.526% | [Metadata](https://guest.api.arcadia.pinnacle.com/0.1/leagues/9587/matchups) · [Prices](https://guest.api.arcadia.pinnacle.com/0.1/leagues/9587/markets/straight) |
| 1638750814 | Liquid / CTBC Flying Oyster | 2026-10-23 18:00 | -285 / +228 | 70.829% / 29.171% | [Metadata](https://guest.api.arcadia.pinnacle.com/0.1/leagues/9587/matchups) · [Prices](https://guest.api.arcadia.pinnacle.com/0.1/leagues/9587/markets/straight) |
| 1638750902 | Anyone's Legend / Karmine Corp | 2026-10-23 19:00 | -200 / +167 | 64.029% / 35.971% | [Metadata](https://guest.api.arcadia.pinnacle.com/0.1/matchups/1638750902) · [Prices](https://guest.api.arcadia.pinnacle.com/0.1/leagues/9587/markets/straight) |
| 1638750815 | G2 / Dplus KIA | 2026-10-23 20:00 | +126 / -148 | 42.577% / 57.423% | [Metadata](https://guest.api.arcadia.pinnacle.com/0.1/leagues/9587/matchups) · [Prices](https://guest.api.arcadia.pinnacle.com/0.1/leagues/9587/markets/straight) |
| 1638748203 | Hanwha Life / Top Esports | 2026-10-23 21:00 | -490 / +355 | 79.074% / 20.926% | [Metadata](https://guest.api.arcadia.pinnacle.com/0.1/matchups/1638748203) · [Prices](https://guest.api.arcadia.pinnacle.com/0.1/leagues/9587/markets/straight) |
| 1638748205 | LOS / T1 | 2026-10-23 22:00 | +516 / -800 | 15.443% / 84.557% | [Metadata](https://guest.api.arcadia.pinnacle.com/0.1/matchups/1638748205) · [Prices](https://guest.api.arcadia.pinnacle.com/0.1/leagues/9587/markets/straight) |
| 1638754606 | Secret Whales / LYON | 2026-10-23 23:00 | +123 / -145 | 43.107% / 56.893% | [Metadata](https://guest.api.arcadia.pinnacle.com/0.1/leagues/9587/matchups) · [Prices](https://guest.api.arcadia.pinnacle.com/0.1/leagues/9587/markets/straight) |
| 1638755459 | Bilibili / Movistar KOI | 2026-10-24 00:00 | -512 / +368 | 79.655% / 20.345% | [Metadata](https://guest.api.arcadia.pinnacle.com/0.1/matchups/1638755459) · [Prices](https://guest.api.arcadia.pinnacle.com/0.1/leagues/9587/markets/straight) |

Reproducible formula: for positive American price `a`, `q=100/(a+100)`; for negative `a`, `q=(-a)/((-a)+100)`. Then `p_home=q_home/(q_home+q_away)` and `p_away=1-p_home`. The JSON retains observed prices and the computed overround separately.

## Review flags

- **Source disagreement:** the directly fetched Thunderpick Solary/Galions full-series page has Solary -122 / Galions -114, narrowly favouring Solary, while this Pinnacle line narrowly favours Galions. Do not claim a unanimous favourite. [Thunderpick exact market](https://thunderpick.io/esports/league-of-legends/emea-masters-2026-summer/10747/solary-vs-galions/2829674).
- **Time verification:** Pinnacle gives Solary/Galions 16:00Z. The Hotspawn lobby displays October 22, 08:00 without a zone in extracted text. Do not infer the extracted lobby zone or conflate displayed local time with a verified UTC field. [Hotspawn official card](https://www.hotspawn.com/matches/galions-vs-solary-em-2026-summer-main-event-1081205).
- **Unverified alias mapping:** Invictus, Liquid, G2, Hanwha Life, LOS, Secret Whales and Bilibili are the bookmaker's actual names, not silently normalized replacements. Fixture-specific identity/competition checks are still needed before attachment to Hotspawn.
- **No low-tier-market overclaim:** these nine observed lines do not prove that all other LoL games lack markets. Independent organizer results in the companion audit remain useful for unpriced regional fixtures.
- **No fake source freshness:** the recorded observation date is 2026-10-21, not a claim of an exact provider update time. API `version` values are opaque revision IDs, not timestamps.

Machine-readable research record: `pinnacle-verified-price-snapshot.json`. Implementation handoff: [issue #11](https://github.com/karagemop466-tech/LOLHOTSPAWN4/issues/11).
