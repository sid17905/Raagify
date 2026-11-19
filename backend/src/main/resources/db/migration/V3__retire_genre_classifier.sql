UPDATE songs SET genre='Unclassified',genre_source='UNCLASSIFIED'
WHERE genre_source IN ('MODEL','PLACEHOLDER');
ALTER TABLE songs DROP CHECK ck_genre_confidence,
                  DROP COLUMN genre_confidence,
                  DROP COLUMN genre_model;
