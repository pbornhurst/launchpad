# Pathfinder Deep Dives

---

### PF-001 What Pathfinder Is and Why It Exists
- **Difficulty:** beginner
- **Durations:** 1 min, 3 min
- **Core thesis:** Pathfinder is DoorDash's POS product — it exists because owning the in-store transaction layer gives DoorDash a complete view of a restaurant's business and creates a stickier, more valuable merchant relationship.
- **Key talking points:**
  1. What Pathfinder does: full POS system for restaurants — order entry, card payments, KDS, reporting
  2. Why DoorDash built it: controlling in-store data completes the picture (delivery + dine-in + pickup)
  3. The strategic logic: a merchant using DoorDash for everything is less likely to churn on any one product
  4. How it fits the Commerce Platform: Pathfinder is the in-store piece alongside Marketplace and Storefront
- **Real-world hooks:** Restaurants that run both DoorDash delivery and Pathfinder POS, seeing unified reporting for the first time. The "why would a delivery company build a cash register?" question that comes up in every pitch.
- **Landmine to avoid:** Don't make it sound like Pathfinder is just a data grab — it genuinely solves real problems for operators. Lead with merchant value.

---

### PF-002 The Pathfinder Activation Journey
- **Difficulty:** intermediate
- **Durations:** 3 min, 5 min
- **Core thesis:** Getting a restaurant from "signed contract" to "actively using the POS daily" is a multi-week journey with specific milestones, and most churn happens when activation stalls — making this journey the most important thing to get right.
- **Key talking points:**
  1. The lifecycle stages: Close/Win → Onboarding Call → Hardware Install → Go-Live → Activation (70+ orders/week)
  2. What activation means: sustained weekly card volume that shows the restaurant is actually relying on the POS
  3. Where it breaks: delayed installs, staff not trained, menu not configured correctly, card reader issues at launch
  4. The metrics: days from CW to OB, OB to install, install to go-active, and whether they sustain activation
  5. The AM role: the onboarding call and first 30 days are make-or-break for long-term retention
- **Real-world hooks:** Mx who activated in 3 days vs mx who took 60 days. The correlation between onboarding call quality and activation speed. Specific support patterns that predict churn (e.g., 3+ tickets in week 1).
- **Landmine to avoid:** Don't blame the merchant for slow activation — it's usually a system problem (delayed hardware, poor training, config issues). Own the process.

---

### PF-003 Card Reader Reliability — Engineering Trust
- **Difficulty:** intermediate
- **Durations:** 1 min, 3 min
- **Core thesis:** For a restaurant owner, a card reader that doesn't work means they can't take payments — which means they can't run their business. Card reader reliability isn't a tech problem; it's a trust problem.
- **Key talking points:**
  1. The stakes: a dead card reader during lunch rush = lost revenue + angry customers + panicked staff
  2. Common issues: USB disconnection, chip read failures, firmware bugs, WiFi-dependent readers losing connection
  3. Why it's hard: card readers operate in harsh environments (heat, grease, drops) and connect to multiple systems (POS, payment processor, network)
  4. The support cost: card reader issues drive more support volume than any other category
- **Real-world hooks:** The WisePOS → M2 Puck migration and what it fixed (and didn't). The USB port color issue on Elo devices. Restaurants that keep a backup reader at every station. The time a firmware update bricked readers across multiple locations simultaneously.
- **Landmine to avoid:** Don't be defensive about hardware issues — acknowledge them honestly. The audience respects transparency about failure modes more than perfection claims.

---

### PF-004 How We Measure POS Success
- **Difficulty:** advanced
- **Durations:** 3 min, 5 min
- **Core thesis:** Measuring POS success requires looking beyond just "is it installed?" to a layered set of metrics that capture activation, engagement, reliability, and ultimately merchant retention.
- **Key talking points:**
  1. Vanity metrics vs real metrics: "stores installed" is meaningless if they're not actively using it
  2. The activation metric: Orders per Store Week (OSW) — 70+ weekly card transactions as the activation threshold
  3. Engagement depth: card GOV, average transaction value, feature adoption (KDS, reporting, multi-location management)
  4. Health signals: support ticket volume, MSAT scores, volume trends (growing, stable, declining, dark)
  5. The ultimate metric: merchant retention and expansion (adding locations, adopting ancillary products)
- **Real-world hooks:** How the Pathfinder team evolved its success metrics over time. The dashboard that shows stores going dark before the AM knows. Mx who looked "active" on install count but were barely using the POS.
- **Landmine to avoid:** Don't present metrics as purely objective — choosing what to measure reflects what you value. Be thoughtful about the incentives each metric creates.
