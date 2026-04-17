# Restaurant Tech Speaking Practice

Personal practice tool for sharpening speaking skills on restaurant technology topics. Record yourself, get structured feedback, track progress over time.

## How It Works

1. **Pick a topic:** `/blog-topic` gives you a restaurant tech topic with prep notes and a framework
2. **Record yourself:** Speak for 1, 3, or 5 minutes on the topic (audio or video)
3. **Get reviewed:** `/blog-review ~/path/to/recording.m4a` analyzes your recording with detailed scores
4. **Track progress:** `/blog-progress` shows trends and recommendations

## Commands

| Command | What it does |
|---------|-------------|
| `/blog-topic` | Pick a random topic, or filter by category/difficulty/duration |
| `/blog-review [file]` | Analyze a recording against the 5-dimension rubric |
| `/blog-progress` | View score trends, averages, and improvement recommendations |

## Topic Categories

| Code | Category | File |
|------|----------|------|
| POS | POS Fundamentals | `topics/pos-fundamentals.md` |
| OPS | Restaurant Operations | `topics/restaurant-operations.md` |
| DD | DoorDash Platform | `topics/doordash-platform.md` |
| IND | Industry Trends | `topics/industry-trends.md` |
| PF | Pathfinder Deep Dives | `topics/pathfinder-deep-dives.md` |
| SAL | Sales & Partnerships | `topics/sales-and-partnerships.md` |

## Scoring Rubric

5 dimensions, 1-5 each (25 total). See `rubric.md` for full details.

1. Content & Structure
2. Delivery & Pace
3. Clarity & Filler Words
4. Persuasiveness & Confidence
5. Engagement & Relatability

**Bands:** 21-25 Excellent | 16-20 Strong | 11-15 Developing | 6-10 Early | 1-5 Starting

## Tracking

Progress is logged to a Google Sheet (created on first `/blog-review`).

**Spreadsheet ID:** _(will be populated after first session)_
