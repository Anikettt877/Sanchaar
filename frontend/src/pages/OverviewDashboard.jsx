import React from 'react';
import {
  Users,
  Building2,
  TrendingUp,
  Clock,
  Compass,
  Zap,
  Calendar,
  Activity,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

import PageHeader from '../components/common/PageHeader';
import StatCard from '../components/common/StatCard';
import Card from '../components/common/Card';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';
import Badge from '../components/common/Badge';

import { useFetch } from '../hooks/useFetch';
import {
  getDashboardSummary,
  getMonthlyAnalytics,
  getHourlyAnalytics,
  getWeeklyAnalytics,
  getStationRankings,
  getRecentActivity,
} from '../services/api';
import { formatNumber, formatCompactNumber, formatHour } from '../utils/formatters';

export default function OverviewDashboard() {
  const { data: summary, loading: summaryLoading, error: summaryError, refetch: refetchSummary } = useFetch(getDashboardSummary);
  const { data: monthlyData, loading: monthlyLoading } = useFetch(getMonthlyAnalytics);
  const { data: hourlyData, loading: hourlyLoading } = useFetch(getHourlyAnalytics);
  const { data: weeklyData, loading: weeklyLoading } = useFetch(getWeeklyAnalytics);
  const { data: stationRankings, loading: stationsLoading } = useFetch(() => getStationRankings(5));
  const { data: recentActivity } = useFetch(getRecentActivity);

  if (summaryLoading) return <LoadingSpinner message="Loading transit analytics dashboard..." />;
  if (summaryError) return <ErrorMessage message={summaryError} onRetry={refetchSummary} />;

  const busiestStation = summary?.busiest_station || {};
  const topStations = stationRankings?.top_stations || [];

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <PageHeader
        title="Transit Intelligence Overview"
        subtitle="Real-time ridership patterns, empirical peak detection, and AI capacity planning from MTA Subway operations."
        badge="NYC Subway Ingestion"
      />

      {/* 6 Top Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <StatCard
          title="Total Processed Rows"
          value={formatNumber(summary?.total_records)}
          subtitle="Jan - Jun 2024 Records"
          icon={DatabaseIcon}
          color="blue"
        />
        <StatCard
          title="Active Transit Hubs"
          value={summary?.total_stations || 13}
          subtitle={`Across ${summary?.total_boroughs || 3} NYC Boroughs`}
          icon={Building2}
          color="indigo"
        />
        <StatCard
          title="Avg Hourly Entries"
          value={formatNumber(summary?.avg_hourly_ridership)}
          subtitle="Per Station Complex"
          icon={Users}
          color="emerald"
        />
        <StatCard
          title="Peak Travel Hour"
          value={formatHour(summary?.peak_hour || 19)}
          subtitle="Evening Rush Peak"
          icon={Clock}
          color="amber"
        />
        <StatCard
          title="Busiest Complex"
          value={busiestStation.name ? busiestStation.name.split('(')[0] : 'Rockefeller Ctr'}
          subtitle={`${formatCompactNumber(busiestStation.total_ridership)} total riders`}
          icon={Compass}
          color="purple"
        />
        <StatCard
          title="System Boardings"
          value={formatCompactNumber(summary?.total_ridership)}
          subtitle="Cumulative Volume"
          icon={Zap}
          color="rose"
        />
      </div>

      {/* Primary Analytics Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Monthly Trend Area Chart */}
        <Card
          title="2024 Monthly Transit Volume Trend"
          subtitle="Cumulative subway boarding trajectory across the H1 2024 operating window."
        >
          {monthlyLoading ? (
            <LoadingSpinner message="Loading monthly aggregates..." />
          ) : (
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={monthlyData || []} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="monthlyGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" opacity={0.6} />
                  <XAxis dataKey="month_name" tick={{ fontSize: 12 }} stroke="#94a3b8" />
                  <YAxis
                    tickFormatter={(v) => formatCompactNumber(v)}
                    tick={{ fontSize: 12 }}
                    stroke="#94a3b8"
                  />
                  <Tooltip
                    formatter={(val) => [formatNumber(val) + ' riders', 'Monthly Volume']}
                    labelFormatter={(label) => `Month: ${label}`}
                  />
                  <Area
                    type="monotone"
                    dataKey="total_ridership"
                    stroke="#2563eb"
                    strokeWidth={2.5}
                    fillOpacity={1}
                    fill="url(#monthlyGradient)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}
        </Card>

        {/* 24-Hour Passenger Distribution */}
        <Card
          title="System-Wide 24-Hour Passenger Curve"
          subtitle="Empirical hourly boarding distribution highlighting morning (8-9 AM) and evening (5-7 PM) rush hours."
        >
          {hourlyLoading ? (
            <LoadingSpinner message="Loading hourly curves..." />
          ) : (
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={hourlyData || []} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" opacity={0.6} />
                  <XAxis dataKey="hour" tickFormatter={(h) => `${h}h`} tick={{ fontSize: 11 }} stroke="#94a3b8" />
                  <YAxis tickFormatter={(v) => formatCompactNumber(v)} tick={{ fontSize: 11 }} stroke="#94a3b8" />
                  <Tooltip
                    formatter={(val) => [formatNumber(val) + ' riders', 'Avg Entries']}
                    labelFormatter={(h) => formatHour(h)}
                  />
                  <Bar dataKey="avg_ridership" radius={[4, 4, 0, 0]}>
                    {(hourlyData || []).map((entry) => {
                      const isPeak = (entry.hour >= 7 && entry.hour <= 9) || (entry.hour >= 17 && entry.hour <= 19);
                      return <Cell key={`cell-${entry.hour}`} fill={isPeak ? '#ef4444' : '#3b82f6'} />;
                    })}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </Card>
      </div>

      {/* Secondary Row: Day of Week & Top Stations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Weekly Day Distribution */}
        <Card
          title="Weekly Passenger Volume Distribution"
          subtitle="Weekday commuter demand compared against weekend leisure traffic."
        >
          {weeklyLoading ? (
            <LoadingSpinner message="Loading day distribution..." />
          ) : (
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={weeklyData || []} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" opacity={0.6} />
                  <XAxis dataKey="day_name" tick={{ fontSize: 11 }} stroke="#94a3b8" />
                  <YAxis tickFormatter={(v) => formatCompactNumber(v)} tick={{ fontSize: 11 }} stroke="#94a3b8" />
                  <Tooltip formatter={(val) => [formatNumber(val) + ' riders', 'Daily Average']} />
                  <Bar dataKey="avg_ridership" fill="#6366f1" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </Card>

        {/* Top 5 Busiest Transit Hubs */}
        <Card
          title="Top 5 High-Demand Transit Complexes"
          subtitle="Highest cumulative passenger demand stations requiring maximum fleet provision."
        >
          {stationsLoading ? (
            <LoadingSpinner message="Loading station rankings..." />
          ) : (
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={topStations}
                  layout="vertical"
                  margin={{ top: 5, right: 20, left: 80, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" opacity={0.6} />
                  <XAxis type="number" tickFormatter={(v) => formatCompactNumber(v)} tick={{ fontSize: 11 }} stroke="#94a3b8" />
                  <YAxis
                    type="category"
                    dataKey="name"
                    tickFormatter={(name) => (name.length > 14 ? name.substring(0, 14) + '...' : name)}
                    tick={{ fontSize: 11 }}
                    stroke="#94a3b8"
                  />
                  <Tooltip formatter={(val) => [formatNumber(val) + ' riders', 'Cumulative Demand']} />
                  <Bar dataKey="total_ridership" fill="#059669" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </Card>
      </div>

      {/* Recent Forecasting Activity Audit Log */}
      <Card
        title="Live Model Inference Audit Log"
        subtitle="Recent predictions recorded across Random Forest, XGBoost, and LSTM inference engines."
      >
        {recentActivity && recentActivity.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-slate-800/60 uppercase font-semibold text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
                <tr>
                  <th className="px-4 py-3">Station</th>
                  <th className="px-4 py-3">Target Time</th>
                  <th className="px-4 py-3">Model</th>
                  <th className="px-4 py-3 text-right">Predicted Demand</th>
                  <th className="px-4 py-3 text-center">Classification</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80">
                {recentActivity.map((act) => (
                  <tr key={act.id} className="hover:bg-slate-50/80 dark:hover:bg-slate-800/40 transition-colors">
                    <td className="px-4 py-3 font-medium text-slate-900 dark:text-slate-100">
                      {act.station_name || `Station ${act.station_id}`}
                    </td>
                    <td className="px-4 py-3 text-slate-500 dark:text-slate-400">
                      {act.target_datetime?.replace('T', ' ')}
                    </td>
                    <td className="px-4 py-3 capitalize font-semibold text-brand-600 dark:text-brand-400">
                      {act.model_used}
                    </td>
                    <td className="px-4 py-3 text-right font-bold text-slate-900 dark:text-white">
                      {formatNumber(act.predicted_ridership, 1)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <Badge level={act.demand_level} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-slate-400 text-xs">
            No live predictions generated yet. Navigate to <span className="font-semibold text-brand-500">Demand Forecasting</span> to generate predictions.
          </div>
        )}
      </Card>
    </div>
  );
}

function DatabaseIcon(props) {
  return <TrendingUp {...props} />;
}
