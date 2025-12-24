import React, { useState } from 'react';
import { AssistantResponse, AssistantFile } from '../../types/assistant';

interface ResultViewerProps {
  result: AssistantResponse;
}

export const ResultViewer: React.FC<ResultViewerProps> = ({ result }) => {
  const [selectedFileIndex, setSelectedFileIndex] = useState(0);
  const selectedFile = result.files[selectedFileIndex];

  const handleCopy = (content: string) => {
    navigator.clipboard.writeText(content);
    alert('Copied to clipboard!');
  };

  const handleDownload = (file: AssistantFile) => {
    const blob = new Blob([file.content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = file.path.split('/').pop() || 'file.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col h-full gap-6">
      {/* Summary Section */}
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <h2 className="text-lg font-semibold mb-2 text-gray-800">Summary</h2>
        <p className="text-gray-600 mb-4 whitespace-pre-wrap">{result.summary}</p>
        {result.assumptions.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">Assumptions</h3>
            <ul className="list-disc list-inside text-sm text-gray-600">
              {result.assumptions.map((a, i) => (
                <li key={i}>{a}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Code Section */}
      <div className="flex flex-1 min-h-[500px] gap-4">
        {/* File Explorer */}
        <div className="w-64 bg-gray-50 border border-gray-200 rounded-lg overflow-hidden flex flex-col">
          <div className="p-3 border-b border-gray-200 bg-gray-100 font-medium text-sm text-gray-700">
            Affected Files ({result.files.length})
          </div>
          <div className="flex-1 overflow-y-auto">
            {result.files.map((file, idx) => (
              <button
                key={idx}
                onClick={() => setSelectedFileIndex(idx)}
                className={`w-full text-left p-3 text-sm transition-colors flex flex-col gap-1 ${
                  selectedFileIndex === idx
                    ? 'bg-blue-50 border-r-4 border-blue-500'
                    : 'hover:bg-gray-100'
                }`}
              >
                <span className="font-medium text-gray-800 truncate" title={file.path}>
                  {file.path.split('/').pop()}
                </span>
                <span className="text-xs text-gray-500 truncate">{file.path}</span>
                <span className={`text-[10px] uppercase font-bold ${
                  file.action === 'create' ? 'text-green-600' : 'text-orange-600'
                }`}>
                  {file.action}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Code Preview */}
        <div className="flex-1 bg-gray-900 rounded-lg shadow-lg overflow-hidden flex flex-col">
          <div className="p-3 bg-gray-800 border-b border-gray-700 flex justify-between items-center">
            <span className="text-sm font-mono text-gray-300">{selectedFile?.path}</span>
            <div className="flex gap-2">
              <button
                onClick={() => handleCopy(selectedFile?.content)}
                className="px-3 py-1 text-xs font-medium text-gray-300 hover:text-white hover:bg-gray-700 rounded transition-colors"
              >
                Copy
              </button>
              <button
                onClick={() => handleDownload(selectedFile)}
                className="px-3 py-1 text-xs font-medium text-gray-300 hover:text-white hover:bg-gray-700 rounded transition-colors"
              >
                Download
              </button>
            </div>
          </div>
          <div className="flex-1 overflow-auto p-4">
            <pre className="text-sm font-mono text-gray-300 whitespace-pre">
              <code>{selectedFile?.content}</code>
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
};
