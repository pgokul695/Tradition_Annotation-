import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { get, post } from '../api/client';

const STATUS_TABS = ['pending', 'annotated', 'approved', 'rejected', 'needs_review', 'missing_file'] as const;

type ImageItem = {
  image_id: string;
  style: string;
  local_path: string;
  annotation: {
    status: string;
    confidence: number | null;
  };
};

type GalleryData = {
  items: ImageItem[];
  total: number;
  page: number;
  page_size: number;
};
type ConfiguredModel = { id: string; label: string; available?: boolean; error?: string | null };

export default function Gallery() {
  const navigate = useNavigate();
  const [status, setStatus]     = useState<string>('pending');
  const [data, setData]         = useState<GalleryData>({ items: [], total: 0, page: 1, page_size: 24 });
  const [selected, setSelected] = useState<string[]>([]);
  const [search, setSearch]     = useState('');
  const [style, setStyle]       = useState('');
  const [tag, setTag]           = useState('');
  const [reviewer, setReviewer] = useState('');
  const [minConf, setMinConf]   = useState('');
  const [maxConf, setMaxConf]   = useState('');
  const [running, setRunning]   = useState(false);
  const [page, setPage]         = useState(1);
  const [models, setModels]     = useState<ConfiguredModel[]>([]);
  const [showRunMenu, setShowRunMenu] = useState(false);
  const [batchSize, setBatchSize] = useState<number | 'all'>(25);
  const [selectedModel, setSelectedModel] = useState('');
  const [runMessage, setRunMessage] = useState('');

  const buildQuery = () =>
    new URLSearchParams({
      status,
      search,
      ...(style    ? { style }                         : {}),
      ...(tag      ? { tag }                           : {}),
      ...(reviewer ? { reviewer }                      : {}),
      ...(minConf  ? { min_confidence: minConf }       : {}),
      ...(maxConf  ? { max_confidence: maxConf }       : {}),
      page: String(page),
    }).toString();

  const load = () => get(`/images?${buildQuery()}`).then(setData);

  useEffect(() => { load(); clearSelect(); }, [status, page, search, style, tag, reviewer, minConf, maxConf]); // eslint-disable-line
  useEffect(() => {
    get('/models').then((result: { models: ConfiguredModel[] }) => {
      setModels(result.models);
      setSelectedModel(current => current || result.models.find(model => model.available !== false)?.id || '');
    });
  }, []);

  const toggleSelect = (id: string) =>
    setSelected(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);

  const clearSelect = () => setSelected([]);

  const handleBulkApprove = async () => {
    await post('/bulk/approve', { image_ids: selected });
    clearSelect();
    load();
  };

  const handleBulkStyle = async () => {
    const value = window.prompt('Set tradition style for selected images');
    if (value) {
      await post('/bulk/set-style', { image_ids: selected, style: value });
      clearSelect();
      load();
    }
  };

  const handleRunAI = async () => {
    setRunning(true);
    const body: { limit?: number; model?: string } = {};
    if (batchSize !== 'all') body.limit = batchSize;
    if (models.length > 1 && selectedModel) body.model = selectedModel;
    const result = await post('/annotate/run', body);
    setRunMessage(`Queued ${result.queued} image${result.queued === 1 ? '' : 's'}${result.model ? ` · ${result.model}` : ''}`);
    setShowRunMenu(false);
    await load();
    setRunning(false);
  };

  const handleAutoApprove = async () => {
    await post('/bulk/auto-approve', { confidence_threshold: 0.95, needs_review_threshold: 0.70 });
    load();
  };

  const exportBase = `/api/export?${buildQuery()}`;
  const galleryIds = data.items.map(item => item.image_id);
  const totalPages = Math.max(1, Math.ceil(data.total / data.page_size));
  const firstResult = data.total === 0 ? 0 : (page - 1) * data.page_size + 1;
  const lastResult = Math.min(page * data.page_size, data.total);
  const changePage = (nextPage: number) => {
    setPage(Math.min(Math.max(nextPage, 1), totalPages));
    clearSelect();
  };
  const resetPage = () => { setPage(1); clearSelect(); };
  const pageItems: Array<number | 'ellipsis'> = totalPages <= 7
    ? Array.from({ length: totalPages }, (_, index) => index + 1)
    : page <= 4
      ? [1, 2, 3, 4, 'ellipsis', totalPages]
      : page >= totalPages - 3
        ? [1, 'ellipsis', totalPages - 3, totalPages - 2, totalPages - 1, totalPages]
        : [1, 'ellipsis', page - 1, page, page + 1, 'ellipsis', totalPages];
  const styleColor = (value: string) => {
    const colors = ['#a84f3b', '#bf7c3d', '#557c65', '#467a92', '#765c91', '#8e6b42'];
    return colors[[...value].reduce((total, character) => total + character.charCodeAt(0), 0) % colors.length];
  };

  return (
    <>
      <div className="page-title">
        <div>
          <p className="eyebrow">Review Queue</p>
          <h2>
            Gallery{' '}
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '14px', fontWeight: 400, color: 'var(--ink-muted)' }}>
              {data.total || 0}
            </span>
          </h2>
        </div>
        <div className="actions">
          <div className="run-ai-wrap">
          <button onClick={() => setShowRunMenu(open => !open)} disabled={running} aria-expanded={showRunMenu}>
            {running ? 'Running…' : 'Run AI'}
          </button>
          {showRunMenu && (
            <div className="run-ai-menu">
              <label>
                Batch size
                <input type="number" min="1" disabled={batchSize === 'all'} value={batchSize === 'all' ? '' : batchSize}
                  placeholder="All pending" onChange={event => setBatchSize(Math.max(1, Number(event.target.value) || 1))} />
              </label>
              <div className="batch-presets">
                {[10, 25, 50, 100].map(size => <button className={batchSize === size ? 'active' : ''} key={size} onClick={() => setBatchSize(size)}>{size}</button>)}
                <button className={batchSize === 'all' ? 'active' : ''} onClick={() => setBatchSize('all')}>All pending</button>
              </div>
              {models.length > 1 ? (
                <label>Model<select value={selectedModel} onChange={event => setSelectedModel(event.target.value)}>{models.map(model => <option disabled={model.available === false} key={model.id} value={model.id}>{model.label}{model.available === false ? ' (unavailable)' : ''}</option>)}</select></label>
              ) : models.length === 1 ? <p className="configured-model">Model: {models[0].label}{models[0].available === false ? ' (unavailable)' : ''}</p> : <p className="configured-model">Loading models…</p>}
              {models.find(model => model.id === selectedModel)?.error && <p className="model-error">{models.find(model => model.id === selectedModel)?.error}</p>}
              <button className="start-run" onClick={handleRunAI} disabled={!selectedModel || models.find(model => model.id === selectedModel)?.available === false}>Start</button>
            </div>
          )}
          </div>
          {runMessage && <span className="run-message" role="status">{runMessage}</span>}
          <button onClick={handleAutoApprove}>Auto-approve ≥95%</button>
          <a
            href={exportBase.replace('export?', 'export/json?')}
            className="btn"
            style={{ textDecoration: 'none', color: 'var(--ink)' }}
          >
            Export JSON
          </a>
          <a
            href={exportBase.replace('export?', 'export/csv?')}
            className="btn"
            style={{ textDecoration: 'none', color: 'var(--ink)' }}
          >
            Export CSV
          </a>
        </div>
      </div>

      {/* ── Status tabs ── */}
      <div className="tabs" role="tablist">
        {STATUS_TABS.map(s => (
          <button
            key={s}
            role="tab"
            aria-selected={s === status}
            className={s === status ? 'active' : ''}
            onClick={() => { setStatus(s); resetPage(); }}
          >
            {s.replace('_', ' ')}
          </button>
        ))}
      </div>

      {/* ── Filters ── */}
      <div className="filters">
        <input
          placeholder="Search caption, description, tags"
          value={search}
          onChange={e => { setSearch(e.target.value); resetPage(); }}
          onKeyDown={e => e.key === 'Enter' && resetPage()}
        />
        <input placeholder="Style"       value={style}    onChange={e => { setStyle(e.target.value); resetPage(); }} />
        <input placeholder="Tag"         value={tag}      onChange={e => { setTag(e.target.value); resetPage(); }} />
        <input placeholder="Reviewer"    value={reviewer} onChange={e => { setReviewer(e.target.value); resetPage(); }} />
        <input placeholder="Min conf"    value={minConf}  onChange={e => { setMinConf(e.target.value); resetPage(); }} style={{ maxWidth: 100 }} />
        <input placeholder="Max conf"    value={maxConf}  onChange={e => { setMaxConf(e.target.value); resetPage(); }} style={{ maxWidth: 100 }} />
        <button onClick={resetPage}>Filter</button>
      </div>

      {/* ── Image grid ── */}
      <p className="gallery-range">Showing {firstResult}–{lastResult} of {data.total}</p>
      {data.items.length === 0 ? (
        <p className="empty-state">No images match the current filters.</p>
      ) : (
        <div className="grid">
          {data.items.map(item => {
            const isSelected = selected.includes(item.image_id);
            return (
              <article className="card metadata-card" key={item.image_id} role="button" tabIndex={0}
                onClick={() => navigate(`/review/${item.image_id}`, { state: { imageIds: galleryIds } })}
                onKeyDown={event => {
                  if ((event.target as HTMLElement).tagName === 'INPUT') return;
                  if (event.key === 'Enter' || event.key === ' ') navigate(`/review/${item.image_id}`, { state: { imageIds: galleryIds } });
                }}>
                <div className="card-body">
                  <div className="card-top">
                    <div className="style-label"><span className="style-swatch" style={{ backgroundColor: styleColor(item.style || 'unknown') }} /><h3 title={item.style}>{item.style || '—'}</h3></div>
                    <span className={`badge ${item.annotation.status}`}>
                      {item.annotation.status}
                    </span>
                  </div>
                  <p className="card-id">{item.image_id}</p>
                  <p className="card-meta">
                    {item.annotation.confidence == null
                      ? 'Unannotated'
                      : `${Math.round(item.annotation.confidence * 100)}% confidence`}
                  </p>
                  <div className="card-actions">
                    <label className="card-select" title="Select image" onClick={event => event.stopPropagation()}>
                      <input checked={isSelected} onChange={() => toggleSelect(item.image_id)} type="checkbox" /> Select
                    </label>
                    <span className="review-link">Open →</span>
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      )}

      {totalPages > 1 && (
        <nav className="pagination" aria-label="Gallery pages">
          <button onClick={() => changePage(page - 1)} disabled={page === 1}>‹ Previous</button>
          {pageItems.map((item, index) => item === 'ellipsis' ? (
            <span className="pagination-ellipsis" key={`ellipsis-${index}`}>…</span>
          ) : (
            <button className={item === page ? 'active' : ''} aria-current={item === page ? 'page' : undefined} key={item} onClick={() => changePage(item)}>{item}</button>
          ))}
          <button onClick={() => changePage(page + 1)} disabled={page === totalPages}>Next ›</button>
        </nav>
      )}

      {/* ── Bulk action bar ── */}
      {selected.length > 0 && (
        <div className="bulk-bar" role="toolbar" aria-label="Bulk actions">
          <span>{selected.length} selected</span>
          <button onClick={handleBulkApprove}>Approve</button>
          <button onClick={handleBulkStyle}>Set Style</button>
          <button onClick={clearSelect} style={{ opacity: 0.6 }}>Clear</button>
        </div>
      )}
    </>
  );
}
