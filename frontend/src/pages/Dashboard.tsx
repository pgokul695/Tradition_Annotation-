import { useEffect, useState } from 'react';
import { get, post } from '../api/client';

type StyleRow = {
  style: string;
  count: number;
  approved: number;
  approval_rate: number;
};

type Stats = {
  total: number;
  pending: number;
  annotated: number;
  approved: number;
  rejected: number;
  needs_review: number;
  missing_file: number;
  styles: StyleRow[];
};

export default function Dashboard() {
  const [s, setS] = useState<Stats>();
  const [ingesting, setIngesting] = useState(false);

  const load = () => get('/stats').then(setS);

  useEffect(() => { load(); }, []);

  const handleIngest = async () => {
    setIngesting(true);
    await post('/ingest');
    await load();
    setIngesting(false);
  };

  if (!s) {
    return <p className="loading-text">Loading dashboard…</p>;
  }

  const done = s.approved + s.rejected;
  const pct = s.total ? Math.round((done / s.total) * 100) : 0;

  const statItems: [string, number][] = [
    ['Total', s.total],
    ['Annotated', s.annotated],
    ['Approved', s.approved],
    ['Rejected', s.rejected],
    ['Remaining', s.pending],
    ['Missing files', s.missing_file],
  ];

  return (
    <>
      <div className="page-title">
        <div>
          <p className="eyebrow">Research Dataset</p>
          <h2>Annotation Progress</h2>
        </div>
        <div className="actions">
          <button onClick={handleIngest} disabled={ingesting}>
            {ingesting ? 'Ingesting…' : 'Ingest dataset'}
          </button>
        </div>
      </div>

      {/* ── Stat cards ── */}
      <section className="stats">
        {statItems.map(([label, value]) => (
          <article key={label}>
            <div className="stat-label">{label}</div>
            <div className="stat-value">{value}</div>
          </article>
        ))}
      </section>

      {/* ── Progress ── */}
      <section className="panel">
        <div className="progress-wrap">
          <div className="progress">
            <div
              className="progress-fill"
              style={{ width: `${pct}%` }}
            />
          </div>
          <div className="progress-meta">
            <span>{done} of {s.total} reviewed · {s.needs_review} need review · {s.missing_file} files missing</span>
            <span className="progress-pct">{pct}%</span>
          </div>
        </div>
      </section>

      {/* ── By tradition ── */}
      <section className="panel">
        <h3>By Tradition</h3>
        <table>
          <thead>
            <tr>
              <th>Style</th>
              <th>Images</th>
              <th>Approved</th>
              <th>Rate</th>
            </tr>
          </thead>
          <tbody>
            {s.styles.map(row => (
              <tr key={row.style}>
                <td>{row.style || '—'}</td>
                <td>{row.count}</td>
                <td>{row.approved}</td>
                <td>
                  <span className="rate-badge">
                    {Math.round(row.approval_rate * 100)}%
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {s.styles.length === 0 && (
          <p className="empty-state">No style data yet. Run ingest to populate.</p>
        )}
      </section>
    </>
  );
}
