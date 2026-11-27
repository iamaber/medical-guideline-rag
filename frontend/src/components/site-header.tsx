'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';

const LINKS = [
  { href: '/consultation/', label: 'Consultation' },
  { href: '/drug-interaction/', label: 'Interactions' },
];

export function SiteHeader() {
  const pathname = usePathname();

  return (
    <header className="border-b">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between gap-4 px-6">
        <Link href="/" className="font-serif font-semibold tracking-tight whitespace-nowrap sm:text-lg">
          <span className="sm:hidden">Guideline RAG</span>
          <span className="hidden sm:inline">Medical Guideline RAG</span>
        </Link>
        <nav className="flex items-center gap-4 text-sm sm:gap-6">
          {LINKS.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              aria-current={pathname.startsWith(href) ? 'page' : undefined}
              className={cn(
                'text-muted-foreground hover:text-foreground',
                pathname.startsWith(href) && 'text-foreground underline decoration-primary decoration-2 underline-offset-[1.15rem]'
              )}
            >
              {label}
            </Link>
          ))}
          <a
            href="https://github.com/iamaber/medical-guideline-rag"
            className="hidden text-muted-foreground hover:text-foreground sm:inline"
          >
            GitHub
          </a>
        </nav>
      </div>
    </header>
  );
}
