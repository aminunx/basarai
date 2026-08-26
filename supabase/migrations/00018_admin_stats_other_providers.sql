-- ========================================
-- Admin stats: count providers outside the native three
-- ========================================
--
-- With an open provider list, a fixed per-provider breakdown can no longer be
-- complete. The three native adapters keep their own counters — they are the
-- ones with bespoke code worth watching — and everything else (catalogue
-- entries on the OpenAI-compatible adapter, plus custom endpoints) rolls up
-- into generations_other, so the parts still sum to the total.

DROP VIEW IF EXISTS admin_stats;

CREATE VIEW admin_stats AS
SELECT
  (SELECT count(*) FROM profiles) AS total_accounts,
  (SELECT count(*) FROM brands) AS total_brands,
  (SELECT count(*) FROM generations) AS total_generations,
  (SELECT count(*) FROM generations WHERE status = 'pending') AS generations_pending,
  (SELECT count(*) FROM generations WHERE status = 'processing') AS generations_processing,
  (SELECT count(*) FROM generations WHERE status = 'succeeded') AS generations_succeeded,
  (SELECT count(*) FROM generations WHERE status = 'failed') AS generations_failed,
  (SELECT count(*) FROM generations WHERE provider = 'openai') AS generations_openai,
  (SELECT count(*) FROM generations WHERE provider = 'gemini') AS generations_gemini,
  (SELECT count(*) FROM generations WHERE provider = 'minimax') AS generations_minimax,
  (SELECT count(*) FROM generations
     WHERE provider NOT IN ('openai', 'gemini', 'minimax')) AS generations_other,
  (SELECT count(*) FROM generations WHERE created_at >= now() - interval '7 days') AS generations_last_7d,
  (SELECT count(*) FROM generations WHERE created_at >= now() - interval '30 days') AS generations_last_30d,
  (SELECT count(*) FROM brand_kits WHERE status = 'complete') AS brand_kits_complete,
  (SELECT count(*) FROM provider_keys WHERE is_active) AS active_provider_keys,
  (SELECT count(*) FROM custom_providers) AS custom_providers_registered;

-- DROP VIEW discarded the grants; restore them.
REVOKE ALL ON admin_stats FROM anon, authenticated;
GRANT SELECT ON admin_stats TO service_role;
