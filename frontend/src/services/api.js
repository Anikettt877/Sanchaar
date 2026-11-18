/**
 * Central API Client Service for Sanchaar Backend.
 */

import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Response unwrap interceptor
api.interceptors.response.use(
  response => response.data,
  error => {
    const message = error.response?.data?.error || error.message || 'API request failed';
    return Promise.reject(new Error(message));
  }
);

// -------------------------------------------------------------
// DASHBOARD & ANALYTICS
// -------------------------------------------------------------
export const getDashboardSummary = () => api.get('/dashboard/summary');
export const getDashboardTrends = () => api.get('/dashboard/trends');
export const getRecentActivity = () => api.get('/dashboard/recent-activity');

export const getHourlyAnalytics = () => api.get('/analytics/hourly');
export const getWeeklyAnalytics = () => api.get('/analytics/weekly');
export const getMonthlyAnalytics = () => api.get('/analytics/monthly');
export const getStationRankings = (topN = 10) => api.get(`/analytics/stations?top_n=${topN}`);
export const getStationDetails = (stationId) => api.get(`/analytics/stations/${stationId}`);
export const getBoroughStats = () => api.get('/analytics/boroughs');
export const getPeakAnalysis = () => api.get('/analytics/peak');
export const getWeekdayWeekendComparison = () => api.get('/analytics/weekday-weekend');
export const getHeatmapData = () => api.get('/analytics/heatmap');
export const getRouteAnalytics = () => api.get('/analytics/routes');

// -------------------------------------------------------------
// PREDICTION & FORECASTING
// -------------------------------------------------------------
export const predictDemand = (stationId, date, hour, model = 'xgboost') => 
  api.post('/predict', { station_id: stationId, date, hour, model });

export const forecastDemand = (stationId, startDate, startHour = 0, hours = 24, model = 'xgboost') => 
  api.post('/forecast', { station_id: stationId, start_date: startDate, start_hour: startHour, hours, model });

export const getModelPerformance = () => api.get('/models/performance');
export const getDailyForecast = (stationId, startDate, days = 7, model = 'xgboost') =>
  api.post('/forecast/daily', { station_id: stationId, start_date: startDate, days, model });
export const getPeakForecast = (stationId, date, model = 'xgboost') =>
  api.post('/forecast/peaks', { station_id: stationId, date, model });

// -------------------------------------------------------------
// TRANSPORT OPTIMIZATION
// -------------------------------------------------------------
export const getOptimizationRecommendation = (stationId, date, vehicleCapacity = 50) =>
  api.post('/optimization/recommend', { station_id: stationId, date, vehicle_capacity: vehicleCapacity });

export const allocateFleet = (stationPredictions, totalVehicles = 100, vehicleCapacity = 50) =>
  api.post('/optimization/allocate', { station_predictions: stationPredictions, total_vehicles: totalVehicles, vehicle_capacity: vehicleCapacity });

export const compareCapacityScenarios = (hourlyDemand, capacities = [30, 50, 80, 120]) =>
  api.post('/optimization/scenarios', { hourly_demand: hourlyDemand, capacities });

// -------------------------------------------------------------
// DATA MANAGEMENT
// -------------------------------------------------------------
export const getDatasetInfo = () => api.get('/datasets');
export const getDatasetPreview = (limit = 50) => api.get(`/datasets/preview?limit=${limit}`);
export const getStationsList = () => api.get('/datasets/stations');

export default api;
