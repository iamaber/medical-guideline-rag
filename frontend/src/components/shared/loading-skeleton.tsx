'use client';

interface SkeletonProps {
  className?: string;
  height?: string;
  width?: string;
}

export function Skeleton({ className = '', height = 'h-12', width = 'full' }: SkeletonProps) {
  const shimmer = 'animate-shimmer';

  return (
    <div className={`${className} ${shimmer}`} style={{ height, width }}>
      <div className="animate-pulse">
        <div className="h-12 w-full flex items-center justify-center gap-4">
          <div className="w-8 h-8 bg-gradient-to-r from-slate-200 to-slate-100 animate-fade-in">
            <div className="h-4 w-4 bg-slate-300 rounded-full animate-scale-up" />
          </div>
        </div>
      </div>
    </div>
  );
}

export function CardSkeleton({ className = '', height = 'h-24' }: SkeletonProps) {
  return (
    <div className={`${className} animate-fade-in`} style={{ height }}>
      <div className="h-24 w-full bg-slate-200 dark:bg-slate-800 rounded-lg animate-fade-in">
        <div className="p-6 animate-pulse">
          <div className="h-4 w-full bg-slate-300 rounded-full animate-scale-up" />
        </div>
      </div>
    </div>
  );
}
