'use client';

import ReactMarkdown from 'react-markdown';
import rehypeSanitize from 'rehype-sanitize';
import remarkGfm from 'remark-gfm';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { FileText } from 'lucide-react';
import type { AdviceResponse } from '@/lib/api';

const PUBMED_CITATION = /PMID:\s?(\d+)/g;

function linkPubMedCitations(advice: string): string {
  return advice.replace(
    PUBMED_CITATION,
    (label, pmid) => `[${label}](https://pubmed.ncbi.nlm.nih.gov/${pmid}/)`
  );
}

interface ResultsViewProps {
  results: AdviceResponse;
  onReset: () => void;
}

export default function ResultsView({ results, onReset }: ResultsViewProps) {
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

        {results.advice_source === 'fallback' && (
          <Alert className="mb-6 border-amber-300 bg-amber-50 dark:bg-amber-900/30">
            <AlertDescription className="text-amber-900 dark:text-amber-200">
              <strong>AI guidance unavailable.</strong> The text below is a fixed safety
              notice, not generated medical advice
              {results.missing_configuration?.length
                ? ` (missing: ${results.missing_configuration.join(', ')})`
                : ''}
              .
            </AlertDescription>
          </Alert>
        )}

        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="prose max-w-none break-words text-slate-900 dark:text-slate-100">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeSanitize]}
                components={{
                  a: ({ href, children }) => (
                    <a
                      href={href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 underline hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-500"
                    >
                      {children}
                    </a>
                  ),
                }}
              >
                {linkPubMedCitations(results.advice || 'No advice available')}
              </ReactMarkdown>
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
                  {source.url && (
                    <a
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-500 font-semibold"
                    >
                      <FileText className="w-4 h-4 mr-2" />
                      View Article
                    </a>
                  )}
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
