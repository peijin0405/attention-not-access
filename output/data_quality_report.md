# Data Quality Report

- Images processed: 33
- Sessions extracted: 147
- Speaker rows extracted: 277
- Structured rows written: 312

## Missing Field Counts

- source_file: 0
- event_name: 0
- date: 312
- start_time: 0
- end_time: 0
- stage_or_venue: 20
- session_title: 5
- session_type: 199
- session_description: 312
- speaker_name: 35
- speaker_title: 312
- speaker_company: 38
- topic_category: 0
- raw_text: 0
- confidence_level: 0
- notes: 0

## Low-Confidence Rows

- 1. IMG_3324.PNG | 09:30 am-11:30 am | & Web3 . | notes: No full date visible in OCR. Session title contains likely OCR artifacts. No speaker name visible or confidently extracted.
- 2. IMG_3327.PNG | 10:45 am-10:48 am | Spotlight on Success: FemT3ch | notes: Missing or uncertain stage/venue. No full date visible in OCR.
- 3. IMG_3328.PNG | 10:50 am-11:05 am | Turning Hoodies Into Suits: Charting Today’s Disruption, Shaping Tomorrow’s Finance. Presented by Association for Women in Cryptocurrency | notes: Missing or uncertain stage/venue. No full date visible in OCR.
- 4. IMG_3332.PNG | 12:30 pm-12:40 pm | (missing title) | notes: Missing session title from OCR context. No full date visible in OCR. No speaker name visible or confidently extracted.
- 5. IMG_3334.PNG | 12:45 pm-01:15 pm | (missing title) | notes: Missing session title from OCR context. No full date visible in OCR. No speaker name visible or confidently extracted.
- 6. IMG_3336.PNG | 02:00 pm-02:15 pm | Store, Grow, Spend: Leading The Evolution of Personal Finance. Presented by Tangem | notes: Missing or uncertain stage/venue. No full date visible in OCR. No speaker name visible or confidently extracted.
- 7. IMG_3339.PNG | 03:40 pm-04:05 pm | PANEL: From Surviving to Thriving: How Blockchain Opens Doors for Women | notes: Missing or uncertain stage/venue. No full date visible in OCR. No speaker name visible or confidently extracted.
- 8. IMG_3342.PNG | 05:30 pm-06:00 pm | TRADFI TO DEFI PANEL: TradFi Meets DeFi: Building Bridges in Blockchain | notes: Missing or uncertain stage/venue. No full date visible in OCR.
- 9. IMG_3342.PNG | 05:30 pm-06:00 pm | TRADFI TO DEFI PANEL: TradFi Meets DeFi: Building Bridges in Blockchain | notes: Missing or uncertain stage/venue. No full date visible in OCR.
- 10. IMG_3342.PNG | 05:30 pm-06:00 pm | TRADFI TO DEFI PANEL: TradFi Meets DeFi: Building Bridges in Blockchain | notes: Missing or uncertain stage/venue. No full date visible in OCR.
- 11. IMG_3342.PNG | 05:30 pm-06:00 pm | TRADFI TO DEFI PANEL: TradFi Meets DeFi: Building Bridges in Blockchain | notes: Missing or uncertain stage/venue. No full date visible in OCR.
- 12. IMG_3342.PNG | 05:30 pm-06:00 pm | TRADFI TO DEFI PANEL: TradFi Meets DeFi: Building Bridges in Blockchain | notes: Missing or uncertain stage/venue. No full date visible in OCR.
- 13. IMG_3344.PNG | 09:00 am-10:00 am | (missing title) | notes: Missing session title from OCR context. No full date visible in OCR. No speaker name visible or confidently extracted.
- 14. IMG_3345.PNG | 10:05 am-10:35 am | PAYMENTS PANEL: The Next Transaction: How Payments Power Digital Adoption | notes: Missing or uncertain stage/venue. No full date visible in OCR.
- 15. IMG_3345.PNG | 10:05 am-10:35 am | PAYMENTS PANEL: The Next Transaction: How Payments Power Digital Adoption | notes: Missing or uncertain stage/venue. No full date visible in OCR.
- 16. IMG_3345.PNG | 10:05 am-10:35 am | PAYMENTS PANEL: The Next Transaction: How Payments Power Digital Adoption | notes: Missing or uncertain stage/venue. No full date visible in OCR.
- 17. IMG_3349.PNG | 11:50 am-12:00 pm | (missing title) | notes: Missing session title from OCR context. No full date visible in OCR. No speaker name visible or confidently extracted.
- 18. IMG_3349.PNG | 12:00 pm-12:35 pm | GAMING PANEL: Beyond Play- to-Earn: Building Real Ownership in Web3 Gaming | notes: Missing or uncertain stage/venue. No full date visible in OCR.
- 19. IMG_3350.PNG | 12:25 pm-12:50 pm | (missing title) | notes: Missing session title from OCR context. No full date visible in OCR. No speaker name visible or confidently extracted.
- 20. IMG_3352.PNG | 02:00 pm-02:05 pm | Day 2 | notes: Missing or uncertain stage/venue. No full date visible in OCR. No speaker name visible or confidently extracted.
- 21. IMG_3354.PNG | 03:15 pm-03:25 pm | Pack Your Bags for the Supercycle. Presented by Sarsons Fund | notes: Missing or uncertain stage/venue. No full date visible in OCR.
- 22. IMG_3355.PNG | 04:05 pm-04:30 pm | Fireside Chat: Coalition: How Non-Profits and Brands Embrace Digital Assets | notes: Missing or uncertain stage/venue. No full date visible in OCR.
- 23. IMG_3355.PNG | 04:05 pm-04:30 pm | Fireside Chat: Coalition: How Non-Profits and Brands Embrace Digital Assets | notes: Missing or uncertain stage/venue. No full date visible in OCR.
- 24. IMG_3355.PNG | 04:05 pm-04:30 pm | Fireside Chat: Coalition: How Non-Profits and Brands Embrace Digital Assets | notes: Missing or uncertain stage/venue. No full date visible in OCR.
- 25. IMG_3355.PNG | 04:05 pm-04:30 pm | Fireside Chat: Coalition: How Non-Profits and Brands Embrace Digital Assets | notes: Missing or uncertain stage/venue. No full date visible in OCR.
- 26. IMG_3355.PNG | 04:05 pm-04:30 pm | Fireside Chat: Coalition: How Non-Profits and Brands Embrace Digital Assets | notes: Missing or uncertain stage/venue. No full date visible in OCR.

## Common OCR Issues

- Decorative mobile-app icons are sometimes recognized as stray characters such as HH, FA, or punctuation.
- Venue bullets can be recognized as ©, e, @, or o, so venue parsing normalizes these but may still be imperfect.
- Speaker titles are generally not visible in the agenda list screenshots and are left blank.
- Full agenda dates are often not visible; partial month-tab text is not treated as a reliable date.
- Company names are extracted only when OCR preserves the visible parenthesized company pattern.

## Recommendations For Manual Review

- Review every low-confidence row and every row with blank title, time, venue, or speaker fields.
- Validate multi-speaker panels against the screenshots, especially where names or companies contain OCR punctuation errors.
- Fill speaker titles from a speaker-detail source if required; they are not reliably present in these agenda-list screenshots.
- Confirm the conference date from the app day selector or an external official agenda before using the date field analytically.
