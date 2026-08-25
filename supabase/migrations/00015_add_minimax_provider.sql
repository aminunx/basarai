-- ========================================
-- Add MiniMax as a third image provider
-- ========================================
--
-- MiniMax's image-01 model is reachable on a Token Plan Subscription Key
-- (sk-cp…), which is a different credential from a pay-as-you-go API key.
--
-- Note: ALTER TYPE ... ADD VALUE cannot be followed by a use of the new value
-- in the same transaction, which is why the view below is recreated in a
-- separate statement rather than inline.

ALTER TYPE provider_t ADD VALUE IF NOT EXISTS 'minimax';

COMMENT ON COLUMN provider_keys.provider IS 'Provider type (openai, gemini or minimax)';
