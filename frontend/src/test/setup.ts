import '@testing-library/jest-dom';
import { beforeAll, afterEach, afterAll, vi } from 'vitest';
import { server } from './server';

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
});

// Mock ResizeObserver for Recharts
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock MapLibre GL for JSDOM
vi.mock('maplibre-gl', () => {
  class MockMap {
    on = vi.fn((event, cb) => {
      if (event === 'load') cb();
      return this;
    });
    addControl = vi.fn();
    remove = vi.fn();
    addSource = vi.fn();
    getSource = vi.fn(() => null);
    addLayer = vi.fn();
    fitBounds = vi.fn();
  }

  class MockMarker {
    setLngLat = vi.fn().mockReturnThis();
    addTo = vi.fn().mockReturnThis();
    remove = vi.fn();
    setPopup = vi.fn().mockReturnThis();
  }

  class MockPopup {
    setHTML = vi.fn().mockReturnThis();
    setLngLat = vi.fn().mockReturnThis();
    addTo = vi.fn().mockReturnThis();
    remove = vi.fn();
    togglePopup = vi.fn().mockReturnThis();
  }

  return {
    default: {
      Map: MockMap,
      Marker: MockMarker,
      Popup: MockPopup,
      NavigationControl: vi.fn(),
      ScaleControl: vi.fn(),
      LngLatBounds: class {
        extend = vi.fn();
      },
    },
    Map: MockMap,
    Marker: MockMarker,
    Popup: MockPopup,
    NavigationControl: vi.fn(),
    ScaleControl: vi.fn(),
    LngLatBounds: class {
      extend = vi.fn();
    },
  };
});

beforeAll(() => server.listen({ onUnhandledRequest: 'bypass' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
