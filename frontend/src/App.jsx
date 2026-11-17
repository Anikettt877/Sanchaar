import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import MainLayout from './layouts/MainLayout';

import OverviewDashboard from './pages/OverviewDashboard';
import DemandForecasting from './pages/DemandForecasting';
import PeakHourAnalytics from './pages/PeakHourAnalytics';
import StationAnalytics from './pages/StationAnalytics';
import WeekdayWeekendAnalysis from './pages/WeekdayWeekendAnalysis';
import TransportOptimization from './pages/TransportOptimization';
import ModelPerformance from './pages/ModelPerformance';
import DataManagement from './pages/DataManagement';
import Settings from './pages/Settings';

export default function App() {
  return (
    <ThemeProvider>
      <Routes>
        <Route element={<MainLayout />}>
          <Route index element={<OverviewDashboard />} />
          <Route path="forecasting" element={<DemandForecasting />} />
          <Route path="peak-hours" element={<PeakHourAnalytics />} />
          <Route path="stations" element={<StationAnalytics />} />
          <Route path="weekday-weekend" element={<WeekdayWeekendAnalysis />} />
          <Route path="optimization" element={<TransportOptimization />} />
          <Route path="model-performance" element={<ModelPerformance />} />
          <Route path="data" element={<DataManagement />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </ThemeProvider>
  );
}
