'use client';

import ReactMarkdown from 'react-markdown';
import rehypeSanitize from 'rehype-sanitize';
import remarkGfm from 'remark-gfm';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import type { AdviceResponse, UserInput } from '@/lib/api';

const PUBMED_CITATION = /PMID:\s?(\d+)/g;
const PUBMED_URL_ID = /pubmed\.ncbi\.nlm\.nih\.gov\/(\d+)/;

function linkPubMedCitations(advice: string): string {
  return advice.replace(
    PUBMED_CITATION,
    (label, pmid) => `[${label}](https://pubmed.ncbi.nlm.nih.gov/${pmid}/)`
  );
}

interface ResultsViewProps {
  results: AdviceResponse;
  input: UserInput;
  onEdit: () => void;
}

export default function ResultsView({ results, input, onEdit }: ResultsViewProps) {
  const sources = results.context_sources?.slice(0, 5) ?? [];
  const patient = [
    `${input.age} years`,
    input.gender === 'M' ? 'male' : 'female',
    ...(input.conditions ?? []),
  ].join(', ');
  const summary: [string, string | number][] = [
    ['Found on MedEx', `${results.medications_found} of ${results.medications_processed}`],
    ['PubMed articles', results.pubmed_articles],
    ['Known interactions', results.drug_interactions_found],
    ['Interaction warnings', results.interaction_warnings],
  ];

  return (
    <div className="mx-auto max-w-6xl px-6 py-10 md:py-14">
      <Button variant="link" onClick={onEdit} className="h-auto px-0 text-muted-foreground">
        <ArrowLeft /> Edit consultation
      </Button>

      <header className="mt-6 border-b pb-8">
        <h1 className="font-serif text-3xl font-semibold tracking-tight md:text-4xl">
          Medication advice
        </h1>
        <p className="mt-3 text-muted-foreground">{patient}</p>
        <ul className="mt-4 flex flex-wrap gap-x-6 gap-y-1 text-sm">
          {input.meds.map((name, index) => (
            <li key={index}>
              {name} <span className="font-mono text-muted-foreground">{input.schedule[index]}</span>
            </li>
          ))}
        </ul>
      </header>

      {results.advice_source === 'fallback' && (
        <p className="mt-8 border-l-2 border-warning pl-4 text-sm">
          <strong>AI guidance unavailable.</strong> The text below is a fixed safety notice, not
          generated medical advice
          {results.missing_configuration?.length
            ? ` (missing: ${results.missing_configuration.join(', ')})`
            : ''}
          .
        </p>
      )}

      <div className="mt-10 grid gap-14 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <article className="advice max-w-[68ch]">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeSanitize]}
            components={{
              a: ({ href, children }) => (
                <a href={href} target="_blank" rel="noopener noreferrer">
                  {children}
                </a>
              ),
            }}
          >
            {linkPubMedCitations(results.advice || 'No advice available.')}
          </ReactMarkdown>
        </article>

        <aside className="lg:sticky lg:top-8 lg:self-start">
          <h2 className="text-xs font-semibold tracking-[0.12em] text-muted-foreground uppercase">
            Evidence sources
          </h2>
          {sources.length ? (
            <ol className="mt-4 divide-y">
              {sources.map((source, index) => {
                const pmid = source.url?.match(PUBMED_URL_ID)?.[1];
                const year = source.publication_year && source.publication_year !== 'N/A'
                  ? source.publication_year
                  : null;
                return (
                  <li key={index} className="grid grid-cols-[1.25rem_1fr] gap-2 py-3 text-sm">
                    <span className="text-muted-foreground tabular-nums">{index + 1}</span>
                    <div>
                      {source.url ? (
                        <a
                          href={source.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="leading-snug hover:underline"
                        >
                          {source.title}
                        </a>
                      ) : (
                        <span className="leading-snug">{source.title}</span>
                      )}
                      <p className="mt-1 text-xs text-muted-foreground">
                        {pmid ? `PMID ${pmid}` : source.source}
                        {year ? ` · ${year}` : ''}
                      </p>
                    </div>
                  </li>
                );
              })}
            </ol>
          ) : (
            <p className="mt-4 text-sm text-muted-foreground">No sources were retrieved.</p>
          )}

          <dl className="mt-8 grid grid-cols-[1fr_auto] gap-x-4 gap-y-2 border-t pt-6 text-sm">
            {summary.map(([label, value]) => (
              <div key={label} className="contents">
                <dt className="text-muted-foreground">{label}</dt>
                <dd className="text-right tabular-nums">{value}</dd>
              </div>
            ))}
          </dl>
        </aside>
      </div>
    </div>
  );
}
