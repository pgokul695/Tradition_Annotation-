import { useEffect, useState } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { get, imageUrl, patch, post } from '../api/client';

const TAG_FIELDS = [
  'objects', 'animals', 'people', 'colors', 'patterns', 'religious_elements',
] as const;

const META_FIELDS = [
  'artist', 'year', 'region', 'license', 'source_url', 'title',
] as const;

type HistoryEntry = {
  id: number;
  field: string;
  old_value: string;
  new_value: string;
  changed_by: string;
  changed_at: string;
};

type ImageData = {
  image_id: string;
  style: string;
  local_path: string;
  artist?: string;
  year?: string;
  region?: string;
  license?: string;
  source_url?: string;
  title?: string;
  annotation: Record<string, any>;
  history?: HistoryEntry[];
};
type ReviewNavigation = { imageIds?: string[] };

export default function Review() {
  const { id } = useParams<{ id: string }>();
  const nav = useNavigate();
  const location = useLocation();
  const imageIds = (location.state as ReviewNavigation | null)?.imageIds ?? [];
  const currentIndex = id ? imageIds.indexOf(id) : -1;
  const previousId = currentIndex > 0 ? imageIds[currentIndex - 1] : undefined;
  const nextId = currentIndex >= 0 && currentIndex < imageIds.length - 1 ? imageIds[currentIndex + 1] : undefined;
  const [image, setImage] = useState<ImageData>();
  const [form, setForm] = useState<Record<string, any>>({});
  const [saving, setSaving] = useState(false);

  const load = () =>
    get('/images/' + id).then((x: ImageData) => {
      setImage(x);
      setForm(x.annotation ?? {});
    });

  useEffect(() => { load(); }, [id]); // eslint-disable-line

  const move = (targetId?: string) => {
    if (targetId) nav(`/review/${targetId}`, { state: { imageIds } });
  };

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const element = event.target as HTMLElement;
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes(element.tagName)) return;
      if (event.key === 'ArrowLeft') move(previousId);
      if (event.key === 'ArrowRight') move(nextId);
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [previousId, nextId, id]); // eslint-disable-line

  if (!image) {
    return <p className="loading-text">Loading image…</p>;
  }

  const change = (key: string, value: any) =>
    setForm(f => ({ ...f, [key]: value }));

  const save = async () => {
    setSaving(true);
    await patch('/images/' + id, { ...form, reviewed_by: 'reviewer' });
    await load();
    setSaving(false);
  };

  const approve = async () => {
    await post(`/images/${id}/approve`);
    nav('/gallery');
  };

  const reject = async () => {
    await post(`/images/${id}/reject`);
    nav('/gallery');
  };

  const lowConf = form.confidence != null && form.confidence < 0.8;

  return (
    <>
      <div className="page-title">
        <div>
          <p className="eyebrow">{image.image_id}</p>
          <h2>{form.style || image.style || 'Untitled'}</h2>
        </div>
        <div className="actions">
          {imageIds.length > 0 && <span className="image-position">{currentIndex + 1} / {imageIds.length}</span>}
          <button onClick={() => move(previousId)} disabled={!previousId}>← Previous</button>
          <button onClick={() => move(nextId)} disabled={!nextId}>Next →</button>
          <button onClick={save} disabled={saving}>
            {saving ? 'Saving…' : 'Save'}
          </button>
          <button className="btn-primary" onClick={approve}>Approve</button>
          <button className="btn-danger"  onClick={reject}>Reject</button>
        </div>
      </div>

      {/* Low confidence warning */}
      {lowConf && (
        <div className="confidence-warning">
          <span>⚠</span>
          <span>
            AI confidence is <strong>{Math.round(form.confidence * 100)}%</strong> — below the 80% threshold. Review carefully before approving.
          </span>
        </div>
      )}

      <div className="review">
        {/* ── Left: image + metadata ── */}
        <aside className="review-aside">
          <img
            className="hero"
            src={imageUrl(image.local_path)}
            alt={image.title || image.style}
          />

          <div className="metadata-grid">
            <h3>Source Metadata</h3>
            {META_FIELDS.map(key => (
              <div className="metadata-row" key={key}>
                <div className="metadata-key">{key.replace('_', ' ')}</div>
                <div className="metadata-val">
                  {image[key]
                    ? (key === 'source_url'
                        ? <a href={image[key]} target="_blank" rel="noreferrer">{image[key]}</a>
                        : image[key])
                    : <span style={{ color: 'var(--ink-muted)' }}>—</span>
                  }
                </div>
              </div>
            ))}
          </div>
        </aside>

        {/* ── Right: annotation form ── */}
        <section className="form">
          <label>
            Style
            <input
              value={form.style || ''}
              onChange={e => change('style', e.target.value)}
              onBlur={save}
            />
          </label>

          {TAG_FIELDS.map(key => (
            <label key={key}>
              {key.replace('_', ' ')}
              <input
                value={(form[key] || []).join(', ')}
                onChange={e =>
                  change(key, e.target.value.split(',').map((x: string) => x.trim()).filter(Boolean))
                }
                onBlur={save}
              />
            </label>
          ))}

          <label>
            Scene
            <textarea
              value={form.scene || ''}
              onChange={e => change('scene', e.target.value)}
              onBlur={save}
            />
          </label>

          <label>
            Caption
            <textarea
              value={form.caption || ''}
              onChange={e => change('caption', e.target.value)}
              onBlur={save}
            />
          </label>

          <label>
            Description
            <textarea
              rows={8}
              value={form.description || ''}
              onChange={e => change('description', e.target.value)}
              onBlur={save}
            />
          </label>

          <label>
            AI Confidence
            <input readOnly value={form.confidence != null ? `${Math.round(form.confidence * 100)}%` : '—'} />
          </label>

          {/* ── History ── */}
          <details className="history-details">
            <summary>AI vs Human history</summary>
            {image.history && image.history.length > 0 ? (
              <ul>
                {image.history.map(h => (
                  <li key={h.id}>
                    <b>{h.field}</b>
                    <span style={{ color: 'var(--ink-muted)' }}>{h.old_value || '∅'} → {h.new_value}</span>
                    <small>({h.changed_by})</small>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="history-empty">No edits yet.</p>
            )}
          </details>
        </section>
      </div>
    </>
  );
}
