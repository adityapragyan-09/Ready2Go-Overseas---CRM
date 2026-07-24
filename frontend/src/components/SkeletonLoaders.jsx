/**
 * Enterprise Skeleton Loading Components
 * Provides skeleton placeholders for all major views.
 */

export function SkeletonCard({ className = '' }) {
  return (
    <div className={`card-brand p-5 space-y-4 ${className}`}>
      <div className="skeleton h-4 w-3/4" />
      <div className="skeleton h-8 w-1/2" />
      <div className="space-y-2">
        <div className="skeleton h-3 w-full" />
        <div className="skeleton h-3 w-2/3" />
      </div>
    </div>
  );
}

export function SkeletonTable({ rows = 5, cols = 5 }) {
  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex gap-4 mb-4">
        {Array.from({ length: cols }).map((_, i) => (
          <div key={i} className="skeleton h-4 flex-1" />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} className="flex gap-4 py-3 border-b" style={{ borderColor: 'var(--border-light)' }}>
          {Array.from({ length: cols }).map((_, c) => (
            <div key={c} className="skeleton h-3 flex-1" style={{ width: `${60 + Math.random() * 40}%` }} />
          ))}
        </div>
      ))}
    </div>
  );
}

export function SkeletonStats() {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="card-brand p-5 space-y-3">
          <div className="flex justify-between items-start">
            <div className="space-y-2">
              <div className="skeleton h-3 w-20" />
              <div className="skeleton h-8 w-16" />
            </div>
            <div className="skeleton h-10 w-10 rounded-2xl" />
          </div>
          <div className="skeleton h-3 w-32" />
        </div>
      ))}
    </div>
  );
}

export function SkeletonChart() {
  return (
    <div className="card-brand p-5 space-y-4">
      <div className="skeleton h-5 w-48" />
      <div className="skeleton h-3 w-64" />
      <div className="skeleton h-48 w-full mt-4" />
    </div>
  );
}

export function SkeletonList({ items = 4 }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: items }).map((_, i) => (
        <div key={i} className="card-brand p-4 flex items-center gap-4">
          <div className="skeleton h-10 w-10 rounded-full shrink-0" />
          <div className="flex-1 space-y-2">
            <div className="skeleton h-4 w-1/3" />
            <div className="skeleton h-3 w-2/3" />
          </div>
          <div className="skeleton h-6 w-16 rounded-lg" />
        </div>
      ))}
    </div>
  );
}
