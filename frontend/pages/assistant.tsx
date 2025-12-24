import { useState } from 'react';
import { SidebarShell } from '@/components/SidebarShell';
import { TaskInput } from '@/components/assistant/TaskInput';
import { ResultViewer } from '@/components/assistant/ResultViewer';
import { AssistantResponse } from '@/types/assistant';

type ApiError = { detail?: string };

export default function AssistantPage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AssistantResponse | null>(null);
  const [error, setError] = useState('');
  
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  async function handleGenerate(instruction: string) {
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const res = await fetch(`${API_BASE}/assistant/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ instruction }),
      }).catch(() => {
        throw new Error(`Connection failed. Ensure the backend is running at ${API_BASE}`);
      });

      const data = await res.json().catch(() => ({}));
      
      if (!res.ok) {
        throw new Error((data as ApiError)?.detail || `Request failed (HTTP ${res.status})`);
      }

      setResult(data as AssistantResponse);
    } catch (e) {
      setError((e as Error)?.message || 'An unexpected error occurred.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <SidebarShell
      title="AI Codebase Assistant"
      subtitle="Standalone tool for production-ready code generation and architecture analysis."
    >
      <div className="max-w-6xl mx-auto space-y-8 pb-12">
        {/* Input Section */}
        <TaskInput onGenerate={handleGenerate} isLoading={loading} />

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-md">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-700 font-medium">Error: {error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Loading State Skeleton */}
        {loading && (
          <div className="animate-pulse space-y-6">
            <div className="h-32 bg-gray-200 rounded-lg"></div>
            <div className="h-96 bg-gray-200 rounded-lg"></div>
          </div>
        )}

        {/* Result Section */}
        {result && !loading && (
          <ResultViewer result={result} />
        )}

        {/* Empty State */}
        {!result && !loading && !error && (
          <div className="text-center py-20 border-2 border-dashed border-gray-200 rounded-xl">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No generation active</h3>
            <p className="mt-1 text-sm text-gray-500">Provide an instruction above to start generating code.</p>
          </div>
        )}
      </div>
    </SidebarShell>
  );
}
