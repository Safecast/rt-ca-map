-- Database Schema for Real-Time Map Application
-- PostgreSQL 16.9
-- psycopg 3.2.6

-- Superuser (me!)
-- Role: louis
-- DROP ROLE IF EXISTS louis;
CREATE ROLE louis WITH
  LOGIN
  SUPERUSER
  INHERIT
  NOCREATEDB
  NOCREATEROLE
  NOREPLICATION
  NOBYPASSRLS
  ENCRYPTED PASSWORD 'SCRAM-SHA-256$4096:S5etb8hA9sUDvD6KDAddaA==$IDF2Y9oKVqO3oI+vNKnDYpvlSC1sB1foiCOPYAdrxm8=:HfgoCNAzzy6xToIZ7WeZdGq9fRB78NfjQs4lF2vug8A=';

-- User for the application client
-- Role: mapsuser
-- DROP ROLE IF EXISTS mapsuser;
CREATE ROLE mapsuser WITH
  LOGIN
  NOSUPERUSER
  INHERIT
  NOCREATEDB
  NOCREATEROLE
  NOREPLICATION
  NOBYPASSRLS
  ENCRYPTED PASSWORD 'SCRAM-SHA-256$4096:iAi3XpdI3/KZomGI1Yqrlg==$COzgKsq9oC773R03XbD2Zx/Ru34fAJunBGnnx8PuvWk=:dzF0z+ukNRuwKVNGPR4kEDhGCW3driSutilJLPVt/BM=';

-- Database: mapsdb
-- DROP DATABASE IF EXISTS mapsdb;
CREATE DATABASE mapsdb
    WITH
    OWNER = mapsuser
    ENCODING = 'UTF8'
    LC_COLLATE = 'C'
    LC_CTYPE = 'C.UTF-8'
    LOCALE_PROVIDER = 'libc'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1
    IS_TEMPLATE = False;

GRANT TEMPORARY, CONNECT ON DATABASE mapsdb TO PUBLIC;
GRANT ALL ON DATABASE mapsdb TO mapsuser;
GRANT ALL ON DATABASE mapsdb TO postgres;


-- Device classes e.g. 'geigiecast'
CREATE TABLE IF NOT EXISTS device_classes (
        id SERIAL,  -- auto generate from sequence
        class TEXT UNIQUE,
        PRIMARY KEY (id)
);

-- Device transports e.g. where the data came from, usually IP address
-- Given in JSON "current_values" as class:IP e.g. "geigiecast:216.59.235.178"
CREATE TABLE IF NOT EXISTS transports (
        id SERIAL UNIQUE,  -- auto generate from sequence
        service_transport TEXT PRIMARY KEY,  -- typically class:IP address .
        service_uploaded TIMESTAMP WITH TIME ZONE,  -- last time seen
        transport_ip_info TEXT  -- JSON dict giving description
);

-- Devices
--  - assume that the numeric device ID is Safecast globally unique, 
--    therefore usable as a primary key
--  - device URN required to fetch from external data server (TT server)
CREATE TABLE IF NOT EXISTS devices (
    id SERIAL,  -- auto generate from sequence
    device INT UNIQUE,
    urn TEXT NOT NULL UNIQUE,  -- if not unique, Safecast nomenclature problem
    device_class INT REFERENCES device_classes(id),
    service_transport INT REFERENCES transports(id),
    display boolean DEFAULT TRUE,  -- If True, display on map
    active boolean DEFAULT TRUE,  -- If True, fetch new updates from Safecast database
    PRIMARY KEY (id)
);


-- Measurements 
CREATE TABLE IF NOT EXISTS measurements (
    id SERIAL,  -- auto generate from sequence
    device INT NOT NULL REFERENCES devices(device),
    when_captured TIMESTAMP WITH TIME ZONE NOT NULL,
    loc_lat REAL NOT NULL,
    loc_lon REAL NOT NULL,
    lnd_7318u INT NOT NULL,
    PRIMARY KEY (device, when_captured)  -- prevent nonsense readings
);

-- postgres=# \l
--                                                    List of databases
--    Name    |  Owner   | Encoding | Locale Provider | Collate |  Ctype  | ICU Locale | ICU Rules |   Access privileges   
-- -----------+----------+----------+-----------------+---------+---------+------------+-----------+-----------------------
--  mapsdb    | postgres | UTF8     | libc            | C       | C.UTF-8 |            |           | =Tc/postgres         +
--            |          |          |                 |         |         |            |           | postgres=CTc/postgres+
--            |          |          |                 |         |         |            |           | mapsuser=CTc/postgres
--  postgres  | postgres | UTF8     | libc            | C       | C.UTF-8 |            |           | 
--  template0 | postgres | UTF8     | libc            | C       | C.UTF-8 |            |           | =c/postgres          +
--            |          |          |                 |         |         |            |           | postgres=CTc/postgres
--  template1 | postgres | UTF8     | libc            | C       | C.UTF-8 |            |           | =c/postgres          +
--            |          |          |                 |         |         |            |           | postgres=CTc/postgres
-- (4 rows)

-- postgres=# \d
--                  List of relations
--  Schema |         Name          |   Type   | Owner 
-- --------+-----------------------+----------+-------
--  public | device_classes        | table    | louis
--  public | device_classes_id_seq | sequence | louis
--  public | devices               | table    | louis
--  public | devices_id_seq        | sequence | louis
--  public | measurements          | table    | louis
--  public | measurements_id_seq   | sequence | louis
--  public | transports            | table    | louis
--  public | transports_id_seq     | sequence | louis
-- (8 rows)


