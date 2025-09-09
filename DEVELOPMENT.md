# Hive Photo Metadata Tracker — DEVELOPMENT Notes

**Mission (why):** Explore whether we can turn hive inspection photos into structured metadata (features, weather context, timelines) to give beekeepers evidence-based insights.  
**Date range:** 2025 · **Status:** Active (prototype phase)  
**Live app:** _TBD — served via Streamlit on EC2_  
**Primary tech:** Streamlit, Python, Google Cloud Vision API, Weather API integration, CSV/JSON export  
**Constraints:** Small dataset of personal hive photos; single-developer timebox; deployable on low-cost EC2

---

## Architecture (1-page)

```mermaid
flowchart LR
  User --> UI[Streamlit UI]
  UI --> ETL[Photo Upload & EXIF Parser]
  ETL --> Storage[Storage Abstraction Layer]
  Storage --> Local[Local Provider]
  Storage --> S3[S3 Cloud Provider]
  ETL --> CV[Vision API (labels, colors, annotations)]
  ETL --> WX[Weather API (by timestamp/location)]
  CV --> DB[(Metadata CSV/JSON)]
  WX --> DB
  DB --> Graph[Neo4j / NetworkX for relationships]
  UI --> Viz[Timeline & Dashboard]
  UI --> StorageMgmt[Storage Management UI]
```

**Assumptions:**  
- Timestamp + location in EXIF are reliable enough to join with weather.  
- Beekeepers prefer CSV/JSON export for portability.  

---

## Experiments & Decisions

### Key decisions

| Decision | Options considered | Why chosen | Impact | Revisit? |
|----------|--------------------|------------|--------|----------|
| **Vision API** | OpenCV, TorchVision, Google Cloud Vision | Vision API gave faster prototyping + labels beyond simple CV | Enabled early demo | Later explore on-prem for cost |
| **Metadata format** | SQLite, JSON, CSV | CSV/JSON simpler for analysis + sharing | Lightweight, transparent | Add DB if scaling |
| **Graph layer** | NetworkX, Neo4j | Neo4j aligns with portfolio goal (graphs, query power) | Showcase graph skills | Keep NetworkX fallback |
| **Storage architecture** | Direct local/cloud coupling, Storage abstraction layer | Abstraction layer for provider switching + migration | Clean separation, zero breaking changes | Monitor performance overhead |
| **Cloud storage** | Google Cloud Storage, AWS S3, Azure Blob | S3 for broader compatibility + cost predictability | Enterprise-ready, rich feature set | Evaluate GCS for Vision API synergy |

### Experiment log (selected)

- **H1:** Cloud Vision API provides meaningful labels for hive inspections.  
  **Result:** Labels capture color, general objects, but limited bee-specific classes.  
  **Decision:** Keep API but supplement with custom classifiers later.  

- **H2:** Weather overlay adds context to hive behavior patterns.  
  **Result:** Strong correlation with bee activity timelines.  
  **Decision:** Keep weather integration as core feature.

- **H3:** Storage abstraction layer enables seamless cloud integration without breaking changes.  
  **Method:** Built 3-phase implementation (abstraction → S3 → UI) with comprehensive test suite.  
  **Result:** Zero breaking changes, full backward compatibility, working S3 integration with one-click setup.  
  **Decision:** Production-ready storage system with local fallback.

- **H4:** Users need simple cloud setup without technical AWS knowledge.  
  **Method:** Built guided credential input with validation, auto bucket creation, real-time testing.  
  **Result:** Complete S3 setup in <2 minutes with clear error handling.  
  **Decision:** Keep one-click approach as primary cloud onboarding flow.  

---

## What worked / what didn’t

**Worked well**  
- Streamlit session-state flow for photo batch uploads  
- Weather API join by EXIF timestamp  
- CSV/JSON export for quick validation  
- Storage abstraction layer with zero breaking changes
- One-click S3 setup with automatic bucket configuration
- Comprehensive test suite with real AWS integration testing

**Didn't work (yet)**  
- Cloud Vision's lack of bee-specific labels → requires custom model  
- ~~Handling large image sets (upload latency)~~ → **Solved:** S3 multipart uploads + progress tracking
- Graph schema still too shallow for insight  

---

## Current limitations & risks
- Small personal dataset; generalizability unclear  
- API costs scale with image volume (mitigated: S3 cost estimation + monitoring)
- ~~Need for offline fallback if APIs are unavailable~~ → **Solved:** Local storage always available as fallback
- ~~Limited UX polish in current Streamlit app~~ → **Improved:** Storage management UI with guided setup  

---

## Next steps (tiny backlog)
- [ ] Design first **custom classifier** for bee/comb features  
- [ ] Extend Neo4j schema with temporal & condition nodes  
- [x] ~~Add thumbnail preview + batch progress bar~~ → **Completed:** S3 progress tracking + thumbnails
- [x] ~~Cloud storage integration~~ → **Completed:** Full S3 provider with management UI
- [ ] Draft Methods page in `/docs/guide/how-it-works.md`  
- [ ] Deploy to `docs.barbhs.com/beehive-tracker/`
- [ ] Add Google Cloud Storage provider for Vision API synergy
- [ ] Implement backup integrity verification (framework exists)  

---

## Repro (quick run)

```bash
git clone https://github.com/dagny099/beehive-tracker
cd beehive-tracker
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run run_tracker.py
```

---

## Change log (direction shifts)

- **2025-09-09:** **Major storage system overhaul** — Implemented complete storage abstraction with S3 cloud integration, one-click setup UI, and comprehensive test suite. Zero breaking changes, production-ready.
- **2025-09-09:** Chose Neo4j over NetworkX to align with graph/portfolio goals  
- **2025-08-15:** Added weather API overlay to photo metadata  
- **2025-07-30:** Pivoted from OpenCV prototype to Google Cloud Vision for faster labeling
