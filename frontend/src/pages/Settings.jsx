import React, { useState, useEffect, useCallback } from 'react';
import {
  Settings as SettingsIcon,
  Save,
  RotateCcw,
  Bus,
  Brain,
  Clock,
  BarChart3,
  Palette,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';

import PageHeader from '../components/common/PageHeader';
import Card from '../components/common/Card';
import { useTheme } from '../context/ThemeContext';

/* ------------------------------------------------------------------ */
/*  Defaults                                                          */
/* ------------------------------------------------------------------ */
const DEFAULTS = {
  vehicleCapacity: 50,
  defaultModel: 'xgboost',
  forecastHorizon: 24,
  demandThresholds: { low: 500, moderate: 1500, high: 3000 },
  dashboardRefresh: 0,       // 0 = manual only
  chartAnimation: true,
  compactNumbers: true,
};

const STORAGE_KEY = 'transit_ai_settings';

function loadSettings() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? { ...DEFAULTS, ...JSON.parse(raw) } : { ...DEFAULTS };
  } catch {
    return { ...DEFAULTS };
  }
}

/* ------------------------------------------------------------------ */
/*  Reusable tiny components                                          */
/* ------------------------------------------------------------------ */
function SectionTitle({ icon: Icon, title, subtitle }) {
  return (
    <div className="flex items-center space-x-3 mb-5">
      <div className="w-9 h-9 rounded-xl bg-brand-50 dark:bg-brand-950/40 flex items-center justify-center text-brand-600 dark:text-brand-400">
        <Icon className="w-4.5 h-4.5" />
      </div>
      <div>
        <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-200">{title}</h3>
        {subtitle && <p className="text-xs text-slate-400">{subtitle}</p>}
      </div>
    </div>
  );
}

function FieldRow({ label, description, children }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 py-3 border-b border-slate-100 dark:border-slate-800 last:border-0">
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-slate-700 dark:text-slate-300">{label}</p>
        {description && <p className="text-xs text-slate-400 mt-0.5">{description}</p>}
      </div>
      <div className="flex-shrink-0">{children}</div>
    </div>
  );
}

function NumberInput({ value, onChange, min = 0, max, step = 1, className = '' }) {
  return (
    <input
      type="number"
      value={value}
      min={min}
      max={max}
      step={step}
      onChange={e => onChange(Number(e.target.value))}
      className={`w-28 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500 outline-none transition ${className}`}
    />
  );
}

function SelectInput({ value, onChange, options }) {
  return (
    <select
      value={value}
      onChange={e => onChange(e.target.value)}
      className="w-40 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500 outline-none transition"
    >
      {options.map(o => (
        <option key={o.value} value={o.value}>{o.label}</option>
      ))}
    </select>
  );
}

