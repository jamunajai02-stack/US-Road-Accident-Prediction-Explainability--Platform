import React, { useEffect, useRef, useState } from 'react';
import maplibregl, { Map, Marker, Popup } from 'maplibre-gl';
import { EdgeRiskPrediction, HotspotCluster, Waypoint } from '../../api/types';
import { parseWktLineString } from '../../utils/wkt';
import { Navigation, Layers } from 'lucide-react';
import { getRiskColorHex } from '../../utils/risk';

interface MapContainerProps {
  predictions?: EdgeRiskPrediction[];
  hotspots?: HotspotCluster[];
  primaryRouteWkt?: string;
  detourRouteWkt?: string;
  originWaypoint?: Waypoint | null;
  destinationWaypoint?: Waypoint | null;
  onMapClickWaypoint?: (waypoint: Waypoint) => void;
  onSelectHotspot?: (clusterId: string) => void;
  selectedHotspotId?: string | null;
  className?: string;
  isPickingWaypoint?: 'origin' | 'destination' | null;
}

export const MapContainer: React.FC<MapContainerProps> = ({
  predictions = [],
  hotspots = [],
  primaryRouteWkt,
  detourRouteWkt,
  originWaypoint,
  destinationWaypoint,
  onMapClickWaypoint,
  onSelectHotspot,
  selectedHotspotId,
  className = 'h-[600px] w-full',
  isPickingWaypoint = null,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<Map | null>(null);
  const markersRef = useRef<Marker[]>([]);
  const [mapLoaded, setMapLoaded] = useState(false);

  // References to avoid stale closures in event listeners
  const onMapClickWaypointRef = useRef(onMapClickWaypoint);
  const isPickingWaypointRef = useRef(isPickingWaypoint);

  useEffect(() => {
    onMapClickWaypointRef.current = onMapClickWaypoint;
    isPickingWaypointRef.current = isPickingWaypoint;
  }, [onMapClickWaypoint, isPickingWaypoint]);

  // Initialize MapLibre GL
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: {
        version: 8,
        sources: {
          osm: {
            type: 'raster',
            tiles: [
              'https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png',
              'https://b.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}@2x.png',
            ],
            tileSize: 256,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
          },
        },
        layers: [
          {
            id: 'osm-layer',
            type: 'raster',
            source: 'osm',
            minzoom: 0,
            maxzoom: 19,
          },
        ],
      },
      center: [-122.4194, 37.7749], // San Francisco default
      zoom: 12,
      maxZoom: 18, // Fixed Issue 2: black map on heavy zoom
    });

    map.on('load', () => {
      setMapLoaded(true);
    });

    // Fixed Issue 3: Manual Waypoint Map Click
    map.on('click', (e) => {
      if (isPickingWaypointRef.current && onMapClickWaypointRef.current) {
        onMapClickWaypointRef.current({
          latitude: e.lngLat.lat,
          longitude: e.lngLat.lng,
        });
      }
    });

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Update Markers & Layers when props change
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded) return;

    // Clear previous custom HTML markers
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];

    // 0. Render Live Road Segment Risk Predictions (Issue 1)
    const riskFeatures = predictions
      .map(p => {
        const geo = parseWktLineString(p.geometry_wkt);
        if (!geo) return null;
        return {
          type: 'Feature',
          geometry: geo,
          properties: {
            id: p.edge_id,
            risk: p.risk_probability,
            color: getRiskColorHex(p.risk_band)
          }
        };
      })
      .filter(f => f !== null) as any[];

    const predictionsSource = map.getSource('predictions-source') as maplibregl.GeoJSONSource;
    if (predictionsSource) {
      predictionsSource.setData({
        type: 'FeatureCollection',
        features: riskFeatures,
      });
    } else if (riskFeatures.length > 0) {
      map.addSource('predictions-source', {
        type: 'geojson',
        data: {
          type: 'FeatureCollection',
          features: riskFeatures,
        }
      });
      map.addLayer({
        id: 'predictions-layer',
        type: 'line',
        source: 'predictions-source',
        layout: { 'line-join': 'round', 'line-cap': 'round' },
        paint: {
          'line-color': ['get', 'color'],
          'line-width': ['interpolate', ['linear'], ['zoom'], 10, 2, 15, 6],
          'line-opacity': 0.8,
        },
      }, 'detour-route-layer'); // try to insert below routes if exist

      // Fit map to predictions if no route is currently showing
      if (!primaryRouteWkt && riskFeatures.length > 0) {
        const bounds = new maplibregl.LngLatBounds();
        riskFeatures.forEach(f => {
          f.geometry.coordinates.forEach((c: any) => bounds.extend(c));
        });
        map.fitBounds(bounds, { padding: 40, maxZoom: 14, duration: 1000 });
      }
    }

    // 1. Render Hotspot Clusters as pulsing circular beacons
    hotspots.forEach((hs) => {
      const isSelected = selectedHotspotId === hs.cluster_id;
      const el = document.createElement('div');
      el.className = 'group cursor-pointer relative';
      el.innerHTML = `
        <div class="relative flex items-center justify-center">
          <div class="absolute w-8 h-8 rounded-full bg-rose-500/50 animate-ping"></div>
          <div class="w-7 h-7 rounded-full bg-gradient-to-tr from-rose-600 to-red-500 border-2 ${
            isSelected ? 'border-white ring-4 ring-rose-400 scale-125' : 'border-white shadow-lg shadow-red-500/40'
          } flex items-center justify-center text-white text-xs font-bold transition-transform group-hover:scale-110">
            !
          </div>
        </div>
      `;

      el.addEventListener('click', (e) => {
        e.stopPropagation();
        if (onSelectHotspot) {
          onSelectHotspot(hs.cluster_id);
        }
      });

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([hs.centroid_longitude, hs.centroid_latitude])
        .addTo(map);

      // Popup on hover (Issue 4 - Fixed z-index & rendering logic in marker click/hover)
      const popup = new Popup({ offset: 15, closeButton: false }).setHTML(`
        <div class="text-xs p-1">
          <div class="font-bold text-rose-500 flex items-center gap-1">
            <span>Critical Hotspot</span>
          </div>
          <div class="mt-1 text-slate-700">
            Peak Risk: <span class="font-semibold text-rose-600">${(hs.max_risk_probability * 100).toFixed(1)}%</span>
          </div>
          <div class="text-[11px] text-slate-500">Affected Segments: ${hs.edge_ids.length}</div>
          <div class="text-[10px] text-indigo-500 mt-1 font-semibold">Click to view causative explanation</div>
        </div>
      `);

      el.addEventListener('mouseenter', () => marker.setPopup(popup).togglePopup());
      el.addEventListener('mouseleave', () => popup.remove());

      markersRef.current.push(marker);
    });

    // 2. Render Origin Waypoint Marker
    if (originWaypoint) {
      const oEl = document.createElement('div');
      oEl.className = 'w-7 h-7 rounded-full bg-blue-600 border-2 border-white text-white flex items-center justify-center shadow-lg font-bold text-xs';
      oEl.innerText = 'A';
      const oMarker = new maplibregl.Marker({ element: oEl })
        .setLngLat([originWaypoint.longitude, originWaypoint.latitude])
        .addTo(map);
      markersRef.current.push(oMarker);
    }

    // 3. Render Destination Waypoint Marker
    if (destinationWaypoint) {
      const dEl = document.createElement('div');
      dEl.className = 'w-7 h-7 rounded-full bg-emerald-600 border-2 border-white text-white flex items-center justify-center shadow-lg font-bold text-xs';
      dEl.innerText = 'B';
      const dMarker = new maplibregl.Marker({ element: dEl })
        .setLngLat([destinationWaypoint.longitude, destinationWaypoint.latitude])
        .addTo(map);
      markersRef.current.push(dMarker);
    }

    // 4. Update or Add GeoJSON Layers for Routes & Corridors
    // Primary Route
    const primaryGeo = parseWktLineString(primaryRouteWkt);
    const primarySource = map.getSource('primary-route-source') as maplibregl.GeoJSONSource;
    if (primarySource) {
      primarySource.setData({
        type: 'Feature',
        geometry: primaryGeo || { type: 'LineString', coordinates: [] },
        properties: {},
      });
    } else if (primaryGeo) {
      map.addSource('primary-route-source', {
        type: 'geojson',
        data: {
          type: 'Feature',
          geometry: primaryGeo,
          properties: {},
        },
      });
      map.addLayer({
        id: 'primary-route-layer',
        type: 'line',
        source: 'primary-route-source',
        layout: { 'line-join': 'round', 'line-cap': 'round' },
        paint: {
          'line-color': '#000000', // Black for original route to stand out
          'line-width': 6,
          'line-opacity': 0.85,
        },
      });
    }

    // Detour Route
    const detourGeo = parseWktLineString(detourRouteWkt);
    const detourSource = map.getSource('detour-route-source') as maplibregl.GeoJSONSource;
    if (detourSource) {
      detourSource.setData({
        type: 'Feature',
        geometry: detourGeo || { type: 'LineString', coordinates: [] },
        properties: {},
      });
    } else if (detourGeo) {
      map.addSource('detour-route-source', {
        type: 'geojson',
        data: {
          type: 'Feature',
          geometry: detourGeo,
          properties: {},
        },
      });
      map.addLayer({
        id: 'detour-route-layer',
        type: 'line',
        source: 'detour-route-source',
        layout: { 'line-join': 'round', 'line-cap': 'round' },
        paint: {
          'line-color': '#10B981', // Green for detour
          'line-width': 6,
          'line-dasharray': [2, 2],
          'line-opacity': 1.0,
        },
      });
    }

    // If route is rendered, fit bounds
    if (primaryGeo && primaryGeo.coordinates.length > 0) {
      const bounds = new maplibregl.LngLatBounds();
      primaryGeo.coordinates.forEach((c) => bounds.extend(c));
      if (detourGeo) {
        detourGeo.coordinates.forEach((c) => bounds.extend(c));
      }
      map.fitBounds(bounds, { padding: 80, maxZoom: 15, duration: 1000 });
    }
  }, [mapLoaded, predictions, hotspots, selectedHotspotId, originWaypoint, destinationWaypoint, primaryRouteWkt, detourRouteWkt]);

  return (
    <div className={`relative rounded-2xl overflow-hidden border border-slate-200 dark:border-slate-800 shadow-sm ${className}`}>
      {/* Map Target Canvas */}
      <div ref={mapContainerRef} className="w-full h-full" />

      {/* Picking Waypoint Mode Banner */}
      {isPickingWaypoint && (
        <div className="absolute top-4 left-4 right-4 z-10 px-4 py-3 rounded-xl bg-indigo-600/90 text-white backdrop-blur-md shadow-lg border border-indigo-500 text-sm flex items-center justify-center space-x-2 animate-bounce pointer-events-none">
          <Navigation className="w-5 h-5 text-white" />
          <span>Click anywhere on the map to set <b>{isPickingWaypoint.toUpperCase()}</b> coordinate</span>
        </div>
      )}

      {/* Map Legend Floating Card */}
      <div className="absolute bottom-4 right-4 z-10 p-3 rounded-xl bg-white/95 dark:bg-slate-900/95 backdrop-blur-md border border-slate-200 dark:border-slate-800 shadow-xl text-xs space-y-1.5 pointer-events-auto min-w-[160px]">
        <div className="font-semibold text-slate-800 dark:text-slate-200 flex items-center space-x-1.5 pb-2 mb-1 border-b border-slate-200 dark:border-slate-800">
          <Layers className="w-4 h-4 text-indigo-500" />
          <span>Risk Legend</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-3.5 h-3.5 rounded-full bg-rose-500 animate-pulse shadow-sm shadow-rose-500" />
          <span className="text-slate-600 dark:text-slate-300 font-medium">Danger Hotspot</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-3.5 h-1 rounded-full bg-[#EF4444]" />
          <span className="text-slate-600 dark:text-slate-300">Severe Risk (&ge;80%)</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-3.5 h-1 rounded-full bg-[#F97316]" />
          <span className="text-slate-600 dark:text-slate-300">High Risk (60-80%)</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-3.5 h-1 rounded-full bg-[#F59E0B]" />
          <span className="text-slate-600 dark:text-slate-300">Moderate (30-60%)</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-3.5 h-1 rounded-full bg-[#10B981]" />
          <span className="text-slate-600 dark:text-slate-300">Low Risk (0-30%)</span>
        </div>
      </div>
    </div>
  );
};
