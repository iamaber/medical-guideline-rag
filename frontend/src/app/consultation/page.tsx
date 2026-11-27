'use client';

import { useState } from 'react';
import dynamic from 'next/dynamic';
import { Loader2, Plus, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { DrugNameInput } from '@/components/drug-name-input';
import { apiClient, type UserInput, type AdviceResponse } from '@/lib/api';

// Markdown rendering pulls in ~170 KB of parser code that is only needed once
// an answer exists, so it stays out of the initial page bundle.
const ResultsView = dynamic(() => import('@/components/consultation/results-view'));

const MAX_MEDICATIONS = 10;
const SCHEDULES = ['1+0+1', '1+1+1', '1+1+0', '1+0+0', '0+0+1', '0+1+0', '0+1+1'];

interface Medication {
  id: number;
  name: string;
  schedule: string;
}

let nextMedicationId = 0;
const newMedication = (): Medication => ({ id: nextMedicationId++, name: '', schedule: '1+0+1' });

const fieldLabel = 'mb-1.5 block text-sm font-medium';

export default function ConsultationPage() {
  const [age, setAge] = useState('');
  const [gender, setGender] = useState<'M' | 'F' | ''>('');
  const [conditions, setConditions] = useState('');
  const [medications, setMedications] = useState<Medication[]>(() => [newMedication()]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [results, setResults] = useState<AdviceResponse | null>(null);
  const [submitted, setSubmitted] = useState<UserInput | null>(null);

  const updateMedication = (id: number, change: Partial<Medication>) => {
    setMedications((current) => current.map((m) => (m.id === id ? { ...m, ...change } : m)));
  };

  const validationError = (): string => {
    const parsedAge = Number(age);
    if (!age || !Number.isInteger(parsedAge) || parsedAge < 1 || parsedAge > 120) {
      return 'Enter an age between 1 and 120.';
    }
    if (!gender) return 'Choose a gender.';
    if (medications.some((m) => !m.name.trim())) return 'Fill in every medication name, or remove the empty row.';
    return '';
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    const problem = validationError();
    setError(problem);
    if (problem || !gender) return;

    const userInput: UserInput = {
      meds: medications.map((m) => m.name.trim()),
      schedule: medications.map((m) => m.schedule),
      age: Number(age),
      gender,
      conditions: conditions
        .split(',')
        .map((condition) => condition.trim())
        .filter(Boolean)
        .slice(0, 10),
    };

    setLoading(true);
    try {
      setResults(await apiClient.getMedicationAdvice(userInput));
      setSubmitted(userInput);
      window.scrollTo(0, 0);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate medication advice.');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setAge('');
    setGender('');
    setConditions('');
    setMedications([newMedication()]);
    setError('');
  };

  if (results && submitted) {
    return (
      <ResultsView
        results={results}
        input={submitted}
        onEdit={() => {
          setResults(null);
          window.scrollTo(0, 0);
        }}
      />
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-6 py-12 md:py-16">
      <h1 className="font-serif text-3xl font-semibold tracking-tight md:text-4xl">New consultation</h1>
      <p className="mt-3 text-muted-foreground">
        The advice is written from retrieved PubMed and WHO evidence and cites it. It takes 5 to 20
        seconds.
      </p>

      <form onSubmit={handleSubmit} noValidate className="mt-10">
        <section className="grid gap-6 border-t py-8 md:grid-cols-[10rem_1fr]">
          <h2 className="text-sm font-semibold">Patient</h2>
          <div className="grid gap-5">
            <div className="flex flex-wrap gap-5">
              <div>
                <label htmlFor="age" className={fieldLabel}>
                  Age
                </label>
                <Input
                  id="age"
                  type="number"
                  inputMode="numeric"
                  min={1}
                  max={120}
                  value={age}
                  onChange={(e) => setAge(e.target.value)}
                  className="w-24"
                />
              </div>
              <div>
                <label htmlFor="gender" className={fieldLabel}>
                  Gender
                </label>
                <select
                  id="gender"
                  value={gender}
                  onChange={(e) => setGender(e.target.value as 'M' | 'F' | '')}
                  className="w-36"
                >
                  <option value="">Choose…</option>
                  <option value="M">Male</option>
                  <option value="F">Female</option>
                </select>
              </div>
            </div>
            <div>
              <label htmlFor="conditions" className={fieldLabel}>
                Conditions
              </label>
              <Input
                id="conditions"
                placeholder="type 2 diabetes, hypertension"
                value={conditions}
                onChange={(e) => setConditions(e.target.value)}
              />
              <p className="mt-1.5 text-xs text-muted-foreground">Optional. Separate with commas.</p>
            </div>
          </div>
        </section>

        <section className="grid gap-6 border-t py-8 md:grid-cols-[10rem_1fr]">
          <div>
            <h2 className="text-sm font-semibold">Medications</h2>
            <p className="mt-1 text-xs text-muted-foreground">
              Schedule is morning + noon + night.
            </p>
          </div>
          <div>
            <ol className="grid gap-3">
              {medications.map((med, index) => (
                <li key={med.id} className="grid grid-cols-[1.25rem_1fr_6.5rem_2rem] items-center gap-2">
                  <span className="text-sm text-muted-foreground tabular-nums">{index + 1}</span>
                  <DrugNameInput
                    id={`med-name-${index}`}
                    label={`Medication ${index + 1}`}
                    value={med.name}
                    onChange={(name) => updateMedication(med.id, { name })}
                  />
                  <select
                    id={`med-schedule-${index}`}
                    aria-label={`Schedule for medication ${index + 1}`}
                    value={med.schedule}
                    onChange={(e) => updateMedication(med.id, { schedule: e.target.value })}
                    className="font-mono"
                  >
                    {SCHEDULES.map((preset) => (
                      <option key={preset} value={preset}>
                        {preset}
                      </option>
                    ))}
                  </select>
                  {medications.length > 1 ? (
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon-sm"
                      onClick={() => setMedications(medications.filter((m) => m.id !== med.id))}
                      aria-label={`Remove medication ${index + 1}`}
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
              onClick={() => setMedications([...medications, newMedication()])}
              disabled={medications.length >= MAX_MEDICATIONS}
              className="mt-3 h-auto px-0 pl-7"
            >
              <Plus /> Add medication
            </Button>
          </div>
        </section>

        <div className="flex flex-wrap items-center gap-4 border-t pt-8">
          <Button type="submit" size="lg" disabled={loading}>
            {loading ? (
              <>
                <Loader2 className="animate-spin" /> Writing advice…
              </>
            ) : (
              'Generate advice'
            )}
          </Button>
          <Button type="button" variant="ghost" size="lg" onClick={handleReset} disabled={loading}>
            Clear
          </Button>
          {error && (
            <p role="alert" className="text-sm text-destructive">
              {error}
            </p>
          )}
        </div>
      </form>
    </div>
  );
}
