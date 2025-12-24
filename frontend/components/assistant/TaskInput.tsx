import React, { useState } from 'react';

interface TaskInputProps {
  onGenerate: (instruction: string) => void;
  isLoading: boolean;
}

export const TaskInput: React.FC<TaskInputProps> = ({ onGenerate, isLoading }) => {
  const [instruction, setInstruction] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (instruction.trim()) {
      onGenerate(instruction.trim());
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <h2 className="text-lg font-semibold mb-4 text-gray-800">New Task</h2>
      <form onSubmit={handleSubmit}>
        <textarea
          className="w-full h-32 p-4 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none text-gray-700"
          placeholder="Describe a task, ask about the codebase, or design something new (e.g., 'Add a feature X', 'Design an e-commerce database schema', 'Explain the architecture')..."
          value={instruction}
          onChange={(e) => setInstruction(e.target.value)}
          disabled={isLoading}
        />
        <div className="mt-4 flex justify-end">
          <button
            type="submit"
            disabled={isLoading || !instruction.trim()}
            className={`px-6 py-2 rounded-md font-medium text-white transition-colors ${
              isLoading || !instruction.trim()
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {isLoading ? 'Generating...' : 'Generate Code'}
          </button>
        </div>
      </form>
    </div>
  );
};
