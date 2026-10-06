ALTER TABLE robots_cache
ADD COLUMN robots_content LONGTEXT NOT NULL
AFTER robots_url;