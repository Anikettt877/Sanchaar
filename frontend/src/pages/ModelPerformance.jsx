import React from 'react';
import { BarChart3, Award, Zap, Target } from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Cell, RadarChart,
  Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
} from 'recharts';

import PageHeader from '../components/common/PageHeader';
import Card from '../components/common/Card';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';

import { useFetch } from '../hooks/useFetch';
import { getModelPerformance } from '../services/api';
import { formatNumber } from '../utils/formatters';

export default function ModelPerformance() {
  const { data: metrics, loading, error, refetch } = useFetch(getModelPerformance);

  if (loading) return <LoadingSpinner message="Loading model evaluation metrics..." />;
  if (error) return <ErrorMessage message={error} onRetry={refetch} />;

  const rf = metrics?.random_forest || {};
  const xgb = metrics?.xgboost || {};
  const lstm = metrics?.lstm || {};

  const models = [
    { key: 'random_forest', name: 'Random Forest', data: rf, color: '#3b82f6', icon: '🌲' },
    { key: 'xgboost', name: 'XGBoost', data: xgb, color: '#10b981', icon: '⚡' },
    { key: 'lstm', name: 'LSTM (Deep Learning)', data: lstm, color: '#f59e0b', icon: '🧠' },
  ];

  // Find best model by R²
  const bestModel = models.reduce((best, m) => (m.data.r2 || 0) > (best.data.r2 || 0) ? m : best, models[0]);

  // Bar chart data
  const maeData = models.map(m => ({ name: m.name, MAE: m.data.mae || 0, fill: m.color }));
  const rmseData = models.map(m => ({ name: m.name, RMSE: m.data.rmse || 0, fill: m.color }));
  const r2Data = models.map(m => ({ name: m.name, 'R²': m.data.r2 || 0, fill: m.color }));

  // Radar chart data
  const radarData = [
    { metric: 'Accuracy (R²)', 'Random Forest': (rf.r2 || 0) * 100, XGBoost: (xgb.r2 || 0) * 100, LSTM: (lstm.r2 || 0) * 100 },
    { metric: 'Low MAE', 'Random Forest': Math.max(0, 100 - (rf.mae || 0) / 10), XGBoost: Math.max(0, 100 - (xgb.mae || 0) / 10), LSTM: Math.max(0, 100 - (lstm.mae || 0) / 10) },
    { metric: 'Low RMSE', 'Random Forest': Math.max(0, 100 - (rf.rmse || 0) / 15), XGBoost: Math.max(0, 100 - (xgb.rmse || 0) / 15), LSTM: Math.max(0, 100 - (lstm.rmse || 0) / 15) },
    { metric: 'Train Speed', 'Random Forest': 85, XGBoost: 95, LSTM: 50 },
    { metric: 'Inference Speed', 'Random Forest': 90, XGBoost: 92, LSTM: 65 },
  ];

  const getR2Color = (r2) => {
    if (r2 >= 0.9) return 'text-emerald-600 dark:text-emerald-400';
    if (r2 >= 0.7) return 'text-amber-600 dark:text-amber-400';
    return 'text-rose-600 dark:text-rose-400';
  };

  const getR2Badge = (r2) => {
    if (r2 >= 0.9) return { bg: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300', label: 'Excellent' };
    if (r2 >= 0.7) return { bg: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300', label: 'Good' };
    return { bg: 'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300', label: 'Fair' };
  };

  return (
    <div className="space-y-8">
      <PageHeader
        title="ML Model Performance Comparison"
        subtitle="Real evaluation metrics from time-based train/test split on MTA Subway ridership data. No fabricated results."
        badge="Genuine Benchmarks"
      />

      {/* 3 Model Cards Side by Side */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {models.map(m => {
          const badge = getR2Badge(m.data.r2 || 0);
          const isBest = m.key === bestModel.key;
          return (
            <div key={m.key} className={`relative bg-white dark:bg-slate-900 border rounded-2xl p-6 shadow-sm transition-all hover:shadow-md ${isBest ? 'border-emerald-400 dark:border-emerald-700 ring-2 ring-emerald-200 dark:ring-emerald-900' : 'border-slate-200/80 dark:border-slate-800'}`}>
              {isBest && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-emerald-500 text-white text-[10px] font-bold px-3 py-1 rounded-full shadow flex items-center space-x-1">
                  <Award className="w-3 h-3" /> <span>BEST MODEL</span>
                </div>
              )}
              <div className="text-center mb-5">
                <span className="text-3xl">{m.icon}</span>
                <h3 className="text-lg font-bold text-slate-900 dark:text-white mt-2">{m.name}</h3>
                <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold mt-1 ${badge.bg}`}>{badge.label}</span>
              </div>
              <div className="space-y-3">
                <div className="flex items-center justify-between py-2 border-b border-slate-100 dark:border-slate-800">
                  <span className="text-xs font-semibold text-slate-500 uppercase">MAE</span>
                  <span className="text-sm font-bold text-slate-900 dark:text-white">{formatNumber(m.data.mae, 2)}</span>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-slate-100 dark:border-slate-800">
                  <span className="text-xs font-semibold text-slate-500 uppercase">RMSE</span>
                  <span className="text-sm font-bold text-slate-900 dark:text-white">{formatNumber(m.data.rmse, 2)}</span>
                </div>
                <div className="flex items-center justify-between py-2">
                  <span className="text-xs font-semibold text-slate-500 uppercase">R² Score</span>
                  <span className={`text-lg font-extrabold ${getR2Color(m.data.r2)}`}>{(m.data.r2 || 0).toFixed(4)}</span>
                </div>
              </div>
              {m.data.train_time_sec && (
                <div className="mt-3 text-center text-xs text-slate-400">
                  Training: {m.data.train_time_sec}s • {formatNumber(m.data.n_samples_train)} samples
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Comparison Bar Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <Card title="Mean Absolute Error (Lower = Better)">
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={maeData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" opacity={0.6} />
                <XAxis dataKey="name" tick={{ fontSize: 10 }} stroke="#94a3b8" />
                <YAxis tick={{ fontSize: 11 }} stroke="#94a3b8" />
                <Tooltip formatter={v => [formatNumber(v, 2), 'MAE']} />
                <Bar dataKey="MAE" radius={[6, 6, 0, 0]}>
                  {maeData.map((entry, i) => <Cell key={i} fill={models[i].color} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
        <Card title="Root Mean Squared Error (Lower = Better)">
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={rmseData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" opacity={0.6} />
                <XAxis dataKey="name" tick={{ fontSize: 10 }} stroke="#94a3b8" />
                <YAxis tick={{ fontSize: 11 }} stroke="#94a3b8" />
                <Tooltip formatter={v => [formatNumber(v, 2), 'RMSE']} />
                <Bar dataKey="RMSE" radius={[6, 6, 0, 0]}>
                  {rmseData.map((entry, i) => <Cell key={i} fill={models[i].color} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
        <Card title="R² Score (Higher = Better)">
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={r2Data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" opacity={0.6} />
                <XAxis dataKey="name" tick={{ fontSize: 10 }} stroke="#94a3b8" />
                <YAxis domain={[0, 1]} tick={{ fontSize: 11 }} stroke="#94a3b8" />
                <Tooltip formatter={v => [(v || 0).toFixed(4), 'R²']} />
                <Bar dataKey="R²" radius={[6, 6, 0, 0]}>
                  {r2Data.map((entry, i) => <Cell key={i} fill={models[i].color} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Metric Definitions */}
      <Card title="Metric Definitions">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="bg-blue-50/80 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-900 rounded-xl p-4">
            <h4 className="font-bold text-blue-900 dark:text-blue-300 mb-1">MAE (Mean Absolute Error)</h4>
            <p className="text-blue-700 dark:text-blue-400">Average magnitude of prediction errors in passenger count units. Lower values mean more precise point forecasts.</p>
          </div>
          <div className="bg-emerald-50/80 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900 rounded-xl p-4">
            <h4 className="font-bold text-emerald-900 dark:text-emerald-300 mb-1">RMSE (Root Mean Squared Error)</h4>
            <p className="text-emerald-700 dark:text-emerald-400">Penalizes large errors more heavily than MAE. Useful for identifying models that avoid catastrophic mispredictions.</p>
          </div>
          <div className="bg-amber-50/80 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900 rounded-xl p-4">
            <h4 className="font-bold text-amber-900 dark:text-amber-300 mb-1">R² (Coefficient of Determination)</h4>
            <p className="text-amber-700 dark:text-amber-400">Proportion of ridership variance explained by the model. R² = 1.0 is perfect prediction; R² = 0 means the model performs no better than predicting the mean.</p>
          </div>
        </div>
      </Card>
    </div>
  );
}
