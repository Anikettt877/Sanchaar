import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  Calendar,
  Clock,
  Sparkles,
  Layers,
  ArrowRight,
  ShieldCheck,
  Zap,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts';

import PageHeader from '../components/common/PageHeader';
import StatCard from '../components/common/StatCard';
import Card from '../components/common/Card';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';
import Badge from '../components/common/Badge';

import { forecastDemand, getStationsList } from '../services/api';
import { formatNumber, formatHour, formatCompactNumber } from '../utils/formatters';

export default function DemandForecasting() {
  const [stations, setStations] = useState([]);
  const [selectedStation, setSelectedStation] = useState('229'); // 47-50 Sts Rockefeller Ctr
  const [selectedDate, setSelectedDate] = useState('2024-06-15');
  const [startHour, setStartHour] = useState(0);
  const [horizon, setHorizon] = useState(24);
  const [selectedModel, setSelectedModel] = useState('xgboost');

  const [loading, setLoading] = useState(false);
  const [forecastData, setForecastData] = useState(null);
  const [error, setError] = useState(null);

  // Load station list on mount
  useEffect(() => {
    async function loadStations() {
      try {
        const res = await getStationsList();
        if (res.data && res.data.length > 0) {
          setStations(res.data);
          setSelectedStation(String(res.data[0].id));
        }
      } catch (err) {
        console.error('Failed to load stations', err);
      }
    }
    loadStations();
  }, []);

  // Initial auto-forecast when stations load
  useEffect(() => {
    if (selectedStation) {
      handleForecast();
    }
  }, [selectedStation]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleForecast = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await forecastDemand(selectedStation, selectedDate, Number(startHour), Number(horizon), selectedModel);
      setForecastData(res.data);
    } catch (err) {
      setError(err.message || 'Forecasting failed');
    } finally {
      setLoading(false);
    }
  };

  const summary = forecastData?.summary || {};
  const forecasts = forecastData?.forecasts || [];

  return (
    <div className="space-y-8">
      <PageHeader
        title="Intelligent Passenger Demand Forecasting"
        subtitle="Generate future time-series passenger demand predictions using tuned ML (Random Forest, XGBoost) and Deep Learning (LSTM) models."
        badge="Multi-Model Prediction Engine"
      />

      {/* Control Panel Card */}
      <Card title="Forecast Horizon & Model Parameters">
        <form onSubmit={handleForecast} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 items-end">
          {/* Station Select */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
              Transit Hub / Station Complex
            </label>
            <select
              value={selectedStation}
              onChange={(e) => setSelectedStation(e.target.value)}
              className="w-full text-xs font-medium bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2.5 text-slate-900 dark:text-white focus:ring-2 focus:ring-brand-500 outline-none"
            >
              {stations.map((st) => (
                <option key={st.id} value={st.id}>
                  {st.name} ({st.borough})
                </option>
              ))}
            </select>
          </div>

          {/* Forecast Date */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
              Forecasting Target Date
            </label>
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="w-full text-xs font-medium bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-slate-900 dark:text-white focus:ring-2 focus:ring-brand-500 outline-none"
            />
          </div>

          {/* Time Horizon */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
              Forecast Horizon
            </label>
            <select
              value={horizon}
              onChange={(e) => setHorizon(Number(e.target.value))}
              className="w-full text-xs font-medium bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2.5 text-slate-900 dark:text-white focus:ring-2 focus:ring-brand-500 outline-none"
            >
              <option value={6}>6 Hours Window</option>
              <option value={12}>12 Hours Window</option>
              <option value={24}>24 Hours (Full Day)</option>
              <option value={48}>48 Hours (2 Days)</option>
            </select>
          </div>

          {/* ML Algorithm */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
              Prediction Algorithm
            </label>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="w-full text-xs font-medium bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2.5 text-slate-900 dark:text-white focus:ring-2 focus:ring-brand-500 outline-none"
            >
              <option value="xgboost">XGBoost Regressor (Recommended - R² 0.923)</option>
              <option value="random_forest">Random Forest Regressor (R² 0.918)</option>
              <option value="lstm">LSTM Neural Network (Deep Learning - R² 0.921)</option>
            </select>
          </div>

          {/* Submit Button */}
          <div>
            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center space-x-2 px-4 py-2.5 bg-brand-600 hover:bg-brand-700 text-white text-xs font-bold rounded-xl shadow-sm shadow-brand-500/20 transition-all disabled:opacity-50"
            >
              <Sparkles className="w-4 h-4" />
              <span>{loading ? 'Forecasting...' : 'Generate Forecast'}</span>
            </button>
          </div>
        </form>
      </Card>

      {error && <ErrorMessage message={error} onRetry={handleForecast} />}

      {loading && <LoadingSpinner message="Executing ML inference & generating sequence..." />}

      {/* Forecast Output */}
      {forecastData && !loading && (
        <div className="space-y-8">
          {/* Summary Stat Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              title="Average Hourly Demand"
              value={formatNumber(summary.average_ridership, 1)}
              subtitle="Projected passengers/hr"
              icon={TrendingUp}
              color="blue"
            />
            <StatCard
              title="Peak Hour Surge"
              value={formatNumber(summary.peak_ridership, 1)}
              subtitle={`At ${formatHour(summary.peak_hour)}`}
              icon={Zap}
              color="rose"
            />
            <StatCard
              title="Total Period Passengers"
              value={formatCompactNumber(summary.total_predicted_passengers)}
              subtitle={`Across ${forecastData.hours_ahead} hours`}
              icon={Layers}
              color="purple"
            />
            <StatCard
              title="Forecasted Demand Tier"
              value={summary.overall_demand_level}
              subtitle="Empirical Quartile Rating"
              icon={ShieldCheck}
              color="emerald"
            />
          </div>

          {/* Time-Series Forecast Line Chart */}
          <Card
            title={`${forecastData.station_name} — ${forecastData.hours_ahead}-Hour Passenger Demand Forecast`}
            subtitle={`Target Date: ${forecastData.start_date} | Model: ${forecastData.model_used.toUpperCase()}`}
          >
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={forecasts} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
                  <defs>
                    <linearGradient id="forecastGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#2563eb" stopOpacity={0.35} />
                      <stop offset="95%" stopColor="#2563eb" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" opacity={0.6} />
                  <XAxis
                    dataKey="formatted_time"
                    tick={{ fontSize: 11 }}
                    stroke="#94a3b8"
                  />
                  <YAxis
                    tickFormatter={(v) => formatCompactNumber(v)}
                    tick={{ fontSize: 11 }}
                    stroke="#94a3b8"
                  />
                  <Tooltip
                    formatter={(val) => [formatNumber(val, 1) + ' riders', 'Predicted Demand']}
                    labelFormatter={(t) => `Time: ${t}`}
                  />
                  <Area
                    type="monotone"
                    dataKey="predicted_ridership"
                    stroke="#2563eb"
                    strokeWidth={3}
                    fillOpacity={1}
                    fill="url(#forecastGrad)"
                    dot={{ r: 3, fill: '#2563eb' }}
                    activeDot={{ r: 6 }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Card>

          {/* Detailed Forecast Schedule Table */}
          <Card
            title="Hourly Forecasting Breakdown Table"
            subtitle="Granular hour-by-hour passenger estimates and demand categorization for transit dispatchers."
          >
            <div className="overflow-x-auto max-h-96 overflow-y-auto">
              <table className="w-full text-left text-xs">
                <thead className="sticky top-0 bg-slate-50 dark:bg-slate-800 uppercase font-semibold text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-700">
                  <tr>
                    <th className="px-4 py-3">Time Window</th>
                    <th className="px-4 py-3">Calendar Date</th>
                    <th className="px-4 py-3 text-right">Forecasted Ridership</th>
                    <th className="px-4 py-3 text-center">Demand Classification</th>
                    <th className="px-4 py-3 text-right">Suggested Vehicles (Cap=50)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {forecasts.map((row, idx) => {
                    const vehicles = Math.ceil(row.predicted_ridership / 50);
                    return (
                      <tr key={idx} className="hover:bg-slate-50/80 dark:hover:bg-slate-800/40">
                        <td className="px-4 py-3 font-semibold text-slate-800 dark:text-slate-200">
                          {row.formatted_time}
                        </td>
                        <td className="px-4 py-3 text-slate-500 dark:text-slate-400">
                          {row.date}
                        </td>
                        <td className="px-4 py-3 text-right font-bold text-slate-900 dark:text-white">
                          {formatNumber(row.predicted_ridership, 1)}
                        </td>
                        <td className="px-4 py-3 text-center">
                          <Badge level={row.demand_level} />
                        </td>
                        <td className="px-4 py-3 text-right font-medium text-brand-600 dark:text-brand-400">
                          {vehicles} vehicles
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
