'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { apiClient, type UserInput } from '@/lib/api';

interface Medication {
  name: string;
  schedule: string;
}

export default function Home() {
  const [patientInfo, setPatientInfo] = useState({
    age: '',
    gender: '' as 'M' | 'F' | '',
    symptoms: '',
    conditions: '',
  });

  const [medications, setMedications] = useState<Medication[]>([
    { name: '', schedule: '1+0+1' }
  ]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [results, setResults] = useState<any>(null);

  const addMedication = () => {
    setMedications([...medications, { name: '', schedule: '1+0+1' }]);
  };

  const removeMedication = (index: number) => {
    if (medications.length > 1) {
      setMedications(medications.filter((_, i) => i !== index));
    }
  };

  const updateMedication = (index: number, field: keyof Medication, value: string) => {
    const updated = [...medications];
    updated[index][field] = value;
    setMedications(updated);
  };

  const validateForm = (): boolean => {
    if (!patientInfo.age || !patientInfo.gender) {
      setError('Please fill in patient age and gender');
      return false;
    }

    const age = parseInt(patientInfo.age);
    if (age < 1 || age > 120) {
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
    } catch (err: any) {
      setError(err.message || 'Failed to generate medication advice. Please try again.');
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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 p-4 md:p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Medical Guideline RAG System
          </h1>
          <p className="text-gray-600">
            AI-powered medication advisor using evidence-based medical literature
          </p>
        </div>

        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="grid gap-6">
          <Card>
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
                  />
                </div>
                <div>
                  <Label htmlFor="gender">Gender</Label>
                  <Select
                    value={patientInfo.gender}
                    onValueChange={(value: 'M' | 'F') => setPatientInfo({ ...patientInfo, gender: value })}
                  >
                    <SelectTrigger id="gender">
                      <SelectValue placeholder="Select gender" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="M">Male</SelectItem>
                      <SelectItem value="F">Female</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div>
                <Label htmlFor="symptoms">Current Symptoms (Optional)</Label>
                <Input
                  id="symptoms"
                  placeholder="Describe any current symptoms"
                  value={patientInfo.symptoms}
                  onChange={(e) => setPatientInfo({ ...patientInfo, symptoms: e.target.value })}
                />
              </div>
              <div>
                <Label htmlFor="conditions">Medical Conditions (Optional)</Label>
                <Input
                  id="conditions"
                  placeholder="Enter any existing medical conditions"
                  value={patientInfo.conditions}
                  onChange={(e) => setPatientInfo({ ...patientInfo, conditions: e.target.value })}
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Medications</CardTitle>
              <CardDescription>
                Add medications and their dosing schedules
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {medications.map((med, index) => (
                  <div key={index} className="grid grid-cols-1 md:grid-cols-12 gap-4 items-start p-4 border rounded-lg bg-gray-50">
                    <div className="md:col-span-2 flex items-center">
                      <span className="text-sm font-medium">Medication {index + 1}</span>
                    </div>
                    <div className="md:col-span-6">
                      <Label htmlFor={`med-name-${index}`} className="sr-only">
                        Medication Name
                      </Label>
                      <Input
                        id={`med-name-${index}`}
                        placeholder="Enter medication name"
                        value={med.name}
                        onChange={(e) => updateMedication(index, 'name', e.target.value)}
                      />
                    </div>
                    <div className="md:col-span-3">
                      <Label htmlFor={`med-schedule-${index}`} className="sr-only">
                        Dosing Schedule
                      </Label>
                      <Input
                        id={`med-schedule-${index}`}
                        placeholder="e.g., 1+0+1"
                        value={med.schedule}
                        onChange={(e) => updateMedication(index, 'schedule', e.target.value)}
                      />
                    </div>
                    <div className="md:col-span-1">
                      {medications.length > 1 && (
                        <Button
                          variant="destructive"
                          size="icon"
                          onClick={() => removeMedication(index)}
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M18 6L6 18M6 6l12 12" />
                          </svg>
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
                <Button
                  variant="outline"
                  onClick={addMedication}
                  className="w-full"
                  disabled={medications.length >= 10}
                >
                  Add Another Medication
                </Button>
              </div>
            </CardContent>
          </Card>

          <div className="flex gap-4">
            <Button
              onClick={handleSubmit}
              disabled={loading}
              className="flex-1"
              size="lg"
            >
              {loading ? 'Processing...' : 'Generate Medication Advice'}
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

function ResultsView({ results, onReset }: { results: any; onReset: () => void }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-50 p-4 md:p-8">
      <div className="max-w-5xl mx-auto">
        <div className="mb-6 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Medication Consultation Results
            </h1>
            <p className="text-gray-600">
              Generated on {new Date().toLocaleDateString()} at {new Date().toLocaleTimeString()}
            </p>
          </div>
          <Button onClick={onReset} variant="outline">
            New Consultation
          </Button>
        </div>

        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="prose max-w-none">
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
                <span className="text-gray-600">Medications Processed:</span>
                <span className="font-semibold">{results.medications_processed}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Medications Found in Database:</span>
                <span className="font-semibold">{results.medications_found}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">PubMed Articles Referenced:</span>
                <span className="font-semibold">{results.pubmed_articles}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Drug Interactions Found:</span>
                <span className="font-semibold">{results.drug_interactions_found}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Interaction Warnings:</span>
                <span className="font-semibold">{results.interaction_warnings}</span>
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
              {results.context_sources?.slice(0, 5).map((source: any, index: number) => (
                <div key={index} className="p-4 border rounded-lg">
                  <h3 className="font-semibold mb-2">{source.title}</h3>
                  <p className="text-sm text-gray-600 mb-2">Source: {source.source}</p>
                  <p className="text-sm text-gray-600 mb-2">Year: {source.publication_year || 'N/A'}</p>
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline text-sm"
                  >
                    View Article
                  </a>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <div className="mt-8 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-sm text-yellow-800">
            <strong>Medical Disclaimer:</strong> This information is for educational purposes only. 
            Always consult your healthcare provider before making any changes to your medication regimen.
          </p>
        </div>
      </div>
    </div>
  );
}
