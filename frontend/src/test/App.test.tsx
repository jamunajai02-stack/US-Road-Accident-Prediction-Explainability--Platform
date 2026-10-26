import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect } from 'vitest';
import App from '../App';

function renderWithClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>
  );
}

describe('SafeCorridor AI Web Application Views', () => {
  it('renders navbar and initial Risk Map view correctly', async () => {
    renderWithClient(<App />);

    expect(screen.getAllByText(/SafeCorridor AI/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/US Accident Predictor/i)).toBeInTheDocument();
    expect(screen.getByText(/Next 1-Hour Window/i)).toBeInTheDocument();
  });

  it('switches to Predictions Explorer and displays edge table', async () => {
    renderWithClient(<App />);

    const explorerTabs = screen.getAllByText(/Predictions Explorer/i);
    fireEvent.click(explorerTabs[0]);

    await waitFor(() => {
      expect(screen.getByText(/1-Hour Road Segment Risk Explorer/i)).toBeInTheDocument();
      expect(screen.getByText('1_2_1000')).toBeInTheDocument();
      expect(screen.getByText('88.4%')).toBeInTheDocument();
    });
  });

  it('switches to Route Safety Check view and evaluates trip', async () => {
    renderWithClient(<App />);

    const routeTabs = screen.getAllByText(/Route Safety Check/i);
    fireEvent.click(routeTabs[0]);

    await waitFor(() => {
      expect(screen.getByText(/Trip Safety & Hazard Avoidance Check/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Check Route Safety/i })).toBeInTheDocument();
    });
  });

  it('switches to Danger Hotspots view and renders active cluster cards', async () => {
    renderWithClient(<App />);

    const hotspotTabs = screen.getAllByText(/Danger Hotspots/i);
    fireEvent.click(hotspotTabs[0]);

    await waitFor(() => {
      expect(screen.getByText(/Danger Hotspots & Natural Language Explanations/i)).toBeInTheDocument();
      expect(screen.getByText('hotspot_cluster_1')).toBeInTheDocument();
    });
  });

  it('switches to System Trust view and renders calibration explanation', async () => {
    renderWithClient(<App />);

    const healthTabs = screen.getAllByText(/System Trust/i);
    fireEvent.click(healthTabs[0]);

    await waitFor(() => {
      expect(screen.getByText(/System Telemetry & Model Trust/i)).toBeInTheDocument();
      expect(screen.getByText(/How Predictions Are Calibrated/i)).toBeInTheDocument();
      expect(screen.getByText(/Charles Elkan’s Prior-Shift Log-Odds Theorem/i)).toBeInTheDocument();
    });
  });
});