function ToggleSwitch({ checked, onChange }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
        checked ? 'bg-brand-500' : 'bg-slate-300 dark:bg-slate-600'
      }`}
    >
      <span
        className={`inline-block h-4 w-4 rounded-full bg-white shadow-sm transform transition-transform ${
          checked ? 'translate-x-6' : 'translate-x-1'
        }`}
      />
    </button>
  );
}

/* ------------------------------------------------------------------ */
/*  Toast                                                             */
/* ------------------------------------------------------------------ */
function Toast({ show, message, type = 'success' }) {
  if (!show) return null;
  const Icon = type === 'success' ? CheckCircle2 : AlertTriangle;
  const colors =
    type === 'success'
      ? 'bg-emerald-50 border-emerald-200 text-emerald-700 dark:bg-emerald-950/60 dark:border-emerald-800 dark:text-emerald-400'
      : 'bg-amber-50 border-amber-200 text-amber-700 dark:bg-amber-950/60 dark:border-amber-800 dark:text-amber-400';

  return (
    <div className={`fixed top-20 right-6 z-[60] flex items-center space-x-2 px-4 py-3 rounded-xl border shadow-lg ${colors} animate-slide-in`}>
      <Icon className="w-4 h-4 flex-shrink-0" />
      <span className="text-sm font-medium">{message}</span>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Main Settings Page                                                */
/* ------------------------------------------------------------------ */
export default function Settings() {
  const { theme, toggleTheme } = useTheme();
  const [settings, setSettings] = useState(loadSettings);
  const [toast, setToast] = useState({ show: false, message: '', type: 'success' });
  const [dirty, setDirty] = useState(false);

  /* Helpers */
  const patch = useCallback((key, value) => {
    setSettings(prev => {
      const next = { ...prev, [key]: value };
      setDirty(true);
      return next;
    });
  }, []);

  const patchThreshold = useCallback((key, value) => {
    setSettings(prev => {
      const next = { ...prev, demandThresholds: { ...prev.demandThresholds, [key]: value } };
      setDirty(true);
      return next;
    });
  }, []);

  const showToast = (message, type = 'success') => {
    setToast({ show: true, message, type });
    setTimeout(() => setToast({ show: false, message: '', type: 'success' }), 3000);
  };

  const handleSave = () => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
      setDirty(false);
      showToast('Settings saved successfully!');
    } catch {
      showToast('Failed to save settings.', 'error');
    }
  };

  const handleReset = () => {
    setSettings({ ...DEFAULTS });
    localStorage.removeItem(STORAGE_KEY);
    setDirty(false);
    showToast('Settings reset to defaults.');
  };

  return (
    <div className="space-y-8">
      <Toast show={toast.show} message={toast.message} type={toast.type} />

      <PageHeader
        title="Settings"
        subtitle="Configure vehicle capacity, demand thresholds, ML models, and dashboard preferences."
        badge="Configuration"
      />

      {/* Action Bar */}
      <div className="flex items-center justify-end space-x-3">
        <button
          onClick={handleReset}
          className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-700 text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
        >
          <RotateCcw className="w-4 h-4" />
          <span>Reset Defaults</span>
        </button>
        <button
          onClick={handleSave}
          disabled={!dirty}
          className={`inline-flex items-center space-x-2 px-5 py-2 rounded-xl text-sm font-semibold shadow-sm transition ${
            dirty
              ? 'bg-brand-500 hover:bg-brand-600 text-white shadow-brand-500/20'
              : 'bg-slate-200 dark:bg-slate-700 text-slate-400 cursor-not-allowed'
          }`}
        >
          <Save className="w-4 h-4" />
          <span>Save Changes</span>
        </button>
      </div>

      {/* Grid of Setting Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* ───── Transport / Optimization ───── */}
        <Card>
          <SectionTitle icon={Bus} title="Transport Capacity" subtitle="Vehicle configuration for optimization module" />

          <FieldRow label="Vehicle Capacity" description="Assumed passengers per vehicle for capacity calculations.">
            <NumberInput value={settings.vehicleCapacity} onChange={v => patch('vehicleCapacity', v)} min={10} max={500} step={5} />
          </FieldRow>
        </Card>

        {/* ───── ML Model Defaults ───── */}
        <Card>
          <SectionTitle icon={Brain} title="Machine Learning" subtitle="Default model and forecast settings" />

          <FieldRow label="Default Model" description="ML model used by default across pages.">
            <SelectInput
              value={settings.defaultModel}
              onChange={v => patch('defaultModel', v)}
              options={[
                { value: 'random_forest', label: 'Random Forest' },
                { value: 'xgboost', label: 'XGBoost' },
                { value: 'lstm', label: 'LSTM' },
              ]}
            />
          </FieldRow>

          <FieldRow label="Forecast Horizon" description="Default hours to forecast when generating predictions.">
            <SelectInput
              value={settings.forecastHorizon}
              onChange={v => patch('forecastHorizon', Number(v))}
              options={[
                { value: 6, label: '6 hours' },
                { value: 12, label: '12 hours' },
                { value: 24, label: '24 hours' },
                { value: 48, label: '48 hours' },
                { value: 168, label: '7 days (168 h)' },
              ]}
            />
          </FieldRow>
        </Card>

        {/* ───── Demand Thresholds ───── */}
        <Card>
          <SectionTitle icon={BarChart3} title="Demand Classification" subtitle="Thresholds for Low / Moderate / High / Very High labels" />

          <FieldRow label="Low → Moderate" description="Ridership above this is 'Moderate'.">
            <NumberInput value={settings.demandThresholds.low} onChange={v => patchThreshold('low', v)} min={0} step={100} />
          </FieldRow>

          <FieldRow label="Moderate → High" description="Ridership above this is 'High'.">
            <NumberInput value={settings.demandThresholds.moderate} onChange={v => patchThreshold('moderate', v)} min={0} step={100} />
          </FieldRow>

          <FieldRow label="High → Very High" description="Ridership above this is 'Very High'.">
            <NumberInput value={settings.demandThresholds.high} onChange={v => patchThreshold('high', v)} min={0} step={100} />
          </FieldRow>
        </Card>

        {/* ───── Dashboard Preferences ───── */}
        <Card>
          <SectionTitle icon={Palette} title="Dashboard Preferences" subtitle="Visual and behavioral settings" />

          <FieldRow label="Dark Mode" description="Toggle between light and dark themes.">
            <ToggleSwitch checked={theme === 'dark'} onChange={toggleTheme} />
          </FieldRow>

          <FieldRow label="Chart Animations" description="Enable smooth transitions on Recharts components.">
            <ToggleSwitch checked={settings.chartAnimation} onChange={v => patch('chartAnimation', v)} />
          </FieldRow>

          <FieldRow label="Compact Numbers" description="Show 1.2K instead of 1,200 for large values.">
            <ToggleSwitch checked={settings.compactNumbers} onChange={v => patch('compactNumbers', v)} />
          </FieldRow>

          <FieldRow label="Auto-refresh Interval" description="Auto-refresh dashboard data (seconds). 0 = manual.">
            <SelectInput
              value={settings.dashboardRefresh}
              onChange={v => patch('dashboardRefresh', Number(v))}
              options={[
                { value: 0, label: 'Manual only' },
                { value: 30, label: '30 seconds' },
                { value: 60, label: '1 minute' },
                { value: 300, label: '5 minutes' },
              ]}
            />
          </FieldRow>
        </Card>
      </div>

      {/* Current Config JSON (debug-friendly, collapsed) */}
      <Card>
        <SectionTitle icon={SettingsIcon} title="Current Configuration" subtitle="JSON representation of saved settings" />
        <pre className="text-xs font-mono bg-slate-50 dark:bg-slate-800/60 border border-slate-200/60 dark:border-slate-700 rounded-xl p-4 overflow-x-auto text-slate-600 dark:text-slate-300">
          {JSON.stringify(settings, null, 2)}
        </pre>
      </Card>
    </div>
  );
}
