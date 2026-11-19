CREATE TABLE users (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  display_name VARCHAR(100) NOT NULL,
  email VARCHAR(190) NOT NULL,
  password_hash VARCHAR(100) NOT NULL,
  role VARCHAR(20) NOT NULL,
  created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  CONSTRAINT uq_users_email UNIQUE (email),
  CONSTRAINT ck_users_role CHECK (role IN ('LISTENER','ADMIN'))
);

CREATE TABLE songs (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  title VARCHAR(160) NOT NULL,
  artist VARCHAR(160) NOT NULL,
  album_name VARCHAR(160),
  genre VARCHAR(80),
  duration_seconds INT NOT NULL,
  audio_storage_name VARCHAR(100) NOT NULL,
  audio_content_type VARCHAR(80) NOT NULL,
  audio_size_bytes BIGINT NOT NULL,
  cover_storage_name VARCHAR(100),
  cover_content_type VARCHAR(80),
  feature_vector JSON,
  feature_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
  genre_source VARCHAR(40) NOT NULL DEFAULT 'PENDING',
  play_count BIGINT NOT NULL DEFAULT 0,
  created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  INDEX ix_songs_title (title),
  INDEX ix_songs_artist (artist),
  INDEX ix_songs_genre (genre),
  CONSTRAINT ck_song_duration CHECK (duration_seconds > 0),
  CONSTRAINT ck_feature_status CHECK (feature_status IN ('READY','PENDING'))
);

CREATE TABLE playlists (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  owner_id BIGINT NOT NULL,
  name VARCHAR(120) NOT NULL,
  created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  CONSTRAINT fk_playlist_owner FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT uq_playlist_owner_name UNIQUE (owner_id, name)
);

CREATE TABLE playlist_songs (
  playlist_id BIGINT NOT NULL,
  song_id BIGINT NOT NULL,
  position_no INT NOT NULL,
  added_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (playlist_id, song_id),
  CONSTRAINT fk_ps_playlist FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
  CONSTRAINT fk_ps_song FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE,
  CONSTRAINT uq_ps_position UNIQUE (playlist_id, position_no),
  CONSTRAINT ck_ps_position CHECK (position_no >= 0)
);

CREATE TABLE liked_songs (
  user_id BIGINT NOT NULL,
  song_id BIGINT NOT NULL,
  liked_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (user_id, song_id),
  CONSTRAINT fk_like_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_like_song FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE
);

CREATE TABLE play_history (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  song_id BIGINT NOT NULL,
  played_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  INDEX ix_history_user_time (user_id, played_at),
  CONSTRAINT fk_history_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_history_song FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE
);
