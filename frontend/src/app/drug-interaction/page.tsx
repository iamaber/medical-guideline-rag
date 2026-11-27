'use client';

import { useRef, useState } from 'react';
import { Loader2, Plus, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { DrugNameInput } from '@/components/drug-name-input';
import { apiClient } from '@/lib/api';
import { useAdoptPreHydrationInput } from '@/lib/use-adopt-pre-hydration-input';
import { cn } from '@/lib/utils';

interface Drug {
  id: number;
  name: string;
}

interface CheckedDrug {
  name: string;
  generic_name: string | null;
  found_in_database: boolean;
  ingredients: string[];
}

type Severity = 'minor' | 'moderate' | 'major' | 'severe' | 'contraindicated';

interface InteractionResult {
  medications: string[];
  severity: Severity;
  category: string;
  description: string;
  mechanism: string;
  clinical_significance: string;
  risk_factors: string[];
  monitoring_required: string[];
  management_strategy: string;
}

interface InteractionResponse {
  data: InteractionResult[];
  checked: CheckedDrug[];
  known_interactions: number;
}

const MAX_DRUGS = 10;
const SEVERITY_STYLE: Record<Severity, string> = {
  minor: 'border-muted-foreground text-muted-foreground',
  moderate: 'border-warning text-warning',
  major: 'border-destructive text-destructive',
  severe: 'border-destructive text-destructive',
  contraindicated: 'border-destructive text-destructive',
};

let nextDrugId = 0;
const emptyDrug = (): Drug => ({ id: nextDrugId++, name: '' });

export default function DrugInteractionPage() {
  const [drugs, setDrugs] = useState<Drug[]>(() => [emptyDrug(), emptyDrug()]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<InteractionResponse | null>(null);
  const [error, setError] = useState('');
  const formRef = useRef<HTMLFormElement>(null);

  useAdoptPreHydrationInput(formRef, (id, value) => {
    const index = /^drug-name-(\d+)$/.exec(id)?.[1];
    if (index === undefined) return;
    setDrugs((current) => current.map((d, i) => (i === Number(index) ? { ...d, name: value } : d)));
  });

  const changeDrugs = (next: Drug[]) => {
    setDrugs(next);
    setResult(null);
    setError('');
  };

  const checkInteractions = async (event: React.FormEvent) => {
    event.preventDefault();
    const names = drugs.map((d) => d.name.trim()).filter(Boolean);
    if (names.length < 2) {
      setError('Enter at least two medications.');
      return;
    }

    setLoading(true);
    setResult(null);
    setError('');
    try {
      setResult(
        await apiClient.post<InteractionResponse>('/drug_interactions', { medications: names })
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to check interactions.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-3xl px-6 py-12 md:py-16">
      <h1 className="font-serif text-3xl font-semibold tracking-tight md:text-4xl">
        Interaction checker
      </h1>
      <p className="mt-3 text-muted-foreground">
        Checks every pair against a small, hand-curated list of known interactions. Brand names are
        matched to their active ingredients through MedEx.
      </p>

      <form ref={formRef} onSubmit={checkInteractions} noValidate className="mt-10 border-t pt-8">
        <ol className="grid gap-3">
          {drugs.map((drug, index) => (
            <li key={drug.id} className="grid grid-cols-[1.25rem_1fr_2rem] items-center gap-2">
              <span className="text-sm text-muted-foreground tabular-nums">{index + 1}</span>
              <DrugNameInput
                id={`drug-name-${index}`}
                label={`Drug ${index + 1} name`}
                value={drug.name}
                onChange={(name) =>
                  changeDrugs(drugs.map((d) => (d.id === drug.id ? { ...d, name } : d)))
                }
              />
              {drugs.length > 2 ? (
                <Button
                  type="button"
                  variant="ghost"
                  size="icon-sm"
                  onClick={() => changeDrugs(drugs.filter((d) => d.id !== drug.id))}
                  aria-label={`Remove drug ${index + 1}`}
                  className="text-muted-foreground"
                >
                  <X />
                </Button>
              ) : (
                <span />
              )}
            </li>
          ))}
        </ol>
        <Button
          type="button"
          variant="link"
          onClick={() => changeDrugs([...drugs, emptyDrug()])}
          disabled={drugs.length >= MAX_DRUGS}
          className="mt-3 h-auto px-0 pl-7"
        >
          <Plus /> Add medication
        </Button>

        <div className="mt-8 flex flex-wrap items-center gap-4">
          <Button type="submit" size="lg" disabled={loading}>
            {loading ? (
              <>
                <Loader2 className="animate-spin" /> Checking…
              </>
            ) : (
              'Check interactions'
            )}
          </Button>
          {error && (
            <p role="alert" className="text-sm text-destructive">
              {error}
            </p>
          )}
        </div>
      </form>

      {result && (
        <div className="mt-12 border-t pt-8">
          <h2 className="text-xs font-semibold tracking-[0.12em] text-muted-foreground uppercase">
            Checked as
          </h2>
          <dl className="mt-4 grid grid-cols-[minmax(0,12rem)_1fr] gap-x-6 gap-y-2 text-sm">
            {result.checked.map((drug, index) => (
              <div key={index} className="contents">
                <dt className="font-medium">{drug.name}</dt>
                <dd className="text-muted-foreground">
                  {drug.generic_name
                    ? `${drug.generic_name} (${drug.ingredients.join(', ')})`
                    : drug.found_in_database
                      ? 'MedEx page could not be read; checked by the name as entered'
                      : 'Not a MedEx brand; checked by the name as entered'}
                </dd>
              </div>
            ))}
          </dl>

          {result.data.length === 0 ? (
            <div className="mt-10 border-l-2 border-primary pl-5">
              <h2 className="font-serif text-xl font-semibold">No known interactions found</h2>
              <p className="mt-2 text-muted-foreground">
                None of the {result.known_interactions} interactions this checker knows about
                apply to these medications. The list is small and can miss real interactions, so
                ask a pharmacist or doctor before combining medications.
              </p>
            </div>
          ) : (
            result.data.map((interaction, index) => (
              <article
                key={index}
                className={cn('mt-10 border-l-2 pl-5', SEVERITY_STYLE[interaction.severity])}
              >
                <p className="text-xs font-semibold tracking-[0.12em] uppercase">
                  {interaction.severity} · {interaction.category}
                </p>
                <h2 className="mt-2 font-serif text-xl font-semibold text-foreground">
                  {interaction.medications.join(' + ')}
                </h2>
                <p className="mt-2 text-foreground">{interaction.description}</p>
                <dl className="mt-5 grid gap-4 text-sm text-foreground md:grid-cols-[9rem_1fr]">
                  <dt className="font-medium">What to do</dt>
                  <dd>{interaction.management_strategy}</dd>
                  <dt className="font-medium">Why it matters</dt>
                  <dd>{interaction.clinical_significance}</dd>
                  <dt className="font-medium">Mechanism</dt>
                  <dd>{interaction.mechanism}</dd>
                  {interaction.monitoring_required.length > 0 && (
                    <>
                      <dt className="font-medium">Monitor</dt>
                      <dd>{interaction.monitoring_required.join(', ')}</dd>
                    </>
                  )}
                  {interaction.risk_factors.length > 0 && (
                    <>
                      <dt className="font-medium">Higher risk</dt>
                      <dd>{interaction.risk_factors.join('; ')}</dd>
                    </>
                  )}
                </dl>
              </article>
            ))
          )}
        </div>
      )}
    </div>
  );
}
