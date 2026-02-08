'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Activity, Database, FileText, Users, AlertTriangle, TrendingUp, BookOpen } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { ThemeToggle } from '@/components/shared/theme-toggle';

export default function DashboardPage() {
  const [healthStatus, setHealthStatus] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useState(() => {
    async function loadData() {
      try {
        const [health, statsData] = await Promise.all([
          apiClient.getHealth(),
          apiClient.getStats()
        ]);
        setHealthStatus(health);
        setStats(statsData);
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-slate-800 p-6 animate-fade-in">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <header className="mb-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
                Medical Guideline RAG System
              </h1>
              <p className="text-slate-600 dark:text-slate-400 mt-2">
                AI-powered medication advisor using evidence-based medical literature
              </p>
            </div>
            <ThemeToggle />
          </div>
        </header>

        {loading ? (
          <div className="animate-pulse">
            <Card className="border-l-4 border-l-blue-500">
              <CardContent className="pt-6">
                <div className="flex items-center gap-4">
                  <div className="animate-spin w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full" />
                  <span className="text-slate-600">Loading dashboard...</span>
                </div>
              </CardContent>
            </Card>
          </div>
        ) : (
          <>
            {/* Health Status Banner */}
            <Card className="mb-6 border-l-4 border-l-green-500 animate-slide-in">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between flex-wrap gap-4">
                  <div className="flex items-center gap-3">
                    <Activity className="w-6 h-6 text-blue-600" />
                    <div>
                      <h3 className="font-semibold text-lg">
                        System Status: {healthStatus?.status === 'healthy' ? 'Operational' : 'Degraded'}
                      </h3>
                      <p className="text-sm text-slate-600 dark:text-slate-400">
                        Last checked: {new Date().toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    {healthStatus?.services_detail?.vector_search && (
                      <span className="inline-flex items-center px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs font-semibold">
                        Vector Search
                      </span>
                    )}
                    {healthStatus?.services_detail?.llm_client && (
                      <span className="inline-flex items-center px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs font-semibold">
                        LLM Client
                      </span>
                    )}
                    {healthStatus?.services_detail?.drug_lookup && (
                      <span className="inline-flex items-center px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs font-semibold">
                        Drug DB
                      </span>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Quick Actions Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <Link href="/consultation" className="group">
                <Card className="hover:shadow-lg transition-shadow cursor-pointer animate-scale-up h-full border-2 border-transparent hover:border-slate-300">
                  <CardContent className="pt-6 h-full">
                    <div className="flex items-center gap-4">
                      <div className="p-3 bg-blue-100 dark:bg-blue-900 rounded-lg group-hover:scale-110 transition-transform">
                        <FileText className="w-8 h-8 text-blue-600 dark:text-blue-400" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-lg">New Consultation</h3>
                        <p className="text-sm text-slate-600 dark:text-slate-400">
                          Get personalized medication advice
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>

              <Link href="/drug-interaction" className="group">
                <Card className="hover:shadow-lg transition-shadow cursor-pointer animate-scale-up h-full border-2 border-transparent hover:border-slate-300">
                  <CardContent className="pt-6 h-full">
                    <div className="flex items-center gap-4">
                      <div className="p-3 bg-amber-100 dark:bg-amber-900 rounded-lg group-hover:scale-110 transition-transform">
                        <AlertTriangle className="w-8 h-8 text-amber-600 dark:text-amber-400" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-lg">Drug Interactions</h3>
                        <p className="text-sm text-slate-600 dark:text-slate-400">
                          Check for potential drug-drug interactions
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>

              <Link href="/consultation" className="group">
                <Card className="hover:shadow-lg transition-shadow cursor-pointer animate-scale-up h-full border-2 border-transparent hover:border-slate-300">
                  <CardContent className="pt-6 h-full">
                    <div className="flex items-center gap-4">
                      <div className="p-3 bg-green-100 dark:bg-green-900 rounded-lg group-hover:scale-110 transition-transform">
                        <Users className="w-8 h-8 text-green-600 dark:text-green-400" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-lg">For Professionals</h3>
                        <p className="text-sm text-slate-600 dark:text-slate-400">
                          Advanced clinical tools
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            </div>

            {/* Statistics Grid */}
            <h2 className="text-2xl font-bold mb-4">System Statistics</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <StatCard
                icon={<Database className="w-5 h-5 text-blue-600" />}
                title="Documents Indexed"
                value={stats?.services?.vector_search?.total_documents || 0}
                color="blue"
              />
              <StatCard
                icon={<FileText className="w-5 h-5 text-green-600" />}
                title="Drugs in Database"
                value={stats?.services?.drug_database?.total_drugs || 0}
                color="green"
              />
              <StatCard
                icon={<Activity className="w-5 h-5 text-purple-600" />}
                title="Model"
                value={stats?.services?.llm_client?.model || 'N/A'}
                color="purple"
              />
              <StatCard
                icon={<TrendingUp className="w-5 h-5 text-orange-600" />}
                title="Embedding Dim"
                value={stats?.services?.vector_search?.embedding_dimension || 0}
                color="orange"
              />
            </div>

            {/* Recent Activity */}
            <h2 className="text-2xl font-bold mb-4">Recent Activity</h2>
            <Card>
              <CardContent className="pt-6">
                <div className="text-center text-slate-600 dark:text-slate-400 py-8">
                  <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p className="mb-4">No recent consultations yet</p>
                  <Link href="/consultation">
                    <Button className="mt-4">
                      Start Your First Consultation
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          </>
        )}

        {/* Footer */}
        <div className="mt-8 p-4 bg-slate-100 dark:bg-slate-800 rounded-lg text-center text-sm text-slate-600 dark:text-slate-400">
          <p>
            <strong>System Version:</strong> 1.0.0 |{' '}
            <strong>API Status:</strong> {healthStatus?.status === 'healthy' ? 'Online' : 'Degraded'}
          </p>
        </div>
      </div>
    </div>
  );
}

function StatCard({ icon, title, value, color }: any) {
  const colorClasses = {
    blue: 'bg-blue-100 text-blue-700 border-blue-500 dark:bg-blue-900 dark:text-blue-400',
    green: 'bg-green-100 text-green-700 border-green-500 dark:bg-green-900 dark:text-green-400',
    purple: 'bg-purple-100 text-purple-700 border-purple-500 dark:bg-purple-900 dark:text-purple-400',
    orange: 'bg-orange-100 text-orange-700 border-orange-500 dark:bg-orange-900 dark:text-orange-400',
  };

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="pt-6">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${colorClasses[color as keyof typeof colorClasses]}`}>
            {icon}
          </div>
          <div className="flex-1">
            <p className="text-sm text-slate-600 dark:text-slate-400">{title}</p>
            <p className={`text-3xl font-bold ${colorClasses[color as keyof typeof colorClasses].split(' ')[0]}`}>
              {value}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
