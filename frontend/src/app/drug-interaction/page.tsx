'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Plus, Trash2, AlertTriangle, Search, CheckCircle, XCircle, AlertCircle, Loader2 } from 'lucide-react';
import { apiClient } from '@/lib/api';

interface Drug {
  id: string;
  name: string;
  schedule?: string;
}

interface InteractionResult {
  medications: string[];
  severity: 'minor' | 'moderate' | 'major' | 'severe' | 'contraindicated';
  category: string;
  description: string;
  mechanism: string;
  clinical_significance: string;
  risk_factors: string[];
  monitoring_required: string[];
  management_strategy: string;
}

export default function DrugInteractionPage() {
  const [drugs, setDrugs] = useState<Drug[]>([]);
  const [searchResults, setSearchResults] = useState<string[]>([]);
  const [searchIndex, setSearchIndex] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [searching, setSearching] = useState(false);
  const [interactions, setInteractions] = useState<InteractionResult[]>([]);
  const [showProfessionalMode, setShowProfessionalMode] = useState(false);
  const [error, setError] = useState('');

  const addDrug = (name: string) => {
    if (!name || drugs.length >= 10) return;
    setDrugs([...drugs, { id: Date.now().toString(), name }]);
    setSearchResults([]);
    setSearchIndex(null);
    setError('');
  };

  const removeDrug = (id: string) => {
    setDrugs(drugs.filter(d => d.id !== id));
    setInteractions([]);
    setError('');
  };

  const handleSearch = async (query: string, index: number) => {
    if (query.length < 2) {
      setSearchResults([]);
      return;
    }

    setSearching(true);
    try {
      const result = await apiClient.searchDrugs(query, 10);
      setSearchResults(result.results);
      setSearchIndex(index);
    } catch (err: any) {
      console.error('Search failed:', err);
    } finally {
      setSearching(false);
    }
  };

  const checkInteractions = async () => {
    if (drugs.length < 2) {
      setError('Please add at least 2 medications to check for interactions');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/drug_interactions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          medications: drugs.map(d => d.name)
        })
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      setInteractions(data.data || []);
    } catch (err: any) {
      setError(err.message || 'Failed to check interactions. Please try again.');
      console.error('Interaction check failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    const colors = {
      minor: 'bg-blue-100 text-blue-700 border-blue-500',
      moderate: 'bg-amber-100 text-amber-700 border-amber-500',
      major: 'bg-orange-100 text-orange-700 border-orange-500',
      severe: 'bg-red-100 text-red-700 border-red-500',
      contraindicated: 'bg-red-200 text-red-900 border-red-700',
    };
    return colors[severity as keyof typeof colors] || colors.moderate;
  };

  const getSeverityIcon = (severity: string) => {
    const icons = {
      minor: <CheckCircle className="w-5 h-5" />,
      moderate: <AlertCircle className="w-5 h-5" />,
      major: <AlertTriangle className="w-5 h-5" />,
      severe: <XCircle className="w-5 h-5" />,
      contraindicated: <XCircle className="w-5 h-5" />,
    };
    return icons[severity as keyof typeof icons] || icons.moderate;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-slate-800 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-red-600 to-orange-600 bg-clip-text text-transparent animate-fade-in">
            Drug Interaction Checker
          </h1>
          <p className="text-slate-600 dark:text-slate-400 mt-2 animate-fade-in">
            Check for potential drug-drug interactions quickly and safely
          </p>
        </div>

        {/* Mode Toggle */}
        <Card className="mb-6 animate-slide-in">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div>
                <h3 className="font-semibold text-lg">View Mode</h3>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Choose how you want to see interaction information
                </p>
              </div>
              <div className="flex gap-2">
                <Button
                  variant={!showProfessionalMode ? 'default' : 'outline'}
                  onClick={() => setShowProfessionalMode(false)}
                  className="transition-all"
                >
                  Patient View
                </Button>
                <Button
                  variant={showProfessionalMode ? 'default' : 'outline'}
                  onClick={() => setShowProfessionalMode(true)}
                  className="transition-all"
                >
                  Professional View
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Drug Input Section */}
        <Card className="mb-6 animate-slide-in">
          <CardHeader>
            <CardTitle>Add Medications</CardTitle>
            <CardDescription>
              Add at least 2 medications to check for interactions
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {drugs.map((drug, index) => (
                <div key={drug.id} className="flex gap-2 items-start">
                  <div className="flex-1 relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                      value={drug.name}
                      onChange={(e) => {
                        const updated = [...drugs];
                        updated[index].name = e.target.value;
                        setDrugs(updated);
                        handleSearch(e.target.value, index);
                      }}
                      placeholder="Enter drug name..."
                      className="pl-10"
                      aria-label={`Drug ${index + 1} name`}
                    />
                    {searchIndex === index && searchResults.length > 0 && (
                      <div className="absolute z-50 w-full mt-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg shadow-lg max-h-60 overflow-y-auto animate-scale-up">
                        {searchResults.map((result, i) => (
                          <button
                            key={i}
                            onClick={() => addDrug(result)}
                            className="w-full text-left px-4 py-3 hover:bg-blue-50 dark:hover:bg-blue-900/30 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
                          >
                            {result}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                  <Button
                    variant="destructive"
                    size="icon"
                    onClick={() => removeDrug(drug.id)}
                    aria-label={`Remove drug ${index + 1}`}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              ))}

              <Button
                variant="outline"
                onClick={() => addDrug('')}
                disabled={drugs.length >= 10}
                className="w-full transition-all"
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Another Medication
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Error Alert */}
        {error && (
          <Alert variant="destructive" className="mb-6 animate-fade-in">
            <AlertTriangle className="w-4 h-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Check Interactions Button */}
        {drugs.length >= 2 && (
          <div className="mb-6 flex justify-center animate-scale-up">
            <Button
              size="lg"
              onClick={checkInteractions}
              disabled={loading}
              className="px-12 transition-all"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Checking...
                </span>
              ) : (
                'Check for Interactions'
              )}
            </Button>
          </div>
        )}

        {/* Results Section */}
        {interactions.length > 0 && (
          <div className="space-y-6 animate-fade-in">
            <h2 className="text-2xl font-bold">Interaction Results</h2>

            {interactions.map((interaction, index) => (
              <Card
                key={index}
                className={`border-l-4 animate-slide-in ${getSeverityColor(interaction.severity)}`}
              >
                <CardContent className="pt-6">
                  <div className="flex items-start gap-4 mb-4">
                    {getSeverityIcon(interaction.severity)}
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2 flex-wrap">
                        <h3 className="text-xl font-bold">
                          {interaction.medications.join(' + ')}
                        </h3>
                        <Badge variant="outline" className={`${getSeverityColor(interaction.severity)}`}>
                          {interaction.severity.toUpperCase()}
                        </Badge>
                      </div>
                      <p className="text-lg text-slate-700 dark:text-slate-300 mb-3">
                        {interaction.description}
                      </p>
                    </div>
                  </div>

                  {showProfessionalMode ? (
                    <ProfessionalView interaction={interaction} />
                  ) : (
                    <PatientView interaction={interaction} />
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {interactions.length === 0 && drugs.length >= 2 && !loading && (
          <Card className="border-l-4 border-l-green-500 animate-scale-up">
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <CheckCircle className="w-12 h-12 text-green-600" />
                <div>
                  <h3 className="text-2xl font-bold text-green-700 dark:text-green-400">
                    No Interactions Detected
                  </h3>
                  <p className="text-slate-600 dark:text-slate-400 mt-2">
                    Based on our current medical knowledge, these medications do not have known interactions.
                    However, always consult your healthcare provider for personalized advice.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Disclaimer */}
        <Alert className="mt-6 animate-fade-in">
          <AlertTriangle className="w-4 h-4" />
          <AlertDescription>
            <strong>Medical Disclaimer:</strong> This tool is for informational purposes only.
            It is not a substitute for professional medical advice. Always consult your
            healthcare provider or pharmacist before starting, stopping, or changing any medications.
          </AlertDescription>
        </Alert>
      </div>
    </div>
  );
}

function PatientView({ interaction }: { interaction: InteractionResult }) {
  return (
    <div className="space-y-4">
      <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg animate-fade-in">
        <h4 className="font-semibold mb-2">What This Means</h4>
        <p className="text-slate-700 dark:text-slate-300">
          {interaction.clinical_significance}
        </p>
      </div>

      <div className="bg-amber-50 dark:bg-amber-900/20 p-4 rounded-lg animate-fade-in">
        <h4 className="font-semibold mb-2">What To Do</h4>
        <p className="text-slate-700 dark:text-slate-300">
          {interaction.management_strategy}
        </p>
      </div>

      {interaction.monitoring_required.length > 0 && (
        <div className="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-lg animate-fade-in">
          <h4 className="font-semibold mb-2">Watch For</h4>
          <ul className="list-disc list-inside space-y-1">
            {interaction.monitoring_required.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      {interaction.risk_factors.length > 0 && (
        <div className="bg-red-50 dark:bg-red-900/20 p-4 rounded-lg animate-fade-in">
          <h4 className="font-semibold mb-2">Who's At Higher Risk</h4>
          <ul className="list-disc list-inside space-y-1">
            {interaction.risk_factors.map((factor, i) => (
              <li key={i}>{factor}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function ProfessionalView({ interaction }: { interaction: InteractionResult }) {
  return (
    <div className="space-y-4">
      <div className="bg-slate-50 dark:bg-slate-800 p-4 rounded-lg">
        <h4 className="font-semibold mb-2">Mechanism</h4>
        <p className="text-slate-700 dark:text-slate-300 font-mono text-sm">
          {interaction.mechanism}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-slate-50 dark:bg-slate-800 p-4 rounded-lg">
          <h4 className="font-semibold mb-2">Category</h4>
          <Badge variant="outline">{interaction.category}</Badge>
        </div>

        <div className="bg-slate-50 dark:bg-slate-800 p-4 rounded-lg">
          <h4 className="font-semibold mb-2">Clinical Significance</h4>
          <p className="text-sm">{interaction.clinical_significance}</p>
        </div>
      </div>

      {interaction.monitoring_required.length > 0 && (
        <div className="bg-slate-50 dark:bg-slate-800 p-4 rounded-lg">
          <h4 className="font-semibold mb-2">Monitoring Parameters</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {interaction.monitoring_required.map((param, i) => (
              <div key={i} className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-blue-600" />
                <span className="text-sm">{param}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {interaction.risk_factors.length > 0 && (
        <div className="bg-slate-50 dark:bg-slate-800 p-4 rounded-lg">
          <h4 className="font-semibold mb-2">Risk Factors</h4>
          <ul className="space-y-2">
            {interaction.risk_factors.map((factor, i) => (
              <li key={i} className="flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-600 mt-0.5" />
                <span className="text-sm">{factor}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
