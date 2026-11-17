import React from 'react';
import { CalendarDays, ArrowUpRight, ArrowDownRight, TrendingUp, Users } from 'lucide-react';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';

import PageHeader from '../components/common/PageHeader';
import StatCard from '../components/common/StatCard';
import Card from '../components/common/Card';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';

import { useFetch } from '../hooks/useFetch';
import { getWeekdayWeekendComparison } from '../services/api';
import { formatNumber, formatCompactNumber, formatHour, formatPercentage } from '../utils/formatters';

export default function WeekdayWeekendAnalysis() {
  const { data, loading, error, refetch } = useFetch(getWeekdayWeekendComparison);

  if (loading) return <LoadingSpinner message="Analyzing weekday vs weekend travel behavior..." />;
  if (error) return <ErrorMessage message={error} onRetry={refetch} />;

  const weekdayAvg = data?.weekday_avg || 0;
  const weekendAvg = data?.weekend_avg || 0;
  const diffPct = data?.difference_pct || 0;
  const weekdayHourly = data?.weekday_hourly || [];
  const weekendHourly = data?.weekend_hourly || [];

  // Combined chart data
  const hourlyComparison = [];
  for (let i = 0; i < 24; i++) {
    const wdVal = weekdayHourly.find(h => h.hour === i)?.avg_ridership || 0;
    const weVal = weekendHourly.find(h => h.hour === i)?.avg_ridership || 0;
    hourlyComparison.push({
      hour: i,
      label: formatHour(i),
      weekday: Math.round(wdVal),
      weekend: Math.round(weVal),
      difference: Math.round(wdVal - weVal),
    });
  }

  // Bar chart: time-of-day buckets
  const timeBuckets = [
    { name: 'Early Morning\n(0-6 AM)', weekday: 0, weekend: 0 },
    { name: 'Morning Rush\n(7-10 AM)', weekday: 0, weekend: 0 },
    { name: 'Midday\n(11 AM-3 PM)', weekday: 0, weekend: 0 },
    { name: 'Evening Rush\n(4-7 PM)', weekday: 0, weekend: 0 },
    { name: 'Night\n(8-11 PM)', weekday: 0, weekend: 0 },
  ];

  hourlyComparison.forEach(h => {
    if (h.hour <= 6) { timeBuckets[0].weekday += h.weekday; timeBuckets[0].weekend += h.weekend; }
    else if (h.hour <= 10) { timeBuckets[1].weekday += h.weekday; timeBuckets[1].weekend += h.weekend; }
    else if (h.hour <= 15) { timeBuckets[2].weekday += h.weekday; timeBuckets[2].weekend += h.weekend; }
    else if (h.hour <= 19) { timeBuckets[3].weekday += h.weekday; timeBuckets[3].weekend += h.weekend; }
    else { timeBuckets[4].weekday += h.weekday; timeBuckets[4].weekend += h.weekend; }
  });

  return (
    <div className="space-y-8">
      <PageHeader
        title="Weekday vs Weekend Demand Analysis"
        subtitle="Compare commuter-driven weekday patterns against leisure weekend travel behavior."
        badge="Behavioral Analytics"
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          title="Weekday Average"
          value={formatNumber(weekdayAvg)}
          subtitle="Mon–Fri hourly mean"
          icon={TrendingUp}
          color="blue"
          trend={weekdayAvg > weekendAvg ? 'up' : 'down'}
          trendValue={`${Math.abs(diffPct).toFixed(1)}% vs weekend`}
        />
        <StatCard
          title="Weekend Average"
          value={formatNumber(weekendAvg)}
          subtitle="Sat–Sun hourly mean"
          icon={CalendarDays}
          color="purple"
        />
        <StatCard
          title="Traffic Differential"
          value={formatPercentage(diffPct)}
          subtitle={weekdayAvg > weekendAvg ? 'Weekdays carry more traffic' : 'Weekends carry more traffic'}
          icon={Users}
          color={diffPct > 0 ? 'emerald' : 'amber'}
        />
      </div>

      {/* Hourly Comparison Line Chart */}
      <Card
        title="24-Hour Demand Overlay: Weekday vs Weekend"
        subtitle="Superimposed hourly boarding patterns showing commuter peaks on weekdays and flatter weekend leisure curves."
      >
        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={hourlyComparison} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" opacity={0.6} />
              <XAxis dataKey="label" tick={{ fontSize: 10 }} stroke="#94a3b8" interval={2} />
              <YAxis tickFormatter={v => formatCompactNumber(v)} tick={{ fontSize: 11 }} stroke="#94a3b8" />
              <Tooltip formatter={v => [formatNumber(v) + ' riders', '']} />
              <Legend verticalAlign="top" wrapperStyle={{ paddingBottom: '10px', fontSize: '12px' }} />
              <Line type="monotone" dataKey="weekday" name="Weekday (Mon-Fri)" stroke="#2563eb" strokeWidth={2.5} dot={{ r: 2 }} activeDot={{ r: 5 }} />
              <Line type="monotone" dataKey="weekend" name="Weekend (Sat-Sun)" stroke="#8b5cf6" strokeWidth={2.5} strokeDasharray="6 3" dot={{ r: 2 }} activeDot={{ r: 5 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* Time-of-Day Bucket Comparison */}
      <Card
        title="Time-of-Day Period Comparison"
        subtitle="Grouped bars showing weekday vs weekend passenger volumes across distinct operational periods."
      >
        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={timeBuckets} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" opacity={0.6} />
              <XAxis dataKey="name" tick={{ fontSize: 10 }} stroke="#94a3b8" />
              <YAxis tickFormatter={v => formatCompactNumber(v)} tick={{ fontSize: 11 }} stroke="#94a3b8" />
              <Tooltip formatter={v => [formatNumber(v) + ' riders', '']} />
              <Legend verticalAlign="top" wrapperStyle={{ paddingBottom: '10px', fontSize: '12px' }} />
              <Bar dataKey="weekday" name="Weekday" fill="#2563eb" radius={[4, 4, 0, 0]} />
              <Bar dataKey="weekend" name="Weekend" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* Key Insights */}
      <Card title="Key Behavioral Insights">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div className="bg-blue-50/80 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-900 rounded-xl p-4">
            <h4 className="font-bold text-blue-900 dark:text-blue-300 mb-1">Morning Rush Differential</h4>
            <p className="text-blue-700 dark:text-blue-400 text-xs">
              Weekday mornings (7-10 AM) show significantly higher demand driven by office commuter flows. Weekend mornings are more gradual as leisure travelers start later.
            </p>
          </div>
          <div className="bg-purple-50/80 dark:bg-purple-950/30 border border-purple-200 dark:border-purple-900 rounded-xl p-4">
            <h4 className="font-bold text-purple-900 dark:text-purple-300 mb-1">Weekend Midday Pattern</h4>
            <p className="text-purple-700 dark:text-purple-400 text-xs">
              Weekend midday (11 AM-3 PM) demand can approach or exceed weekday off-peak levels, driven by tourism and shopping activity in Manhattan.
            </p>
          </div>
          <div className="bg-emerald-50/80 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900 rounded-xl p-4">
            <h4 className="font-bold text-emerald-900 dark:text-emerald-300 mb-1">Evening Commute</h4>
            <p className="text-emerald-700 dark:text-emerald-400 text-xs">
              The evening peak (4-7 PM) is the highest demand window on weekdays, as office workers return home. Weekend evenings show entertainment and dining traffic.
            </p>
          </div>
          <div className="bg-amber-50/80 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900 rounded-xl p-4">
            <h4 className="font-bold text-amber-900 dark:text-amber-300 mb-1">Fleet Optimization Opportunity</h4>
            <p className="text-amber-700 dark:text-amber-400 text-xs">
              Weekend services can operate with reduced fleet sizes during early morning and late night hours, while maintaining adequate midday capacity for leisure travelers.
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}
