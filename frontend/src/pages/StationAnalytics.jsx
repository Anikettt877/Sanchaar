import React, { useState, useEffect } from 'react';
import { MapPin, Building2, ArrowUp, ArrowDown, BarChart3, Users } from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, LineChart, Line,
} from 'recharts';

import PageHeader from '../components/common/PageHeader';
import StatCard from '../components/common/StatCard';
import Card from '../components/common/Card';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';

import { useFetch } from '../hooks/useFetch';
import { getStationRankings, getBoroughStats, getStationDetails, getStationsList } from '../services/api';
import { formatNumber, formatCompactNumber, formatHour } from '../utils/formatters';

const BOROUGH_COLORS = {
  Manhattan: '#3b82f6',
  Brooklyn: '#10b981',
  Queens: '#f59e0b',
  Bronx: '#ef4444',
  'Staten Island': '#8b5cf6',
};

export default function StationAnalytics() {
  const { data: rankings, loading: rankLoading, error: rankError, refetch: refetchRanks } = useFetch(() => getStationRankings(10));
  const { data: boroughData, loading: boroughLoading } = useFetch(getBoroughStats);
  const { data: stationsList } = useFetch(getStationsList);

  const [selectedStation, setSelectedStation] = useState(null);
  const [stationDetail, setStationDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const stations = stationsList || [];
  const topStations = rankings?.top_stations || [];
  const bottomStations = rankings?.bottom_stations || [];
  const boroughs = boroughData || [];

  useEffect(() => {
    if (stations.length > 0 && !selectedStation) {
      setSelectedStation(String(stations[0].id));
    }
  }, [stations]);

  useEffect(() => {
    if (!selectedStation) return;
    async function loadDetail() {
      setDetailLoading(true);
      try {
        const res = await getStationDetails(selectedStation);
        setStationDetail(res.data);
      } catch (err) {
        console.error('Station detail failed:', err);
      } finally {
        setDetailLoading(false);
      }
    }
    loadDetail();
  }, [selectedStation]);

  if (rankLoading) return <LoadingSpinner message="Ranking transit hubs by passenger volume..." />;
  if (rankError) return <ErrorMessage message={rankError} onRetry={refetchRanks} />;

  const pieData = boroughs.map(b => ({
    name: b.borough,
    value: Math.round(b.total_ridership || 0),
    color: BOROUGH_COLORS[b.borough] || '#94a3b8',
  }));

  return (
    <div className="space-y-8">
      <PageHeader
        title="Station & Borough Analytics"
        subtitle="Comparative demand profiling across NYC subway station complexes and borough corridors."
        badge="Geospatial Intelligence"
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Borough Pie Chart */}
        <Card title="Borough Ridership Share" subtitle="Cumulative passenger distribution across NYC borough corridors.">
          {boroughLoading ? <LoadingSpinner /> : (
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="45%" innerRadius={50} outerRadius={85} paddingAngle={3} dataKey="value">
                    {pieData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                  </Pie>
                  <Tooltip formatter={(v) => formatCompactNumber(v) + ' riders'} />
                  <Legend verticalAlign="bottom" wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </Card>

        {/* Top 10 Stations */}
        <Card title="Top 10 Busiest Stations" subtitle="Highest cumulative boarding volume complexes." className="lg:col-span-2">
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={topStations} layout="vertical" margin={{ top: 5, right: 20, left: 100, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" opacity={0.6} />
                <XAxis type="number" tickFormatter={v => formatCompactNumber(v)} tick={{ fontSize: 11 }} stroke="#94a3b8" />
                <YAxis type="category" dataKey="name" tickFormatter={n => n.length > 18 ? n.substring(0, 18) + '…' : n} tick={{ fontSize: 10 }} stroke="#94a3b8" width={100} />
                <Tooltip formatter={v => [formatNumber(v) + ' riders', 'Total Ridership']} />
                <Bar dataKey="total_ridership" fill="#2563eb" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Bottom 10 Stations */}
      <Card title="Lowest-Demand Stations" subtitle="Stations with least ridership — potential candidates for service frequency adjustment.">
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={bottomStations} layout="vertical" margin={{ top: 5, right: 20, left: 100, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" opacity={0.6} />
              <XAxis type="number" tickFormatter={v => formatCompactNumber(v)} tick={{ fontSize: 11 }} stroke="#94a3b8" />
              <YAxis type="category" dataKey="name" tickFormatter={n => n.length > 18 ? n.substring(0, 18) + '…' : n} tick={{ fontSize: 10 }} stroke="#94a3b8" width={100} />
              <Tooltip formatter={v => [formatNumber(v) + ' riders', 'Total Ridership']} />
              <Bar dataKey="total_ridership" fill="#f59e0b" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* Station Detail Selector */}
      <Card title="Station Demand Deep-Dive" subtitle="Select a station complex to explore its hourly boarding patterns and peak behavior.">
        <div className="space-y-6">
          <select
            value={selectedStation || ''}
            onChange={e => setSelectedStation(e.target.value)}
            className="w-full max-w-md text-sm bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl px-4 py-2.5 font-medium text-slate-900 dark:text-white focus:ring-2 focus:ring-brand-500 outline-none"
          >
            {stations.map(st => (
              <option key={st.id} value={st.id}>{st.name} ({st.borough})</option>
            ))}
          </select>

          {detailLoading && <LoadingSpinner message="Loading station profile..." />}

          {stationDetail && !detailLoading && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl p-4 border border-slate-200/60 dark:border-slate-700">
                  <p className="text-xs font-semibold text-slate-500 uppercase">Borough</p>
                  <p className="text-lg font-bold text-slate-900 dark:text-white mt-1">{stationDetail.borough}</p>
                </div>
                <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl p-4 border border-slate-200/60 dark:border-slate-700">
                  <p className="text-xs font-semibold text-slate-500 uppercase">Avg Hourly</p>
                  <p className="text-lg font-bold text-slate-900 dark:text-white mt-1">{formatNumber(stationDetail.avg_ridership)}</p>
                </div>
                <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl p-4 border border-slate-200/60 dark:border-slate-700">
                  <p className="text-xs font-semibold text-slate-500 uppercase">Total Ridership</p>
                  <p className="text-lg font-bold text-slate-900 dark:text-white mt-1">{formatCompactNumber(stationDetail.total_ridership)}</p>
                </div>
                <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl p-4 border border-slate-200/60 dark:border-slate-700">
                  <p className="text-xs font-semibold text-slate-500 uppercase">Peak Hour</p>
                  <p className="text-lg font-bold text-slate-900 dark:text-white mt-1">{formatHour(stationDetail.peak_hour)}</p>
                </div>
              </div>

              {stationDetail.hourly_pattern && (
                <div className="h-56">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={stationDetail.hourly_pattern} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" opacity={0.6} />
                      <XAxis dataKey="hour" tickFormatter={h => `${h}h`} tick={{ fontSize: 11 }} stroke="#94a3b8" />
                      <YAxis tickFormatter={v => formatCompactNumber(v)} tick={{ fontSize: 11 }} stroke="#94a3b8" />
                      <Tooltip formatter={v => [formatNumber(v) + ' riders', 'Avg Ridership']} labelFormatter={h => formatHour(h)} />
                      <Line type="monotone" dataKey="avg_ridership" stroke="#2563eb" strokeWidth={2.5} dot={{ r: 3 }} activeDot={{ r: 6 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
