'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ThemeToggle } from '@/components/shared/theme-toggle';
import { Search, Plus, XCircle, FileText } from 'lucide-react';
import { apiClient, type UserInput, type AdviceResponse } from '@/lib/api';

interface Medication {
  name: string;
  schedule: string;
}

interface PatientInfo {
  age: string;
  gender: 'M' | 'F' | '';
  symptoms: string;
  conditions: string;
}

export default function ConsultationPage() {
  const [patientInfo, setPatientInfo] = useState<PatientInfo>({
    age: '',
    gender: '',
    symptoms: '',
    conditions: '',
  });

  const [medications, setMedications] = useState<Medication[]>([
    { name: '', schedule: '1+0+1' }
  ]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [results, setResults] = useState<AdviceResponse | null>(null);
  const [searchResults, setSearchResults] = useState<string[]>([]);
  const [searchIndex, setSearchIndex] = useState<number | null>(null);

  const schedulePresets = ['1+0+1', '1+1+1', '1+1+0', '1+0+0', '0+0+1', '0+1+0', '0+1+1'];

  const addMedication = () => {
    if (medications.length >= 10) return;
    setMedications([...medications, { name: '', schedule: '1+0+1' }]);
    setSearchResults([]);
    setSearchIndex(null);
    setError('');
  };

  const removeMedication = (index: number) => {
    setMedications(medications.filter((_, i) => i !== index));
    setError('');
  };

  const updateMedication = (index: number, field: keyof Medication, value: string) => {
    const updated = [...medications];
    updated[index][field] = value;
    setMedications(updated);
  };

  const handleSearch = async (query: string, index: number) => {
    if (query.length < 2) {
      setSearchResults([]);
      return;
    }

    try {
      const result = await apiClient.searchDrugs(query, 10);
      setSearchResults(result.results);
      setSearchIndex(index);
    } catch (err) {
      console.error('Search failed:', err);
    }
  };

  const validateForm = (): boolean => {
    if (!patientInfo.age || !patientInfo.gender) {
      setError('Please fill in patient age and gender');
      return false;
    }

    const age = parseInt(patientInfo.age);
    if (isNaN(age) || age < 1 || age > 120) {
      setError('Please enter a valid age between 1 and 120');
      return false;
    }

    for (const med of medications) {
      if (!med.name.trim()) {
        setError('Please fill in all medication names');
        return false;
      }
    }

    setError('');
    return true;
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setError('');

    try {
      const userInput: UserInput = {
        meds: medications.map(m => m.name.trim()),
        schedule: medications.map(m => m.schedule),
        age: parseInt(patientInfo.age),
        gender: patientInfo.gender,
      };

      const response = await apiClient.getMedicationAdvice(userInput);
      setResults(response);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to generate medication advice';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setPatientInfo({ age: '', gender: '', symptoms: '', conditions: '' });
    setMedications([{ name: '', schedule: '1+0+1' }]);
    setResults(null);
    setError('');
  };

  if (results) {
    return <ResultsView results={results} onReset={handleReset} />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-slate-800 p-6">
      <div className="max-w-4xl mx-auto">
        <header className="mb-8">
          <div className="flex justify-between items-center">
            <div>
              <Link href="/">
                <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent cursor-pointer hover:underline">
                  Medical Guideline RAG System
                </h1>
              </Link>
              <p className="text-slate-600 dark:text-slate-400 mt-2">
                AI-powered medication advisor using evidence-based medical literature
              </p>
            </div>
            <ThemeToggle />
          </div>
        </header>

        {error && (
          <Alert variant="destructive" className="mb-6 animate-fade-in">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="grid gap-6">
          <Card className="animate-slide-in">
            <CardHeader>
              <CardTitle>Patient Information</CardTitle>
              <CardDescription>
                Please provide patient details for personalized recommendations
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="age">Age</Label>
                  <Input
                    id="age"
                    type="number"
                    placeholder="Enter age (1-120)"
                    value={patientInfo.age}
                    onChange={(e) => setPatientInfo({ ...patientInfo, age: e.target.value })}
                    min={1}
                    max={120}
                    className="text-lg"
                  />
                </div>
                <div>
                  <Label htmlFor="gender">Gender</Label>
                  <select
                    id="gender"
                    value={patientInfo.gender}
                    onChange={(e) => setPatientInfo({ ...patientInfo, gender: e.target.value as 'M' | 'F' })}
                    className="w-full px-4 py-3 border rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-blue-500 outline-none"
                  >
                    <option value="">Select gender</option>
                    <option value="M">Male</option>
                    <option value="F">Female</option>
                  </select>
                </div>
              </div>
              <div className="md:col-span-2">
                <Label htmlFor="symptoms">Current Symptoms (Optional)</Label>
                <Input
                  id="symptoms"
                  placeholder="Describe any current symptoms"
                  value={patientInfo.symptoms}
                  onChange={(e) => setPatientInfo({ ...patientInfo, symptoms: e.target.value })}
                  className="text-lg"
                />
              </div>
              <div className="md:col-span-2">
                <Label htmlFor="conditions">Medical Conditions (Optional)</Label>
                <Input
                  id="conditions"
                  placeholder="Enter any existing medical conditions"
                  value={patientInfo.conditions}
                  onChange={(e) => setPatientInfo({ ...patientInfo, conditions: e.target.value })}
                  className="text-lg"
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Medications</CardTitle>
              <CardDescription>
                Add medications and their dosing schedules (max 10)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {medications.map((med, index) => (
                  <div key={index} className="grid grid-cols-1 md:grid-cols-12 gap-4 items-start p-4 border rounded-lg bg-slate-50 dark:bg-slate-800 animate-fade-in">
                    <div className="md:col-span-2 flex items-center">
                      <span className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-blue-600 text-white font-semibold">
                        {index + 1}
                      </span>
                    </div>
                    <div className="md:col-span-6 relative">
                      <Label htmlFor={`med-name-${index}`} className="sr-only">
                        Medication Name
                      </Label>
                      <Input
                        id={`med-name-${index}`}
                        placeholder="Enter medication name"
                        value={med.name}
                        onChange={(e) => updateMedication(index, 'name', e.target.value)}
                        onFocus={() => setSearchIndex(index)}
                        className="pr-10 text-lg"
                      />
                      {searchIndex === index && searchResults.length > 0 && (
                        <div className="absolute z-50 w-full mt-2 bg-white dark:bg-slate-900 border rounded-lg shadow-lg max-h-60 overflow-y-auto">
                          {searchResults.map((result, i) => (
                            <button
                              key={i}
                              onClick={() => {
                                updateMedication(index, 'name', result);
                                setSearchResults([]);
                                setSearchIndex(null);
                              }}
                              className="w-full text-left px-4 py-3 hover:bg-blue-50 dark:hover:bg-slate-700 transition-colors focus:bg-blue-100 focus:outline-none"
                            >
                              {result}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                    <div className="md:col-span-3">
                      <Label htmlFor={`med-schedule-${index}`} className="sr-only">
                        Dosing Schedule
                      </Label>
                      <select
                        id={`med-schedule-${index}`}
                        value={med.schedule}
                        onChange={(e) => updateMedication(index, 'schedule', e.target.value)}
                        className="w-full px-4 py-3 border rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-blue-500 outline-none appearance-none cursor-pointer"
                      >
                        {schedulePresets.map(preset => (
                          <option key={preset} value={preset}>{preset}</option>
                        ))}
                      </select>
                    </div>
                    <div className="md:col-span-1 flex items-start pt-8">
                      {medications.length > 1 && (
                        <Button
                          variant="destructive"
                          size="icon"
                          onClick={() => removeMedication(index)}
                          aria-label={`Remove medication ${index + 1}`}
                          className="shrink-0"
                        >
                          <XCircle className="w-5 h-5" />
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
                <Button
                  variant="outline"
                  onClick={addMedication}
                  disabled={medications.length >= 10}
                  className="w-full text-lg py-3"
                >
                  <Plus className="w-5 h-5 mr-2" />
                  Add Another Medication
                </Button>
              </div>
            </CardContent>
          </Card>

          <div className="flex gap-4">
            <Button
              onClick={handleSubmit}
              disabled={loading || medications.length === 0}
              size="lg"
              className="flex-1"
            >
              {loading ? (
                <span className="flex items-center">
                  <FileText className="w-4 h-4 mr-2 animate-spin" />
                  Processing...
                </span>
              ) : (
                <>
                  <Search className="w-4 h-4 mr-2" />
                  Generate Medication Advice
                </>
              )}
            </Button>
            <Button
              variant="outline"
              onClick={handleReset}
              disabled={loading}
              size="lg"
            >
              Reset Form
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

interface ResultsViewProps {
  results: AdviceResponse;
  onReset: () => void;
}

function ResultsView({ results, onReset }: ResultsViewProps) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-50 dark:from-slate-900 dark:to-slate-800 p-6 animate-fade-in">
      <div className="max-w-5xl mx-auto">
        <div className="mb-6 flex justify-between items-center flex-wrap gap-4">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
              Medication Consultation Results
            </h1>
            <p className="text-slate-600 dark:text-slate-400">
              Generated on {new Date().toLocaleDateString()} at {new Date().toLocaleTimeString()}
            </p>
          </div>
          <Button onClick={onReset} variant="outline" size="lg">
            Back to Form
          </Button>
        </div>

        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="prose max-w-none text-slate-900 dark:text-slate-100">
              <div dangerouslySetInnerHTML={{ __html: results.advice || 'No advice available' }} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Consultation Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4">
              <div className="flex justify-between">
                <span className="text-slate-600 dark:text-slate-400">Medications Processed:</span>
                <span className="font-bold text-slate-900 dark:text-white">{results.medications_processed}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600 dark:text-slate-400">Medications Found in Database:</span>
                <span className="font-bold text-slate-900 dark:text-white">{results.medications_found}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600 dark:text-slate-400">PubMed Articles Referenced:</span>
                <span className="font-bold text-slate-900 dark:text-white">{results.pubmed_articles}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600 dark:text-slate-400">Drug Interactions Found:</span>
                <span className="font-bold text-slate-900 dark:text-white">{results.drug_interactions_found}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600 dark:text-slate-400">Interaction Warnings:</span>
                <span className="font-bold text-slate-900 dark:text-white">{results.interaction_warnings}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Evidence Sources</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {results.context_sources?.slice(0, 5).map((source, index) => (
                <div key={index} className="p-4 border rounded-lg bg-slate-50 dark:bg-slate-800 hover:border-slate-300 transition-all">
                  <h3 className="font-semibold mb-2 text-slate-900 dark:text-white">{source.title}</h3>
                  <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">Source: {source.source}</p>
                  <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">Year: {source.publication_year || 'N/A'}</p>
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-500 font-semibold"
                  >
                    <FileText className="w-4 h-4 mr-2" />
                    View Article
                  </a>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <div className="mt-8 p-4 bg-amber-50 dark:bg-amber-900 border border-amber-200 dark:border-amber-800 rounded-lg text-center">
          <p className="text-sm text-amber-800 dark:text-amber-200">
            <strong>Medical Disclaimer:</strong> This information is for educational purposes only.
            Always consult your healthcare provider before making any changes to your medication regimen.
          </p>
        </div>
      </div>
    </div>
  );
}
