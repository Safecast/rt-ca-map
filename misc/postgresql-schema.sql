
-- -- User for the application client
-- -- Role: mapsuser
-- -- DROP ROLE IF EXISTS mapsuser;
-- CREATE ROLE mapsuser WITH
--   LOGIN
--   NOSUPERUSER
--   INHERIT
--   NOCREATEDB
--   NOCREATEROLE
--   NOREPLICATION
--   NOBYPASSRLS
--   ENCRYPTED PASSWORD 'SCRAM-SHA-256$4096:iAi3XpdI3/KZomGI1Yqrlg==$COzgKsq9oC773R03XbD2Zx/Ru34fAJunBGnnx8PuvWk=:dzF0z+ukNRuwKVNGPR4kEDhGCW3driSutilJLPVt/BM=';

-- Database: mapsdb
-- DROP DATABASE IF EXISTS mapsdb;
-- CREATE DATABASE mapsdb
--     WITH
--     OWNER = mapsuser
--     ENCODING = 'UTF8'
--     LC_COLLATE = 'C'
--     LC_CTYPE = 'C.UTF-8'
--     LOCALE_PROVIDER = 'libc'
--     TABLESPACE = pg_default
--     CONNECTION LIMIT = -1
--     IS_TEMPLATE = False;

-- GRANT TEMPORARY, CONNECT ON DATABASE mapsdb TO PUBLIC;
-- GRANT ALL ON DATABASE mapsdb TO mapsuser;
-- GRANT ALL ON DATABASE mapsdb TO postgres;


-- Device classes e.g. 'geigiecast'
CREATE TABLE IF NOT EXISTS device_classes (
        id SERIAL,  -- auto generate from sequence
        class TEXT UNIQUE,
        PRIMARY KEY (id)
);
ALTER TABLE device_classes OWNER TO mapsuser;

-- Device transports e.g. where the data came from, usually IP address
-- Given in JSON "current_values" as class:IP e.g. "geigiecast:216.59.235.178"
CREATE TABLE IF NOT EXISTS transports (
        id SERIAL PRIMARY KEY,  -- auto generate from sequence
        service_transport TEXT UNIQUE,  -- typically class:IP address .
        service_uploaded TIMESTAMP WITH TIME ZONE,  -- last time seen
        transport_ip_info TEXT  -- JSON dict giving description
);
ALTER TABLE transports OWNER TO mapsuser;

-- Devices
--  - assume that the text device URN is Safecast globally unique, 
--    therefore usable as a unique identifier to fetch from external 
--    data server (TT server)
--  - If numeric only device ID required, use urn.split(":")[1]
--  - ID serial is primary key
CREATE TABLE IF NOT EXISTS devices (
    id SERIAL,  -- auto generate from sequence
    urn TEXT NOT NULL UNIQUE,  -- if not unique, Safecast nomenclature problem
    last_seen TIMESTAMP WITH TIME ZONE NOT NULL,
    device_class INT REFERENCES device_classes(id),
    service_transport INT REFERENCES transports(id),
    display boolean DEFAULT TRUE,  -- If True, display on map
    active boolean DEFAULT TRUE,  -- If True, fetch new updates from Safecast database
    PRIMARY KEY (id)
);
ALTER TABLE devices OWNER TO mapsuser;

-- Measurements 
CREATE TABLE IF NOT EXISTS measurements (
    id SERIAL,  -- auto generate from sequence
    device INT NOT NULL REFERENCES devices(id),
    when_captured TIMESTAMP WITH TIME ZONE NOT NULL,
    loc_lat REAL NOT NULL,
    loc_lon REAL NOT NULL,
    lnd_7318u INT NOT NULL,
    PRIMARY KEY (device, when_captured)  -- prevent nonsense readings
);
ALTER TABLE measurements OWNER TO mapsuser;

