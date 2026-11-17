import React, { useState, useEffect } from 'react';
import { Truck, AlertTriangle, CheckCircle2, Gauge, ArrowRight, Sparkles } from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';

import PageHeader from '../components/common/PageHeader';
import StatCard from '../components/common/StatCard';
import Card from '../components/common/Card';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';
import Badge from '../components/common/Badge';

import { getOptimizationRecommendation, getStationsList } from '../services/api';
import { formatNumber, formatHour, formatCompactNumber } from '../utils/formatters';

export default function TransportOptimization() {
  const [stations, setStations] = useState([]);
  const [selectedStation, setSelectedStation] = useState('229');
  const [selectedDate, setSelectedDate] = useState('2024-06-15');
  const [vehicleCapacity, setVehicleCapacity] = useState(50);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadStations() {
      try {
        const res = await getStationsList();
        if (res.data?.length > 0) {
          setStations(res.data);
          setSelectedStation(String(res.data[0].id));
        }
      } catch (err) { console.error(err); }
    }
    loadStations();
  }, []);

  const handleAnalyze = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await getOptimizationRecommendation(selectedStation, selectedDate, Number(vehicleCapacity));
      setData(res.data);
    } catch (err) {
      setError(err.message || 'Optimization analysis failed');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedStation) handleAnalyze();
  }, [selectedStation]); // eslint-disable-line

  const summary = data?.summary || {};
  const schedule = data?.hourly_schedule || [];
  const recommendations = data?.recommendations || [];

  return (
    <div className="space-y-8">
      <PageHeader
        title="Transport Capacity Optimization"
        subtitle="AI-driven fleet sizing, vehicle allocation, and hourly capacity planning based on demand forecasts."
        badge="Planning Estimates"
      />

      {/* Input Controls */}
      <Card title="Optimization Parameters">
        <form onSubmit={handleAnalyze} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 items-end">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">Station Complex</label>
            <select value={selectedStation} onChange={e => setSelectedStation(e.target.value)}
              className="w-full text-xs font-medium bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2.5 text-slate-900 dark:text-white focus:ring-2 focus:ring-brand-500 outline-none">
              {stations.map(st => <option key={st.id} value={st.id}>{st.name} ({st.borough})</option>)}
            </select>
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">Target Date</label>
            <input type="date" value={selectedDate} onChange={e => setSelectedDate(e.target.value)}
              className="w-full text-xs font-medium bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-slate-900 dark:text-white focus:ring-2 focus:ring-brand-500 outline-none" />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">Vehicle Capacity (passengers)</label>
            <input type="number" min="10" max="500" value={vehicleCapacity} onChange={e => setVehicleCapacity(e.target.value)}
              className="w-full text-xs font-medium bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-3 py-2 text-slate-900 dark:text-white focus:ring-2 focus:ring-brand-500 outline-none" />
          </div>
          <button type="submit" disabled={loading}
            className="flex items-center justify-center space-x-2 px-4 py-2.5 bg-brand-600 hover:bg-brand-700 text-white text-xs font-bold rounded-xl shadow-sm transition-all disabled:opacity-50">
            <Sparkles className="w-4 h-4" />
            <span>{loading ? 'Analyzing...' : 'Run Capacity Analysis'}</span>
          </button>
        </form>
      </Card>

      {error && <ErrorMessage message={error} onRetry={handleAnalyze} />}
      {loading && <LoadingSpinner message="Computing optimal vehicle allocation..." />}

      {data && !loading && (
        <div className="space-y-8">
          {/* Summary Stats */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard title="Average Hourly Demand" value={formatNumber(summary.average_demand)} subtitle="Passengers/hour" icon={Gauge} color="blue" />
            <StatCard title="Peak Hour Demand" value={formatNumber(summary.peak_demand)} subtitle={`At ${formatHour(summary.peak_hour)}`} icon={AlertTriangle} color="rose" />
            <StatCard title="Max Vehicles Needed" value={summary.max_vehicles_required} subtitle={`Vehicle capacity: ${vehicleCapacity}`} icon={Truck} color="purple" />
            <StatCard title="Min Vehicles Needed" value={summary.min_vehicles_required} subtitle="Off-peak low" icon={CheckCircle2} color="emerald" />
          </div>

          {/* 24-Hour Vehicle Allocation Bar Chart */}
          <Card title="24-Hour Fleet Deployment Schedule" subtitle="Hourly vehicle units required based on demand prediction. Red bars indicate peak surge requirements.">
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={schedule} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" opacity={0.6} />
                  <XAxis dataKey="hour" tickFormatter={h => `${h}h`} tick={{ fontSize: 11 }} stroke="#94a3b8" />
                  <YAxis tick={{ fontSize: 11 }} stroke="#94a3b8" label={{ value: 'Vehicles', angle: -90, position: 'insideLeft', style: { fontSize: 11 } }} />
                  <Tooltip formatter={(v, name) => {
                    if (name === 'vehicles_required') return [v + ' vehicles', 'Required'];
                    return [formatNumber(v), name];
                  }} labelFormatter={h => formatHour(h)} />
                  <Bar dataKey="vehicles_required" radius={[4, 4, 0, 0]}>
                    {schedule.map((entry) => {
                      const utilPct = entry.utilization_pct || 0;
                      let fill = '#3b82f6';
                      if (utilPct > 90) fill = '#ef4444';
                      else if (utilPct > 75) fill = '#f59e0b';
                      else if (utilPct < 40) fill = '#10b981';
                      return <Cell key={`cell-${entry.hour}`} fill={fill} />;
                    })}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          {/* Recommendations */}
          <Card title="Strategic Fleet Recommendations" subtitle="AI-generated operational guidance based on demand analysis.">
            <div className="space-y-4">
              {recommendations.map((rec, idx) => {
                const priorityColors = {
                  High: 'border-l-rose-500 bg-rose-50/50 dark:bg-rose-950/20',
                  Medium: 'border-l-amber-500 bg-amber-50/50 dark:bg-amber-950/20',
                  Low: 'border-l-emerald-500 bg-emerald-50/50 dark:bg-emerald-950/20',
                };
                return (
                  <div key={idx} className={`border-l-4 rounded-xl p-4 ${priorityColors[rec.priority] || priorityColors.Low}`}>
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-sm font-bold text-slate-900 dark:text-white">{rec.category}</h4>
                      <Badge level={rec.priority === 'High' ? 'very high' : rec.priority === 'Medium' ? 'high' : 'low'} text={`${rec.priority} Priority`} />
                    </div>
                    <p className="text-xs text-slate-700 dark:text-slate-300 mb-1"><strong>Time:</strong> {rec.time_window}</p>
                    <p className="text-xs text-slate-600 dark:text-slate-400">{rec.recommendation}</p>
                    {rec.suggested_action && (
                      <p className="text-xs text-brand-600 dark:text-brand-400 mt-2 font-medium">
                        <ArrowRight className="w-3 h-3 inline mr-1" />
                        {rec.suggested_action}
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          </Card>

          {/* Planning Disclaimer */}
          <div className="bg-amber-50/60 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900 rounded-xl p-4 text-xs text-amber-800 dark:text-amber-300">
            <strong>⚠ Planning Disclaimer:</strong> {data?.planning_disclaimer || 'These outputs are computational planning estimates based on ML demand predictions and are not real-time dispatch instructions.'}
          </div>
        </div>
      )}
    </div>
  );
}
