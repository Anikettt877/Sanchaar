import React from 'react';
import { getDemandBadge } from '../../utils/formatters';

export default function Badge({ level, text }) {
  const badgeInfo = getDemandBadge(level);

  return (
    <span className={`inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${badgeInfo.bg}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${badgeInfo.dot}`}></span>
      <span>{text || badgeInfo.label}</span>
    </span>
  );
}
