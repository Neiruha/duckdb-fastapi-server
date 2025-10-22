BEGIN TRANSACTION;
DROP INDEX IF EXISTS ux_client_tokens_hash;
ALTER TABLE client_tokens DROP COLUMN IF EXISTS token_hash;
ALTER TABLE client_tokens DROP COLUMN IF EXISTS "role";
ALTER TABLE client_tokens DROP COLUMN IF EXISTS last_used_at;
ALTER TABLE client_tokens ADD COLUMN IF NOT EXISTS payload_json JSON;
COMMIT;
