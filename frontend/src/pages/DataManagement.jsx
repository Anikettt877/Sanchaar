import React from 'react';
import { Database, Table, FileText, RefreshCw, Search } from 'lucide-react';

import PageHeader from '../components/common/PageHeader';
import StatCard from '../components/common/StatCard';
import Card from '../components/common/Card';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';

import { useFetch } from '../hooks/useFetch';
import { getDatasetInfo, getDatasetPreview, getStationsList } from '../services/api';
import { formatNumber, formatCompactNumber } from '../utils/formatters';

export default function DataManagement() {
  const { data: info, loading: infoLoading, error: infoError, refetch: refetchInfo } = useFetch(getDatasetInfo);
  const { data: previewRes, loading: previewLoading } = useFetch(getDatasetPreview);
  const { data: stationsRes, loading: stationsLoading } = useFetch(getStationsList);

  if (infoLoading) return <LoadingSpinner message="Loading dataset metadata..." />;
  if (infoError) return <ErrorMessage message={infoError} onRetry={refetchInfo} />;

  const datasetInfo = info || {};
  const previewData = previewRes?.data || [];
  const previewColumns = previewRes?.columns || [];
  const stationsList = stationsRes?.data || [];

  return (
    <div className="space-y-8">
      <PageHeader
        title="Data Management Console"
        subtitle="Inspect the MTA Subway ridership dataset, review schema, preview records, and explore station metadata."
        badge="Data Quality"
      />

      {/* Dataset Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Records" value={formatNumber(datasetInfo.total_records)} subtitle="Engineered feature rows" icon={Database} color="blue" />
        <StatCard title="Total Columns" value={datasetInfo.total_columns || 22} subtitle="Features + target" icon={Table} color="indigo" />
        <StatCard title="Station Complexes" value={datasetInfo.unique_stations || 13} subtitle="NYC Subway hubs" icon={FileText} color="emerald" />
        <StatCard title="Date Range" value={datasetInfo.date_range?.start ? `${datasetInfo.date_range.start.substring(0, 10)} → ${datasetInfo.date_range.end.substring(0, 10)}` : 'Jan-Jun 2024'} subtitle="6-month coverage" icon={RefreshCw} color="amber" />
      </div>

      {/* Column Schema */}
      <Card title="Dataset Column Schema" subtitle="Engineered feature columns in the processed ridership dataset.">
        {datasetInfo.columns ? (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
            {(datasetInfo.columns || previewColumns).map((col, idx) => (
              <div key={col} className="flex items-center space-x-2 text-xs bg-slate-50 dark:bg-slate-800/60 rounded-lg px-3 py-2 border border-slate-200/60 dark:border-slate-700">
                <span className="w-5 h-5 flex items-center justify-center rounded bg-brand-100 dark:bg-brand-900/40 text-brand-700 dark:text-brand-300 font-bold text-[10px]">
                  {idx + 1}
                </span>
                <span className="font-mono font-medium text-slate-700 dark:text-slate-300">{col}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {previewColumns.map((col, idx) => (
              <div key={col} className="flex items-center space-x-2 text-xs bg-slate-50 dark:bg-slate-800/60 rounded-lg px-3 py-2 border border-slate-200/60 dark:border-slate-700">
                <span className="font-mono font-medium text-slate-700 dark:text-slate-300">{col}</span>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Data Preview Table */}
      <Card title="Dataset Preview (First 25 Records)" subtitle="Raw view of the engineered ridership feature dataset.">
        {previewLoading ? <LoadingSpinner message="Loading preview data..." /> : (
          <div className="overflow-x-auto max-h-96 overflow-y-auto">
            <table className="w-full text-left text-[11px]">
              <thead className="sticky top-0 bg-slate-50 dark:bg-slate-800 uppercase font-semibold text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-700">
                <tr>
                  {previewColumns.slice(0, 12).map(col => (
                    <th key={col} className="px-3 py-2.5 whitespace-nowrap">{col.replace('_', ' ')}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {previewData.slice(0, 25).map((row, idx) => (
                  <tr key={idx} className="hover:bg-slate-50/80 dark:hover:bg-slate-800/40">
                    {previewColumns.slice(0, 12).map(col => (
                      <td key={col} className="px-3 py-2 whitespace-nowrap text-slate-700 dark:text-slate-300">
                        {typeof row[col] === 'number' ? (Number.isInteger(row[col]) ? row[col] : row[col].toFixed(2)) : String(row[col] || '').substring(0, 25)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Station Registry */}
      <Card title="Station Complex Registry" subtitle="All indexed subway station complexes with borough and geographic coordinates.">
        {stationsLoading ? <LoadingSpinner /> : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-slate-800 uppercase font-semibold text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-700">
                <tr>
                  <th className="px-4 py-3">ID</th>
                  <th className="px-4 py-3">Station Name</th>
                  <th className="px-4 py-3">Borough</th>
                  <th className="px-4 py-3">Latitude</th>
                  <th className="px-4 py-3">Longitude</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {stationsList.map(st => (
                  <tr key={st.id} className="hover:bg-slate-50/80 dark:hover:bg-slate-800/40">
                    <td className="px-4 py-3 font-mono font-bold text-brand-600">{st.id}</td>
                    <td className="px-4 py-3 font-semibold text-slate-900 dark:text-white">{st.name}</td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{st.borough}</td>
                    <td className="px-4 py-3 font-mono text-slate-500">{Number(st.lat).toFixed(4)}</td>
                    <td className="px-4 py-3 font-mono text-slate-500">{Number(st.lon).toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
