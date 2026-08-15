# Draft War Room — Full Season App Spec

A personal fantasy football assistant that starts as a draft-day tool and becomes a season-long co-manager: syncing live with your ESPN league, recommending lineups and waiver moves each week, and keeping you competitive with people who've played for 15 years.

---

## 1. Vision

**One app, three jobs:**
1. **Draft day:** live pick tracking and smart recommendations (already built as v1).
2. **Every week:** tell me who to start, who to add, and who to trade — before I have to ask.
3. **All season:** track how my team is trending and warn me before problems (byes, injuries, playoff schedule) cost me a win.

Target user: a first-year player who wants great decisions without hours of research.

---

## 2. Data sources & API strategy

### Primary: ESPN's unofficial Fantasy API
- Base endpoint: `https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{season}/segments/0/leagues/{league_id}`
- Key views: `mDraftDetail` (draft results), `mRoster` (all rosters), `mMatchup` (weekly scores), `mSettings` (league scoring rules), `kona_player_info` (player stats, projections, ownership %, injury status).
- **Auth for private leagues:** copy two cookies from a logged-in browser session — `espn_s2` and `SWID` — stored locally, never shared. The community `espn-api` Python package handles this cleanly.
- **Risk:** unofficial and undocumented; endpoints can change without notice. Mitigation: wrap all ESPN calls in one adapter module so a breakage is a one-file fix, and pin to the maintained `espn-api` package which the community patches quickly.

### Supplemental (free, no auth)
- **Sleeper public API** (`api.sleeper.app`): full NFL player database, injury statuses, and *trending adds/drops* across millions of leagues — a fantastic waiver-wire signal, usable even though the league lives on ESPN.
- **nflverse data** (GitHub): free weekly stats, snap counts, and target shares for deeper "is this player actually good or just lucky?" analysis.

### Architecture note
Browsers block direct calls to ESPN (CORS), so the app needs a thin backend:

```
[ESPN API] ──┐
[Sleeper]  ──┼──> [Backend: Python/FastAPI, runs on a $0–5/mo host or a
[nflverse] ──┘     Raspberry Pi / home PC on a schedule]
                        │  (fetch + score + store, SQLite)
                        ▼
                 [Web app: React PWA on your phone]
                        │
                        ▼
                 [Push alerts: email / Discord / SMS via Twilio]
```

A cron job refreshes data a few times daily (hourly on Sundays).

---

## 3. Feature set by season phase

### Phase 1 — Draft day (v1, built)
- Snake-draft tracker with pick logging and undo
- Recommendation engine: rankings + roster needs + round timing
- **v2 upgrades:** auto-import draft results afterward via `mDraftDetail` so the season features start with zero manual entry; live rankings refresh the morning of the draft.

### Phase 2 — Weekly management (the core of the season)
- **Start/Sit Advisor:** every Thursday, compares ESPN projections + matchup difficulty + injury status for your roster and posts a recommended lineup with plain-English reasons ("Bench Player X: opponent allows fewest WR points in the league").
- **Lineup guardrails:** push alert if you have an injured/bye-week/inactive player in your starting lineup 90 minutes before kickoff. This one feature wins games.
- **Waiver Wire Radar:** Tuesday morning digest ranking available free agents by: Sleeper trending adds, recent usage (snaps/targets from nflverse), rest-of-season schedule, and your roster needs. Suggests who to drop.
- **Matchup Preview:** projected score vs. this week's opponent, win probability, and the one swing decision most likely to flip it.

### Phase 3 — Season strategy
- **Trade Analyzer:** paste any proposed trade; app evaluates both sides using rest-of-season projections and *your* roster construction (a trade can be "fair" but wrong for your team).
- **Trade Finder:** scans league-mates' rosters for mutually beneficial swaps ("Team 6 is desperate at RB; offer your RB4 for their WR2").
- **Playoff Planner:** from week 8 on, weighs players' fantasy-playoff-week schedules (weeks 15–17) so you stockpile players with soft late matchups.
- **Season Dashboard:** record, points-for trend, luck index (actual wins vs. expected wins), and position-by-position strength vs. the league.

### Phase 4 — Delight features
- **Monday Recap:** auto-written weekly summary with MVP, bust, and a trash-talk line ready to paste into the group chat.
- **Rivalry cards:** head-to-head history vs. each opponent (fun with a family/friends league).
- **"Explain like I'm new" mode:** every recommendation includes the why in newbie terms — turning season one into a masterclass.
- **Claude integration:** a chat panel (via the Anthropic API) that can answer free-form questions against your live league data — "Should I be worried about my TE?" — grounded in the actual numbers the backend has fetched.

---

## 4. Recommendation engine (v2)

Score each decision on weighted factors:

| Factor | Weight | Source |
|---|---|---|
| Rest-of-season projection | 30% | ESPN `kona_player_info` |
| Recent usage trend (snaps, targets, touches) | 25% | nflverse |
| Matchup difficulty this week | 20% | ESPN + points-allowed-by-position |
| Injury/practice status | 15% | ESPN + Sleeper |
| Community signal (trending adds) | 10% | Sleeper |

All weights configurable; show the math so trust builds over time.

---

## 5. Build roadmap

| Milestone | Scope | Effort |
|---|---|---|
| M1 | Backend that connects to your league (cookies), pulls rosters/settings/draft | 1 evening |
| M2 | Tuesday waiver digest + Thursday lineup email | 1 weekend |
| M3 | Web dashboard (PWA) with lineup advisor + matchup preview | 1–2 weekends |
| M4 | Trade analyzer + playoff planner | 1 weekend |
| M5 | Alerts (pre-kickoff guardrails) + Monday recap | 1 weekend |

Total: a comfortably paced September–October side project that pays off through the playoffs.

## 6. Risks & principles
- **ESPN API is unofficial** — isolate it behind one adapter; keep a manual-entry fallback (the v1 War Room already is one).
- **Cookies are credentials** — store locally only, never commit to git, refresh when they expire (~every few weeks).
- **Be a light touch** — respect rate limits; a few polite requests per hour is plenty.
- **Recommendations advise, never auto-act** — the app never makes roster moves for you; every change is your tap in the ESPN app.
