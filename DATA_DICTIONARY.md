# Data dictionary

Core retained entities: provider/run provenance and quality; creator provider ID, username/display name, supplied region/followers and review flags; video provider ID, canonical URL, caption, language/market/category/product category, publication/duration, supplied child/minor flags, sound relation and review state; immutable snapshots of views/likes/comments/shares/favourites/followers and freshness/missing fields; hashtags/sounds and joins; classifications with confidence/explanation/model/prompt/review; clusters/members; creator baselines; viral scores and interval metrics; safety flags/reviews; daily reports/entries; settings/jobs; deletion audit.

No full video is retained. Creator region is explicitly not audience geography. JSON fields preserve missing indicators and provider references without secrets.

