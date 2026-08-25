-- ========================================
-- Admin stats: count MiniMax generations
-- ========================================
--
-- Separate from 00015 because a new enum value cannot be referenced in the
-- transaction that adds it.

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
  (SELECT count(*) FROM generations WHERE created_at >= now() - interval '7 days') AS generations_last_7d,
  (SELECT count(*) FROM generations WHERE created_at >= now() - interval '30 days') AS generations_last_30d,
  (SELECT count(*) FROM brand_kits WHERE status = 'complete') AS brand_kits_complete,
  (SELECT count(*) FROM provider_keys WHERE is_active) AS active_provider_keys;

-- DROP VIEW discarded the grants from 00014; restore them.
REVOKE ALL ON admin_stats FROM anon, authenticated;
GRANT SELECT ON admin_stats TO service_role;
