DELETE FROM robots_cache;

ALTER TABLE robots_cache
DROP COLUMN allowed,
ADD COLUMN rule_group VARCHAR(100) NOT NULL
AFTER robots_content;