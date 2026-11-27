'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { apiClient } from '@/lib/api';

interface IndexStats {
  passages: number;
  brands: number;
  drugs: number;
  pairs: number;
  model: string;
}

const STEPS = [
  {
    title: 'Brand to generic',
    body: 'Each brand is looked up on MedEx, so "Comet 500" is searched as metformin and its monograph goes to the model.',
  },
  {
    title: 'Retrieve evidence',
    body: "PubMed abstracts and WHO guidelines are searched with the drugs and the patient's conditions.",
  },
  {
    title: 'Write with citations',
    body: 'The model answers from that evidence only and puts a PMID next to each claim. When the evidence is silent, it says so.',
  },
  {
    title: 'Check it yourself',
    body: 'Every citation links to the article on PubMed.',
  },
];

function formatCount(value: number | undefined): string {
  return value ? value.toLocaleString('en-US') : '…';
}

export default function HomePage() {
  const [stats, setStats] = useState<IndexStats | null>(null);

  useEffect(() => {
    apiClient
      .getStats()
      .then(({ services }) => {
        const s = services as {
          vector_search?: { total_documents?: number };
          drug_database?: { total_drugs?: number };
          knowledge_graph?: { drug_nodes?: number; known_interactions?: number };
          llm_client?: { model?: string };
        };
        setStats({
          passages: s.vector_search?.total_documents ?? 0,
          brands: s.drug_database?.total_drugs ?? 0,
          drugs: s.knowledge_graph?.drug_nodes ?? 0,
          pairs: s.knowledge_graph?.known_interactions ?? 0,
          model: s.llm_client?.model ?? '',
        });
      })
      .catch((err) => console.error('Failed to load stats:', err));
  }, []);

  return (
    <div className="mx-auto max-w-6xl px-6">
      <section className="max-w-3xl py-16 md:py-24">
        <h1 className="font-serif text-4xl leading-tight font-semibold tracking-tight md:text-5xl">
          Medication advice that shows its sources.
        </h1>
        <p className="mt-6 text-lg leading-relaxed text-muted-foreground">
          Enter a patient&apos;s medicines by Bangladeshi brand or generic name, with dosing
          schedules, age and conditions. The answer cites the PubMed abstracts and drug monographs
          it used, and each citation links to the article.
        </p>
        <div className="mt-8 flex flex-wrap items-center gap-6">
          <Button asChild size="lg">
            <Link href="/consultation/">
              Start a consultation <ArrowRight />
            </Link>
          </Button>
          <Link
            href="/drug-interaction/"
            className="text-sm font-medium underline decoration-border underline-offset-4 hover:decoration-foreground"
          >
            Check two drugs for interactions
          </Link>
        </div>
      </section>

      <dl className="grid grid-cols-2 gap-y-6 border-y py-8 md:grid-cols-4">
        <div>
          <dt className="text-sm text-muted-foreground">Evidence passages</dt>
          <dd className="mt-1 font-serif text-2xl tabular-nums">{formatCount(stats?.passages)}</dd>
        </div>
        <div>
          <dt className="text-sm text-muted-foreground">Brand names mapped</dt>
          <dd className="mt-1 font-serif text-2xl tabular-nums">{formatCount(stats?.brands)}</dd>
        </div>
        <div>
          <dt className="text-sm text-muted-foreground">Interaction pairs</dt>
          <dd className="mt-1 font-serif text-2xl tabular-nums">
            {formatCount(stats?.pairs)}
            {stats ? (
              <span className="ml-2 font-sans text-sm text-muted-foreground">
                among {stats.drugs} drugs
              </span>
            ) : null}
          </dd>
        </div>
        <div>
          <dt className="text-sm text-muted-foreground">Model</dt>
          <dd className="mt-2 truncate font-mono text-sm">{stats?.model || '…'}</dd>
        </div>
      </dl>

      <section className="py-16">
        <h2 className="text-xs font-semibold tracking-[0.12em] text-muted-foreground uppercase">
          How an answer is made
        </h2>
        <ol className="mt-8 grid gap-x-10 gap-y-10 md:grid-cols-4">
          {STEPS.map((step, index) => (
            <li key={step.title}>
              <span className="font-serif text-3xl text-primary">{index + 1}</span>
              <h3 className="mt-3 font-medium">{step.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{step.body}</p>
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
