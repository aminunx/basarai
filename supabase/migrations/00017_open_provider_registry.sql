-- ========================================
-- Open the provider list: enum -> text, plus per-brand custom providers
-- ========================================
--
-- provider_t made every new provider a schema change. Providers are now
-- validated in the application against the built-in catalogue plus whatever
-- the brand has registered, so the column only needs to hold an identifier.
--
-- Existing values ('openai', 'gemini', 'minimax') survive the cast unchanged.
--
-- admin_stats reads generations.provider, and Postgres refuses to alter a
-- column a view depends on — so the view is dropped here and rebuilt in 00018.
-- Every step is written to be safe to re-run, because a failure part-way
-- through leaves the two tables in different states.

DROP VIEW IF EXISTS admin_stats;

ALTER TABLE provider_keys ALTER COLUMN provider TYPE text USING provider::text;
ALTER TABLE generations   ALTER COLUMN provider TYPE text USING provider::text;

DROP TYPE IF EXISTS provider_t;

-- A slug is what the rest of the system keys on, so keep it URL-safe and
-- distinct from any built-in id (enforced in the application, which is the
-- only place that knows the built-in list).
ALTER TABLE provider_keys DROP CONSTRAINT IF EXISTS chk_provider_keys_provider_format;
ALTER TABLE provider_keys
  ADD CONSTRAINT chk_provider_keys_provider_format
  CHECK (provider ~ '^[a-z0-9][a-z0-9_-]{0,38}[a-z0-9]$');

ALTER TABLE generations DROP CONSTRAINT IF EXISTS chk_generations_provider_format;
ALTER TABLE generations
  ADD CONSTRAINT chk_generations_provider_format
  CHECK (provider ~ '^[a-z0-9][a-z0-9_-]{0,38}[a-z0-9]$');

COMMENT ON COLUMN provider_keys.provider IS
  'Provider identifier — a built-in catalogue id or a custom_providers.slug';
COMMENT ON COLUMN generations.provider IS
  'Provider identifier — a built-in catalogue id or a custom_providers.slug';

-- ========================================
-- Custom providers
-- ========================================
--
-- Brand-scoped, like every other resource here: a custom endpoint belongs to
-- exactly one brand and is never visible to another.

CREATE TABLE IF NOT EXISTS custom_providers (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_id    UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
  slug        TEXT NOT NULL,
  label       TEXT NOT NULL,
  base_url    TEXT NOT NULL,
  model       TEXT NOT NULL,
  auth_style  TEXT NOT NULL DEFAULT 'bearer',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT chk_custom_providers_slug   CHECK (slug ~ '^[a-z0-9][a-z0-9_-]{0,38}[a-z0-9]$'),
  CONSTRAINT chk_custom_providers_label  CHECK (char_length(label) BETWEEN 1 AND 60),
  CONSTRAINT chk_custom_providers_model  CHECK (char_length(model) BETWEEN 1 AND 200),
  CONSTRAINT chk_custom_providers_auth   CHECK (auth_style IN ('bearer', 'x-api-key')),
  -- https only: an API key must never travel in clear text.
  CONSTRAINT chk_custom_providers_url    CHECK (base_url ~* '^https://[a-z0-9.-]+(:[0-9]+)?(/[^\s]*)?$')
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_custom_providers_slug ON custom_providers(brand_id, slug);
CREATE INDEX IF NOT EXISTS idx_custom_providers_brand ON custom_providers(brand_id, created_at DESC);

DROP TRIGGER IF EXISTS trg_custom_providers_updated_at ON custom_providers;
CREATE TRIGGER trg_custom_providers_updated_at
  BEFORE UPDATE ON custom_providers
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

COMMENT ON TABLE custom_providers IS
  'User-registered OpenAI-compatible image endpoints, scoped to one brand';
COMMENT ON COLUMN custom_providers.slug IS
  'Identifier stored in provider_keys.provider and generations.provider';
COMMENT ON COLUMN custom_providers.base_url IS
  'API root, https only; /images/generations is appended by the adapter';

-- ========================================
-- RLS — same rules as every other brand-scoped table
-- ========================================

ALTER TABLE custom_providers ENABLE ROW LEVEL SECURITY;
ALTER TABLE custom_providers FORCE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS custom_providers_select_own ON custom_providers;
CREATE POLICY custom_providers_select_own ON custom_providers
  FOR SELECT USING (is_brand_owner(brand_id));

DROP POLICY IF EXISTS custom_providers_insert_own ON custom_providers;
CREATE POLICY custom_providers_insert_own ON custom_providers
  FOR INSERT WITH CHECK (is_brand_owner(brand_id));

DROP POLICY IF EXISTS custom_providers_update_own ON custom_providers;
CREATE POLICY custom_providers_update_own ON custom_providers
  FOR UPDATE USING (is_brand_owner(brand_id)) WITH CHECK (is_brand_owner(brand_id));

DROP POLICY IF EXISTS custom_providers_delete_own ON custom_providers;
CREATE POLICY custom_providers_delete_own ON custom_providers
  FOR DELETE USING (is_brand_owner(brand_id));
