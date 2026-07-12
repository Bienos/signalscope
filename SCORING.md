# Scoring

Percentiles are calculated inside market/language/category/video-age cohorts after winsorising continuous inputs. AVS is `.25 views + .25 velocity + .15 share rate + .10 engagement + .10 acceleration + .10 baseline lift + .05 spread`. EVS is `.30 velocity + .25 acceleration + .15 percentage growth + .10 share velocity + .10 baseline lift + .10 novelty`. NPS and RFS follow the supplied product brief. Scores are 0-100. `adjusted = score * (1 - .5 * anomaly/100)`.

Example: AVS 80 and anomaly 20 gives adjusted 72. Emerging requires age <=72h, at least two snapshots, below the viral-view threshold, minimum absolute growth, and acceptable anomaly. Confidence combines snapshot count/continuity, completeness, freshness, cohort size and classification confidence.

## Version 2.0 evidence contract

Every stored score now includes component raw values, cohort percentiles, formula weights, cohort definition/sample size, confidence score, and score version. Cohorts currently use market, language, category, and video-age band. Creator-baseline lift is calculated relative to observed creator velocities in demo mode; production requires comparable licensed creator history. Spread is derived from unique creators sharing a sound or hashtag in the monitored sample. Small cohorts are marked as fallback evidence and reduce confidence.

Emerging eligibility is shared by the API and reports. It requires configurable age, snapshot, view-threshold, growth, anomaly, safety, completeness, and active-record checks. Failed conditions are returned explicitly.
