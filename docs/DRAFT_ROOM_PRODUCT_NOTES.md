# Draft Room Product Notes

## Pinned: bring Draft Pulse + Draft Forecast into the Draft Room

The old/legacy main workspace currently contains two useful concepts that must
NOT be lost while the Home Hub replaces that page:

1. **Live Draft Pulse**
   - recent position activity
   - position-run awareness
   - "what is happening right now" signal

2. **Draft Forecast**
   - what positions are likely to go before the user's next pick
   - likely runs / volume
   - forward-looking board pressure

### Product direction

The Draft Room is the primary drafting product.

These concepts should eventually become compact Draft Room surfaces, not reasons
to keep the legacy War Room as the primary UI. Candidate destinations:

- a compact Pulse strip above/beside Available Players;
- a small expandable Forecast card inside Gridiron AI;
- contextual run alerts near the recommendation ("WR run accelerating");
- never another dense always-visible dashboard.

Do not delete the existing DraftPulseWidget / forecast logic until the best
parts have been migrated into the Draft Room.
