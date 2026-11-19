import React from 'react';
import {
  Sun,
  Moon,
  Clock,
  Flame,
  PieChart as PieIcon,
  Activity,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';

import PageHeader from '../components/common/PageHeader';
import StatCard from '../components/common/StatCard';
import Card from '../components/common/Card';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';
import Badge from '../components/common/Badge';

import { useFetch } from '../hooks/useFetch';
import { getPeakAnalysis, getHeatmapData } from '../services/api';
import { formatNumber, formatHour, formatCompactNumber } from '../utils/formatters';

export default function PeakHourAnalytics() {
  const { data: peakData, loading: peakLoading, error: peakError, refetch } = useFetch(getPeakAnalysis);
  const { data: heatmapData, loading: heatmapLoading } = useFetch(getHeatmapData);

  if (peakLoading) return <LoadingSpinner message="Calculating peak window metrics..." />;
  if (peakError) return <ErrorMessage message={peakError} onRetry={refetch} />;

  const morningPeak = peakData?.morning_peak || {};
  const eveningPeak = peakData?.evening_peak || {};
  const offPeak = peakData?.off_peak || {};
  const hourlyData = peakData?.hourly_data || [];

  // Data for Peak vs Off-Peak Pie Chart
  const pieData = [
    { name: 'Morning Peak (7-10 AM)', value: Math.round(morningPeak.avg_ridership * 3), color: '#f59e0b' },
    { name: 'Evening Peak (4-7 PM)', value: Math.round(eveningPeak.avg_ridership * 3), color: '#ef4444' },
    { name: 'Off-Peak Hours (18 hrs)', value: Math.round(offPeak.avg_ridership * 18), color: '#3b82f6' },
  ];

  // Days and hours for Heatmap
  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  const hours = Array.from({ length: 24 }, (_, i) => i);

  // Build a lookup: day name → { hour → avg_ridership }
  // Backend returns matrix as a 2D list [dayIndex][hourIndex] and days as an ordered list
  const heatmapLookup = (() => {
    const hm = heatmapData;
    if (!hm || !hm.matrix) return {};
    const lookup = {};
    let globalMax = 0;
    const dayNames = hm.days || days;
    const matrixArr = hm.matrix; // list of 7 arrays, each of length 24
    dayNames.forEach((dayName, dIdx) => {
      lookup[dayName] = {};
      const row = matrixArr[dIdx] || [];
      row.forEach((val, hIdx) => {
        const v = Number(val) || 0;
        lookup[dayName][hIdx] = v;
        if (v > globalMax) globalMax = v;
      });
    });
    return { lookup, maxValue: globalMax || 4000 };
  })();

  // Helper for heatmap cell color
  const getHeatmapColor = (hour, day) => {
    if (!heatmapLookup.lookup) return 'bg-slate-100 dark:bg-slate-800';
    const val = heatmapLookup.lookup[day]?.[hour] || 0;

    // Scale against max
    const maxVal = heatmapLookup.maxValue;
    const ratio = Math.min(1.0, val / maxVal);

    if (ratio > 0.8) return 'bg-rose-600 text-white';
    if (ratio > 0.6) return 'bg-rose-500 text-white';
    if (ratio > 0.45) return 'bg-amber-500 text-white';
    if (ratio > 0.3) return 'bg-amber-400 text-slate-900';
    if (ratio > 0.15) return 'bg-blue-400 text-slate-900';
    if (ratio > 0.05) return 'bg-blue-200 text-slate-800 dark:bg-blue-900/60 dark:text-blue-200';
    return 'bg-slate-100 text-slate-400 dark:bg-slate-800/40 dark:text-slate-500';
  };

  const getHeatmapValue = (hour, day) => {
    if (!heatmapLookup.lookup) return 0;
    return heatmapLookup.lookup[day]?.[hour] || 0;
  };

  return (
    <div className="space-y-8">
      <PageHeader
        title="Peak Hour & Heatmap Analytics"
        subtitle="Identify critical overcrowding windows, morning vs evening commute surges, and low-traffic maintenance intervals."
        badge="Temporal Load Profiling"
      />

      {/* 4 Peak Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Morning Peak Avg"
          value={formatNumber(morningPeak.avg_ridership)}
          subtitle="07:00 AM – 10:00 AM"
          icon={Sun}
          color="amber"
        />
        <StatCard
          title="Evening Peak Avg"
          value={formatNumber(eveningPeak.avg_ridership)}
          subtitle="04:00 PM – 07:00 PM"
          icon={Flame}
          color="rose"
        />
        <StatCard
          title="Off-Peak Average"
          value={formatNumber(offPeak.avg_ridership)}
          subtitle="Rest of operating day"
          icon={Clock}
          color="blue"
        />
        <StatCard
          title="Lowest Demand Hour"
          value={formatHour(peakData?.lowest_demand_hour || 3)}
          subtitle="Depot Maintenance Window"
          icon={Moon}
          color="purple"
        />
      </div>

      {/* Primary Peak Distribution Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Hourly Distribution Bar Chart (2 cols) */}
        <div className="lg:col-span-2">
          <Card
            title="Hourly Passenger Load & Overcrowding Risk"
            subtitle="Red bars represent morning and evening peak intervals requiring maximum vehicle headway."
          >
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={hourlyData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" opacity={0.6} />
                  <XAxis dataKey="hour" tickFormatter={(h) => `${h}h`} tick={{ fontSize: 11 }} stroke="#94a3b8" />
                  <YAxis tickFormatter={(v) => formatCompactNumber(v)} tick={{ fontSize: 11 }} stroke="#94a3b8" />
                  <Tooltip
                    formatter={(val) => [formatNumber(val) + ' riders/hr', 'Average Volume']}
                    labelFormatter={(h) => formatHour(h)}
                  />
                  <Bar dataKey="avg_ridership" radius={[4, 4, 0, 0]}>
                    {hourlyData.map((entry) => {
                      const isMorning = entry.hour >= 7 && entry.hour <= 9;
                      const isEvening = entry.hour >= 16 && entry.hour <= 19;
                      let fill = '#3b82f6';
                      if (isMorning) fill = '#f59e0b';
                      if (isEvening) fill = '#ef4444';
                      return <Cell key={`cell-${entry.hour}`} fill={fill} />;
                    })}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="flex items-center justify-center space-x-6 mt-4 text-xs font-medium text-slate-500">
              <span className="flex items-center space-x-1.5">
                <span className="w-3 h-3 rounded-full bg-amber-500"></span>
                <span>Morning Peak (7-9 AM)</span>
              </span>
              <span className="flex items-center space-x-1.5">
                <span className="w-3 h-3 rounded-full bg-rose-500"></span>
                <span>Evening Peak (4-7 PM)</span>
              </span>
              <span className="flex items-center space-x-1.5">
                <span className="w-3 h-3 rounded-full bg-blue-500"></span>
                <span>Off-Peak Normal</span>
              </span>
            </div>
          </Card>
        </div>

        {/* Peak vs Off-Peak Share (1 col) */}
        <div>
          <Card
            title="System Passenger Share"
            subtitle="Proportion of daily boardings occurring during surge intervals."
          >
            <div className="h-72 w-full flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="45%"
                    innerRadius={55}
                    outerRadius={85}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v) => formatCompactNumber(v) + ' passengers'} />
                  <Legend verticalAlign="bottom" wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </div>
      </div>

      {/* 24x7 Demand Heatmap Matrix */}
      <Card
        title="Weekly Passenger Demand Heatmap (Hour of Day × Day of Week)"
        subtitle="Empirical ridership intensity matrix. Darker red cells indicate acute congestion periods requiring surge fleet deployment."
      >
        {heatmapLoading ? (
          <LoadingSpinner message="Building hourly congestion matrix..." />
        ) : (
          <div className="overflow-x-auto pb-2">
            <div className="min-w-[700px]">
              {/* Hours Header */}
              <div className="grid grid-cols-25 gap-1 mb-1 text-[10px] text-center font-semibold text-slate-400">
                <div className="text-left pl-2">Day</div>
                {hours.map((h) => (
                  <div key={h} className="truncate">
                    {h}
                  </div>
                ))}
              </div>

              {/* Rows per Day */}
              {days.map((day) => (
                <div key={day} className="grid grid-cols-25 gap-1 mb-1.5 items-center">
                  <div className="text-xs font-semibold text-slate-700 dark:text-slate-300 truncate pl-2">
                    {day.substring(0, 3)}
                  </div>
                  {hours.map((h) => {
                    const val = getHeatmapValue(h, day);
                    const colorCls = getHeatmapColor(h, day);
                    return (
                      <div
                        key={h}
                        title={`${day} at ${formatHour(h)}: ${formatNumber(val)} riders`}
                        className={`h-7 rounded flex items-center justify-center text-[9px] font-bold transition-transform hover:scale-110 cursor-pointer ${colorCls}`}
                      >
                        {val > 0 ? (val > 1000 ? `${(val / 1000).toFixed(1)}k` : Math.round(val)) : ''}
                      </div>
                    );
                  })}
                </div>
              ))}

              {/* Heatmap Legend */}
              <div className="flex items-center justify-end space-x-3 text-[10px] font-semibold text-slate-400 mt-4 pt-3 border-t border-slate-100 dark:border-slate-800">
                <span>Low Demand</span>
                <span className="w-4 h-3 rounded bg-blue-200 dark:bg-blue-900/60"></span>
                <span className="w-4 h-3 rounded bg-blue-400"></span>
                <span className="w-4 h-3 rounded bg-amber-400"></span>
                <span className="w-4 h-3 rounded bg-rose-500"></span>
                <span className="w-4 h-3 rounded bg-rose-600"></span>
                <span>Critical Surge Peak</span>
              </div>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
