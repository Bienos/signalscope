# Toy provider field mapping

Raw Clockworks names are accepted only by `app.providers.apify.schemas` and translated by
`app.providers.apify.normalizer`. Product APIs, scoring, reports and frontend code consume
provider-independent `ProviderVideo` fields.

## Video and creator identity

| Actor output | Normalised field | Rule |
|---|---|---|
| `id` | `id` | Required stable provider video ID |
| `webVideoUrl` | `url` | Required canonical evidence link; submitted URL is a refresh fallback |
| `createTimeISO` / `createTime` | `published_at` | ISO timestamp preferred; missing value is flagged |
| `text` | `caption` | Empty string only for compatibility and listed as missing |
| `textLanguage` | `language` | Provider language; `und` only when unavailable |
| `authorMeta.id` | `creator_id` | Required stable provider creator ID |
| `authorMeta.name` | `username` | Required public username |
| `authorMeta.nickName` | `creator_display_name` | Nullable |
| `authorMeta.profileUrl` | `creator_profile_url` | Nullable public profile link |
| `authorMeta.fans` | `creator_followers` | Nullable observed profile count; not a follower identity list |
| `authorMeta.verified` | `creator_verified` | Nullable provider-reported state |
| `locationCreated` | `creator_account_region` | Never audience geography and never collection market |

The normalised `market` value comes from the SignalScope collection request (`GB` or `PL`), not
`locationCreated`. The two concepts must remain separate in storage and API contracts.

## Engagement snapshots

| Actor output | Normalised metric | Missing behavior |
|---|---|---|
| `playCount` | `views` | Null plus `missing_fields=["views"]` |
| `diggCount` | `likes` | Null plus `missing_fields=["likes"]` |
| `commentCount` | `comments` | Count only; no comment bodies |
| `shareCount` | `shares` | Null plus `missing_fields=["shares"]` |
| `collectCount` | `saves` | Null plus `missing_fields=["saves"]` |

The current database calls saves `favourites`. The provider emits a temporary `favourites` alias
with the same nullable value so existing ingestion remains compatible. New domain contracts should
use `saves`; the alias can be removed after the database migration.

## Hashtags, sounds and post metadata

| Actor output | Normalised field | Rule |
|---|---|---|
| `hashtags[].id` | `hashtag_metadata[].provider_id` | Nullable provider ID |
| `hashtags[].name` | `hashtags[]`, `hashtag_metadata[].name` | Leading `#` removed |
| `hashtags[].title` | `hashtag_metadata[].title` | Nullable display title |
| `musicMeta.musicId` | `sound_id` | Missing value is explicit |
| `musicMeta.musicName` | `sound_title` | Nullable |
| `musicMeta.musicAuthor` | `sound_author` | Nullable metadata only |
| `musicMeta.musicOriginal` | `sound_original` | Nullable; does not establish commercial rights |
| `videoMeta.duration` | `duration_seconds` | Nullable |
| `isAd` | `is_ad` | Nullable provider-reported flag |
| `isPinned` | `is_pinned` | Nullable provider-reported flag |
| `isSlideshow` | `is_slideshow` | Nullable provider-reported flag |
| `searchQuery` | `discovery_queries[]` | Combined with typed request context |

## Generated provenance

The provider adds:

- `retrieved_at` and `freshness_at` in UTC;
- `provider_run_id` and `dataset_id`;
- `collection_type` and configured collection market;
- query/source context;
- token-free `apify://` evidence reference;
- top-level schema fingerprint;
- `normalizer_version`;
- explicit `missing_fields` and `availability_status`.

Invalid items receive only a quarantine category, redacted summary, item index and schema
fingerprint. The package does not persist the raw item.

## Deliberately discarded data

The provider model has no field for:

- full video, audio, cover, slideshow or avatar URLs/files;
- comment or reply bodies;
- subtitles or transcripts;
- follower/following identities;
- TikTok Shop details;
- audience geography;
- inferred creator age, child identity or child classification.

Unexpected extra Actor fields are ignored. Schema fingerprints make shape changes observable
without leaking raw payloads into product code.
