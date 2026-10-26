/**
 * Utility to parse WKT (Well-Known Text) geometries into GeoJSON coordinates.
 */

export interface GeoJsonLineString {
  type: 'LineString';
  coordinates: [number, number][]; // [longitude, latitude]
}

export function parseWktLineString(wkt: string | null | undefined): GeoJsonLineString | null {
  if (!wkt || typeof wkt !== 'string') return null;

  const match = wkt.match(/LINESTRING\s*\(([^)]+)\)/i);
  if (!match || !match[1]) return null;

  const coordPairs = match[1].split(',').map((pair) => pair.trim());
  const coordinates: [number, number][] = [];

  for (const pair of coordPairs) {
    const parts = pair.split(/\s+/).map(Number);
    if (parts.length >= 2 && !isNaN(parts[0]) && !isNaN(parts[1])) {
      coordinates.push([parts[0], parts[1]]);
    }
  }

  if (coordinates.length === 0) return null;

  return {
    type: 'LineString',
    coordinates,
  };
}

export function computeBoundingBox(coordinates: [number, number][]): [[number, number], [number, number]] | null {
  if (!coordinates || coordinates.length === 0) return null;

  let minLng = Infinity;
  let maxLng = -Infinity;
  let minLat = Infinity;
  let maxLat = -Infinity;

  for (const [lng, lat] of coordinates) {
    if (lng < minLng) minLng = lng;
    if (lng > maxLng) maxLng = lng;
    if (lat < minLat) minLat = lat;
    if (lat > maxLat) maxLat = lat;
  }

  return [
    [minLng, minLat],
    [maxLng, maxLat],
  ];
}

export function createFallbackLineString(
  origin: { latitude: number; longitude: number },
  destination: { latitude: number; longitude: number }
): GeoJsonLineString {
  return {
    type: 'LineString',
    coordinates: [
      [origin.longitude, origin.latitude],
      [destination.longitude, destination.latitude],
    ],
  };
}
