-- PostGIS Spatial Schema Initialization

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Topological Road Segments Table
CREATE TABLE IF NOT EXISTS road_segments (
    edge_id VARCHAR(64) PRIMARY KEY,
    source_node_id BIGINT NOT NULL,
    target_node_id BIGINT NOT NULL,
    osm_way_id BIGINT,
    h3_cell VARCHAR(20) NOT NULL,
    length_meters DOUBLE PRECISION NOT NULL,
    curvature DOUBLE PRECISION DEFAULT 0.0,
    sinuosity DOUBLE PRECISION DEFAULT 1.0,
    speed_limit_kmh DOUBLE PRECISION DEFAULT 50.0,
    lanes INTEGER DEFAULT 1,
    highway_type VARCHAR(32) DEFAULT 'secondary',
    is_oneway BOOLEAN DEFAULT FALSE,
    is_bridge BOOLEAN DEFAULT FALSE,
    is_tunnel BOOLEAN DEFAULT FALSE,
    geom GEOMETRY(LineString, 4326),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_road_segments_h3 ON road_segments(h3_cell);
CREATE INDEX IF NOT EXISTS idx_road_segments_geom ON road_segments USING GIST(geom);

-- 2. Historical & Enriched Accidents Table
CREATE TABLE IF NOT EXISTS historical_accidents (
    id VARCHAR(64) PRIMARY KEY,
    is_accident BOOLEAN NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    h3_cell VARCHAR(20) NOT NULL,
    edge_id VARCHAR(64) REFERENCES road_segments(edge_id) ON DELETE SET NULL,
    temperature_c DOUBLE PRECISION,
    precipitation_mm DOUBLE PRECISION,
    wind_speed_kmh DOUBLE PRECISION,
    visibility_km DOUBLE PRECISION,
    humidity_pct DOUBLE PRECISION,
    solar_elevation_deg DOUBLE PRECISION,
    solar_azimuth_deg DOUBLE PRECISION,
    sun_glare_risk DOUBLE PRECISION,
    location GEOMETRY(Point, 4326),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_accidents_time ON historical_accidents(timestamp);
CREATE INDEX IF NOT EXISTS idx_accidents_h3 ON historical_accidents(h3_cell);
CREATE INDEX IF NOT EXISTS idx_accidents_location ON historical_accidents USING GIST(location);

-- 3. Serving Predictions & Hotspots Audit Table
CREATE TABLE IF NOT EXISTS prediction_audit_logs (
    prediction_id VARCHAR(64) PRIMARY KEY,
    forecast_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    num_edges INTEGER NOT NULL,
    num_hotspots INTEGER NOT NULL,
    latency_ms DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
