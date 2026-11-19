ALTER TABLE songs ADD COLUMN genre_confidence DOUBLE NULL,
                  ADD COLUMN genre_model VARCHAR(160) NULL,
                  ADD CONSTRAINT ck_genre_confidence CHECK (genre_confidence IS NULL OR (genre_confidence >= 0 AND genre_confidence <= 1));
CREATE INDEX ix_history_played_at ON play_history(played_at);
CREATE INDEX ix_songs_popularity ON songs(play_count);
