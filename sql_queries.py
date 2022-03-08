import configparser


# CONFIG
config = configparser.ConfigParser()
config.read('dwh.cfg')

# DROP TABLES

staging_events_table_drop = "DROP TABLE IF EXISTS staging_events"
staging_songs_table_drop = "DROP TABLE IF EXISTS staging_songs"
songplay_table_drop = "DROP TABLE IF EXISTS songplay_table"
user_table_drop = "DROP TABLE IF EXISTS user_table"
song_table_drop = "DROP TABLE IF EXISTS song_table"
artist_table_drop = "DROP TABLE IF EXISTS artist_table"
time_table_drop = "DROP TABLE IF EXISTS time_table"

# CREATE TABLES

staging_events_table_create= ("""
    CREATE TABLE staging_events(
        event_id INT IDENTITY(0,1) PRIMARY KEY,
        artist_name VARCHAR(255),
        auth VARCHAR(32),
        user_first_name VARCHAR(255),
        user_last_name VARCHAR(255),
        user_gender VARCHARD(32),
        item_in_session INTEGER,
        song_length DOUBLE PRECISION,
        user_level VARCHAR(32),
        location VARCHAR(100),
        method VARCHAR(32),
        page VARCHAR(32),
        registration VARCHAR(32), 
        session_id BIGINT,
        song_title VARCHAR(255),
        status INTEGER,
        ts BIGINT,
        user_agent TEXT,
        user_id VARCHAR(128)
    )
""")

staging_songs_table_create = ("""
    CREATE TABLE staging_songs(
        song_id VARCHAR(100) PRIMARY KEY,
        num_songs INTEGER,
        artist_id VARCHAR(100),
        artist_latitude DOUBLE PRECISION,
        artist_longitude DOUBLE PRECISION,
        artist_location VARCHAR(255),
        artist_name VARCHAR(255),
        title VARCHAR(255),
        duration DOUBLE PRECISION,
        year INTEGER,
    )
""")

songplay_table_create = ("""
    CREATE TABLE songplays(
        songplay_id INT IDENTITY(0,1) PRIMARY KEY,
        start_time TIMESTAMP,
        user_id VARCHAR(100),
        level VARCHAR(50),
        song_id VARCHAR(100),
        artist_id VARCHAR(100),
        session_id BIGINT,
        location VARCHAR(100),
        user_agent TEXT,
    )
""")

user_table_create = ("""
    CREATE TABLE users(
        user_id VARCHAR(100) PRIMARY KEY,
        first_name VARCHAR(255),
        last_name VARCHAR(255),
        gender VARCHARD(32),
        level VARCHAR(50),
    )
""")

song_table_create = ("""
    CREATE TABLE songs(
        song_id VARCHAR(100) PRIMARY KEY,
        title VARCHAR(255),
        artist_id VARCHAR(100),
        year INTEGER,
        duration DOUBLE PRECISION,
    )
""")

artist_table_create = ("""
    CREATE TABLE artists(
        artist_id VARCHAR(100) PRIMARY KEY,
        name VARCHAR(255),
        location VARCHAR(100),
        latitude DOUBLE PRECISION,
        longitude DOUBLE PRECISION,
    )
""")

time_table_create = ("""
    CREATE TABLE time(
        start_time TIMESTAMP PRIMARY KEY,
        hour INTEGER,
        day INTEGER,
        week INTEGER,
        month INTEGER,
        year INTEGER,
        weekday INTEGER,
    )
""")

# STAGING TABLES

staging_events_copy = ("""
    COPY staging_events
    FROM {}
    IAM_ROLE {}
    JSON {};
""").format(config.get('S3','LOG_DATA'), config.get('IAM_ROLE','DWH_ROLE_ARN'), config.get('S3','LOG_JSONPATH'))

staging_songs_copy = ("""
    COPY staging_songs
    FROM {}
    IAM_ROLE {}
    JSON 'auto';
""").format(config.get('S3','SONG_DATA'), config.get('IAM_ROLE','ARN'))

# FINAL TABLES

songplay_table_insert = ("""
    INSERT INTO songplays (start_time, user_id, level, song_id, artist_id, session_id, location, user_agent)
    SELECT
        TIMESTAMP 'epoch' + (se.ts / 1000) * INTERVAL '1 second' as start_time,
        se.user_id,
        se.user_level,
        so.song_id,
        so.artist_id,
        se.session_id,
        se.location,
        se.user_agent
    FROM staging_events se
    INNER JOIN staging_songs ss ON ss.title = se.song
    AND se.artist = so.artist_name
    WHERE se.page = 'NextSong';
""")

user_table_insert = ("""
    INSERT INTO users (user_id, first_name, last_name, gender, level)
    SELECT DISTINCT
        user_id,
        user_first_name,
        user_last_name,
        user_gender,
        user_level
    FROM staging_events
    WHERE page = 'NextSong';
""")

song_table_insert = ("""
    INSERT INTO songs (song_id, title, artist_id, year, duration)
    SELECT DISTINCT
        song_id,
        title,
        artist_id,
        year,
        duration
    FROM staging_songs
    WHERE song_id IS NOT NULL;
""")

artist_table_insert = ("""
    INSERT INTO artists (artist_id, name, location, latitude, longitude)
    SELECT DISTINCT
        artist_id,
        artist_name,
        artist_location,
        artist_latitude,
        artist_longitude
    FROM staging_songs
    WHERE artist_id IS NOT NULL;
""")

time_table_insert = ("""
    INSERT INTO time (start_time, hour, day, week, month, year, weekday)
    SELECT start_time,
        EXTRACT(hour FROM start_time),
        EXTRACT(day FROM start_time),
        EXTRACT(week FROM start_time),
        EXTRACT(month FROM start_time),
        EXTRACT(year FROM start_time),
        EXTRACT(dayofweek FROM start_time)
    FROM songplays;
""")

# QUERY LISTS

create_table_queries = [staging_events_table_create, staging_songs_table_create, songplay_table_create, user_table_create, song_table_create, artist_table_create, time_table_create]
drop_table_queries = [staging_events_table_drop, staging_songs_table_drop, songplay_table_drop, user_table_drop, song_table_drop, artist_table_drop, time_table_drop]
copy_table_queries = [staging_events_copy, staging_songs_copy]
insert_table_queries = [songplay_table_insert, user_table_insert, song_table_insert, artist_table_insert, time_table_insert]
