import React, { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import Editor from '@monaco-editor/react';
import { codingService, sessionService } from '../services/codingService';
import { useSessionRecorder } from '../hooks/useSessionRecorder';
import {
  Play,
  Send,
  Terminal,
  Clock,
  Cpu,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Code2,
  ShieldCheck,
} from 'lucide-react';

const DEFAULT_BOILERPLATES = {
  python: `class BankAccount:
    def __init__(self, account_holder: str, initial_balance: float = 0.0):
        # Validate initial_balance invariant (cannot be negative)
        if initial_balance < 0:
            raise ValueError("Initial balance cannot be negative")
        self.account_holder = account_holder
        self.balance = float(initial_balance)

    def deposit(self, amount: float) -> float:
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        self.balance += amount
        return self.balance

    def withdraw(self, amount: float) -> float:
        if amount <= 0:
            raise ValueError("Withdraw amount must be positive")
        if amount > self.balance:
            raise ValueError("Insufficient balance")
        self.balance -= amount
        return self.balance

    def get_balance(self) -> float:
        return self.balance

# Driver loop for sandbox test cases
if __name__ == "__main__":
    try:
        init_line = input().strip()
        if init_line:
            acc = BankAccount("Student", float(init_line))
            while True:
                cmd_line = input().strip()
                if not cmd_line:
                    break
                parts = cmd_line.split()
                cmd = parts[0].lower()
                if cmd == "deposit":
                    acc.deposit(float(parts[1]))
                    print(acc.get_balance())
                elif cmd == "withdraw":
                    acc.withdraw(float(parts[1]))
                    print(acc.get_balance())
                elif cmd == "balance":
                    print(acc.get_balance())
    except (EOFError, StopIteration):
        pass
`,
  cpp: `#include <iostream>
#include <vector>
#include <string>
using namespace std;

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);
    // Write your solution here
    return 0;
}
`,
  c: `#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main() {
    // Write your solution here
    return 0;
}
`,
  java: `import java.util.*;
import java.io.*;

public class Solution {
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        // Write your solution here
    }
}
`,
  javascript: `const readline = require('readline');

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

const lines = [];
rl.on('line', (line) => {
    lines.push(line.trim());
});

rl.on('close', () => {
    // Write your solution here
});
`
};

export default function CodingAssessmentPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const problemIdFromState = location.state?.problemId || 1;

  const [problem, setProblem] = useState(null);
  const [language, setLanguage] = useState('python');
  const [code, setCode] = useState(DEFAULT_BOILERPLATES.python);
  const [sessionId, setSessionId] = useState(null);
  const [running, setRunning] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [runResult, setRunResult] = useState(null);
  const [activeTab, setActiveTab] = useState('tests'); // tests or output

  const editorRef = useRef(null);
  const isPastingRef = useRef(false);
  const hasRunOnceRef = useRef(false);

  const handleLanguageChange = (newLang) => {
    // If current code matches default of previous language or is empty, switch template
    const prevDefault = DEFAULT_BOILERPLATES[language];
    if (!code.trim() || code.trim() === prevDefault?.trim()) {
      setCode(DEFAULT_BOILERPLATES[newLang] || '');
    }
    setLanguage(newLang);
  };

  // Hook for session recording
  const { recordEvent, flushEvents } = useSessionRecorder(sessionId);

  // Initialize assessment session and fetch problem
  useEffect(() => {
    async function init() {
      try {
        const prob = await codingService.getProblem(problemIdFromState);
        setProblem(prob);

        const sess = await sessionService.startSession(prob.id);
        setSessionId(sess.id);
      } catch (err) {
        console.error('Failed to initialize session/problem:', err);
      }
    }
    init();
  }, [problemIdFromState]);

  // Monaco Editor onMount handler
  const handleEditorMount = (editor, monaco) => {
    editorRef.current = editor;

    // Listen for paste event directly in Monaco
    if (editor.onDidPaste) {
      editor.onDidPaste((e) => {
        isPastingRef.current = true;
      });
    }

    // Listen for copy command initiated inside the editor
    editor.onKeyDown((e) => {
      if ((e.ctrlKey || e.metaKey) && e.code === 'KeyC') {
        const selection = editor.getSelection();
        recordEvent('COPY', {
          codeLocation: {
            start_line: selection.startLineNumber,
            start_column: selection.startColumn,
            end_line: selection.endLineNumber,
            end_column: selection.endColumn,
          },
          metadata: { action: 'editor_internal_copy' },
        });
      }
    });

    // Editor focus/blur tracking
    editor.onDidFocusEditorText(() => {
      recordEvent('FOCUS', { metadata: { target: 'editor_text' } });
    });

    editor.onDidBlurEditorText(() => {
      recordEvent('BLUR', { metadata: { target: 'editor_text' } });
    });
  };

  // Handle code change in Monaco Editor and record typing/paste events with exact code location
  const handleEditorChange = (value, event) => {
    setCode(value);

    // If event contains detailed model changes
    if (event?.changes && event.changes.length > 0) {
      for (const change of event.changes) {
        const inserted = change.text?.length || 0;
        const deleted = change.rangeLength || 0;
        const codeLocation = {
          start_line: change.range.startLineNumber,
          start_column: change.range.startColumn,
          end_line: change.range.endLineNumber,
          end_column: change.range.endColumn,
        };

        let evType = 'TYPE';
        if (isPastingRef.current || inserted >= 100) {
          evType = 'PASTE';
          isPastingRef.current = false;
        } else if (hasRunOnceRef.current) {
          evType = 'EDIT_AFTER_RUN';
        } else if (deleted > 0 && inserted > 0) {
          evType = 'REPLACE';
        } else if (deleted > 0 && inserted === 0) {
          evType = 'DELETE';
        }

        recordEvent(evType, {
          codeLocation,
          insertedCount: inserted,
          deletedCount: deleted,
          currentCode: value,
          metadata: {
            preview: change.text ? change.text.slice(0, 100) : '',
            lines_affected: change.range.endLineNumber - change.range.startLineNumber + 1,
          },
        });
      }
    } else {
      // Fallback
      recordEvent(hasRunOnceRef.current ? 'EDIT_AFTER_RUN' : 'TYPE', {
        currentCode: value,
      });
    }
  };

  // Run visible tests
  const handleRun = async () => {
    if (!problem) return;
    setRunning(true);
    hasRunOnceRef.current = true;
    recordEvent('RUN', {
      currentCode: code,
      metadata: { language, codeLength: code.length },
    });
    await flushEvents();

    try {
      const res = await codingService.runCode(problem.id, language, code);
      setRunResult(res);
      setActiveTab('tests');
    } catch (err) {
      console.error('Run failed:', err);
    } finally {
      setRunning(false);
    }
  };

  // Submit against hidden tests and proceed to Explain Your Code viva
  const handleSubmit = async () => {
    if (!problem) return;
    setSubmitting(true);
    recordEvent('SUBMIT', {
      currentCode: code,
      metadata: { language, codeLength: code.length },
    });
    await flushEvents();

    try {
      const res = await codingService.submitCode(problem.id, language, code, sessionId);
      if (sessionId) {
        await sessionService.endSession(sessionId);
      }
      // Navigate to Explain Your Code
      navigate(`/student/explain/${res.submission_id}`);
    } catch (err) {
      console.error('Submission failed:', err);
      alert('Submission encountered an error. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 100px)', gap: '16px' }}>
      {/* Left Column: Problem Statement & Visible Test Cases */}
      <div
        style={{
          width: '42%',
          backgroundColor: '#ffffff',
          borderRadius: '14px',
          border: '1px solid #e2e8f0',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        <div style={{ padding: '20px 24px', borderBottom: '1px solid #e5e7eb', backgroundColor: '#f8fafc' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
            <span
              style={{
                fontSize: '11px',
                fontWeight: 700,
                color: '#4f46e5',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}
            >
              Problem Specification
            </span>
            <span
              style={{
                fontSize: '11px',
                fontWeight: 700,
                backgroundColor: problem?.difficulty === 'EASY' ? '#ecfdf5' : '#eff6ff',
                color: problem?.difficulty === 'EASY' ? '#059669' : '#2563eb',
                padding: '2px 8px',
                borderRadius: '4px',
              }}
            >
              {problem?.difficulty}
            </span>
          </div>
          <h2 style={{ fontSize: '18px', fontWeight: 800, color: '#0f172a', margin: 0 }}>
            {problem?.title || 'Loading problem...'}
          </h2>
        </div>

        <div style={{ padding: '24px', overflowY: 'auto', flex: 1 }}>
          <div style={{ whiteSpace: 'pre-wrap', fontSize: '14px', color: '#334155', lineHeight: '1.6' }}>
            {problem?.description}
          </div>

          {/* Visible Test Cases */}
          <div style={{ marginTop: '24px' }}>
            <h4 style={{ fontSize: '13px', fontWeight: 700, color: '#475569', textTransform: 'uppercase', marginBottom: '10px' }}>
              Sample Visible Test Cases
            </h4>
            {problem?.visible_test_cases?.map((tc, idx) => (
              <div
                key={tc.id}
                style={{
                  backgroundColor: '#f8fafc',
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                  padding: '12px',
                  marginBottom: '10px',
                  fontSize: '12px',
                  fontFamily: 'monospace',
                }}
              >
                <div style={{ color: '#64748b', fontWeight: 600, marginBottom: '4px' }}>Input:</div>
                <div style={{ backgroundColor: '#ffffff', padding: '6px 8px', borderRadius: '4px', border: '1px solid #e2e8f0', marginBottom: '8px' }}>
                  {tc.input}
                </div>
                <div style={{ color: '#64748b', fontWeight: 600, marginBottom: '4px' }}>Expected Output:</div>
                <div style={{ backgroundColor: '#ffffff', padding: '6px 8px', borderRadius: '4px', border: '1px solid #e2e8f0' }}>
                  {tc.expected_output}
                </div>
              </div>
            ))}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: '#94a3b8', marginTop: '12px' }}>
              <ShieldCheck size={14} color="#10b981" />
              <span>Hidden validation test cases will execute upon final submission.</span>
            </div>
          </div>
        </div>
      </div>

      {/* Right Column: Editor & Sandbox Runner */}
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          backgroundColor: '#ffffff',
          borderRadius: '14px',
          border: '1px solid #e2e8f0',
          overflow: 'hidden',
        }}
      >
        {/* Editor Toolbar */}
        <div
          style={{
            padding: '12px 20px',
            borderBottom: '1px solid #e5e7eb',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            backgroundColor: '#1e293b',
            color: '#ffffff',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <span style={{ fontSize: '13px', fontWeight: 700, color: '#94a3b8' }}>Language:</span>
            <select
              value={language}
              onChange={(e) => handleLanguageChange(e.target.value)}
              style={{
                backgroundColor: '#334155',
                color: '#ffffff',
                border: '1px solid #475569',
                borderRadius: '6px',
                padding: '4px 10px',
                fontSize: '13px',
                fontWeight: 600,
              }}
            >
              <option value="python">Python 3.12</option>
              <option value="cpp">C++ 20 (GCC)</option>
              <option value="c">C (GCC)</option>
              <option value="java">Java 21</option>
              <option value="javascript">JavaScript (Node.js)</option>
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button
              onClick={handleRun}
              disabled={running || submitting}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 16px',
                backgroundColor: '#3b82f6',
                color: '#ffffff',
                border: 'none',
                borderRadius: '6px',
                fontWeight: 700,
                fontSize: '13px',
                cursor: running ? 'not-allowed' : 'pointer',
              }}
            >
              <Play size={14} /> {running ? 'Executing...' : 'Run Tests'}
            </button>

            <button
              onClick={handleSubmit}
              disabled={submitting || running}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 18px',
                backgroundColor: '#10b981',
                color: '#ffffff',
                border: 'none',
                borderRadius: '6px',
                fontWeight: 700,
                fontSize: '13px',
                cursor: submitting ? 'not-allowed' : 'pointer',
              }}
            >
              <Send size={14} /> {submitting ? 'Submitting...' : 'Submit & Explain Code'}
            </button>
          </div>
        </div>

        {/* Monaco Editor Container */}
        <div style={{ flex: 1, minHeight: '340px' }}>
          <Editor
            height="100%"
            language={
              language === 'cpp'
                ? 'cpp'
                : language === 'c'
                ? 'c'
                : language === 'java'
                ? 'java'
                : language === 'javascript'
                ? 'javascript'
                : 'python'
            }
            theme="vs-dark"
            value={code}
            onMount={handleEditorMount}
            onChange={handleEditorChange}
            options={{
              minimap: { enabled: false },
              fontSize: 14,
              tabSize: 4,
              lineNumbers: 'on',
              scrollBeyondLastLine: false,
              automaticLayout: true,
            }}
          />
        </div>

        {/* Bottom Sandbox Output / Test Results Panel */}
        <div
          style={{
            height: '240px',
            borderTop: '1px solid #e5e7eb',
            backgroundColor: '#0f172a',
            color: '#f8fafc',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {/* Output Header */}
          <div
            style={{
              padding: '8px 16px',
              borderBottom: '1px solid #1e293b',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              backgroundColor: '#1e293b',
            }}
          >
            <div style={{ display: 'flex', gap: '16px', fontSize: '12px', fontWeight: 700 }}>
              <button
                onClick={() => setActiveTab('tests')}
                style={{
                  background: 'none',
                  border: 'none',
                  color: activeTab === 'tests' ? '#38bdf8' : '#94a3b8',
                  borderBottom: activeTab === 'tests' ? '2px solid #38bdf8' : 'none',
                  padding: '4px 0',
                  cursor: 'pointer',
                  fontWeight: 700,
                }}
              >
                Visible Test Results {runResult && `(${runResult.all_passed ? 'All Passed' : runResult.status})`}
              </button>
              <button
                onClick={() => setActiveTab('output')}
                style={{
                  background: 'none',
                  border: 'none',
                  color: activeTab === 'output' ? '#38bdf8' : '#94a3b8',
                  borderBottom: activeTab === 'output' ? '2px solid #38bdf8' : 'none',
                  padding: '4px 0',
                  cursor: 'pointer',
                  fontWeight: 700,
                }}
              >
                Raw Standard Output & Errors
              </button>
            </div>

            {runResult && (
              <div style={{ display: 'flex', gap: '12px', fontSize: '11px', color: '#94a3b8' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <Clock size={12} /> {runResult.execution_time}s
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <Cpu size={12} /> {runResult.memory_used} MB
                </span>
              </div>
            )}
          </div>

          {/* Output Content */}
          <div style={{ padding: '14px 18px', overflowY: 'auto', flex: 1, fontFamily: 'monospace', fontSize: '13px' }}>
            {!runResult && !running && (
              <div style={{ color: '#64748b', fontStyle: 'italic' }}>
                Press "Run Tests" to execute your solution inside the isolated Docker/Process sandbox.
              </div>
            )}

            {running && (
              <div style={{ color: '#38bdf8' }}>
                Executing sandbox container... validating memory, time limits, and security constraints...
              </div>
            )}

            {runResult && activeTab === 'tests' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {runResult.visible_test_results?.map((tr, i) => (
                  <div
                    key={i}
                    style={{
                      padding: '10px 14px',
                      borderRadius: '6px',
                      backgroundColor: tr.passed ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                      border: `1px solid ${tr.passed ? '#059669' : '#dc2626'}`,
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <span style={{ fontWeight: 700, color: tr.passed ? '#34d399' : '#f87171' }}>
                        Test Case #{i + 1}: {tr.passed ? 'PASSED' : 'FAILED'}
                      </span>
                      <span style={{ color: '#94a3b8', fontSize: '11px' }}>{tr.execution_time}s</span>
                    </div>
                    {!tr.passed && (
                      <div style={{ fontSize: '12px', color: '#fca5a5' }}>
                        <div>Expected: {tr.expected_output}</div>
                        <div>Actual: {tr.actual_output || tr.error_message}</div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {runResult && activeTab === 'output' && (
              <div>
                {runResult.stdout && (
                  <div>
                    <div style={{ color: '#94a3b8', fontSize: '11px', marginBottom: '4px' }}>STDOUT:</div>
                    <pre style={{ margin: '0 0 10px 0', color: '#e2e8f0' }}>{runResult.stdout}</pre>
                  </div>
                )}
                {runResult.stderr && (
                  <div>
                    <div style={{ color: '#f87171', fontSize: '11px', marginBottom: '4px' }}>STDERR:</div>
                    <pre style={{ margin: 0, color: '#fca5a5' }}>{runResult.stderr}</pre>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
