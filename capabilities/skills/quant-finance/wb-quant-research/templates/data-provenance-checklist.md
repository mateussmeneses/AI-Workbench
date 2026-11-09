# Data provenance checklist

- [ ] Source, license and terms of use recorded; redistribution allowed?
- [ ] Snapshot stored with ID/date and checksum; reruns use the same snapshot.
- [ ] Survivorship: delisted/expired instruments included for the full period.
- [ ] Corporate actions: splits/dividends adjusted consistently (and documented which).
- [ ] Timestamps: timezone, session hours, bar open vs close alignment verified.
- [ ] Look-ahead: features only use data available at decision time (lagged fundamentals, publication delays).
- [ ] Gaps, duplicates and outliers detected and handling documented.
- [ ] Point-in-time universe membership (index constituents) where relevant.
- [ ] Fees, spreads and funding/borrow rates sourced for the same venue and period.
- [ ] Any LLM/news-derived signal has its publication timestamp, not ingestion time.
