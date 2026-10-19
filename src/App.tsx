import React, { useState, useEffect, useRef } from 'react';
import {
  Database,
  ShieldCheck,
  Terminal,
  Table,
  FileText,
  RefreshCw,
  Play,
  Copy,
  Check,
  AlertTriangle,
  TrendingUp,
  Layers,
  Filter,
  Download,
  ArrowRight,
  Search,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Code
} from 'lucide-react';

interface QueryResult {
  success: boolean;
  columns: string[];
  rows: Record<string, any>[];
  row_count: number;
  execution_time_ms: number;
  query_executed: string;
  error?: string | null;
}

interface AnalystResponse {
  question: string;
  is_followup: boolean;
  active_filters: Record<string, any>;
  generated_sql: string;
  sanitized_sql: string;
  is_safe: boolean;
  safety_reason: string;
  safety_warnings: string[];
  query_result: QueryResult | null;
  business_summary: string;
  error?: string | null;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content?: string;
  response?: AnalystResponse;
  timestamp: string;
}

export default function App() {
  const [activeTab, setActiveTab] = useState<'console' | 'benchmark' | 'schema' | 'safety' | 'evidence'>('console');
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        'Welcome to the Retail SQL Data Analyst Agent. I analyze omnichannel retail sales, customer segments, store performance, and returns data using safe read-only SQL queries and conversation context memory.\n\nTry asking: "What are the top 5 products by net sales?", and follow up with: "Now show only online channel."',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Schema state
  const [schemaData, setSchemaData] = useState<any>(null);
  const [selectedTable, setSelectedTable] = useState<string>('sales_transactions');

  // Safety Lab state
  const [safetyInputSql, setSafetyInputSql] = useState('DROP TABLE customers;');
  const [safetyCheckResult, setSafetyCheckResult] = useState<any>(null);
  const [isCheckingSafety, setIsCheckingSafety] = useState(false);

  // Evidence state
  const [testOutput, setTestOutput] = useState<string>('');
  const [isRunningTests, setIsRunningTests] = useState(false);
  const [evidenceData, setEvidenceData] = useState<any>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Fetch schema on mount
  useEffect(() => {
    fetch('/api/database/schema')
      .then((res) => res.json())
      .then((data) => setSchemaData(data))
      .catch((err) => console.error('Error fetching schema:', err));

    fetch('/api/analyst/evidence')
      .then((res) => res.json())
      .then((data) => setEvidenceData(data))
      .catch((err) => console.error('Error fetching evidence:', err));
  }, []);

  const handleSend = async (queryText?: string) => {
    const q = (queryText || inputQuery).trim();
    if (!q || isLoading) return;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: q,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery('');
    setIsLoading(true);

    try {
      const res = await fetch('/api/analyst/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q }),
      });

      const data: AnalystResponse = await res.json();

      const assistantMsg: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        response: data,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: 'assistant',
          content: `Error: Unable to connect to analyst agent (${err.message}).`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetSession = async () => {
    setIsLoading(true);
    try {
      await fetch('/api/analyst/reset', { method: 'POST' });
      setMessages([
        {
          id: `reset-${Date.now()}`,
          role: 'assistant',
          content: 'Conversation memory cleared. Ready for fresh analytical inquiries.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleRunSafetyTest = async () => {
    if (!safetyInputSql.trim()) return;
    setIsCheckingSafety(true);
    try {
      const res = await fetch('/api/analyst/validate-sql', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sql: safetyInputSql }),
      });
      const data = await res.json();
      setSafetyCheckResult(data);
    } catch (e: any) {
      setSafetyCheckResult({ error: e.message });
    } finally {
      setIsCheckingSafety(false);
    }
  };

  const handleExecuteTests = async () => {
    setIsRunningTests(true);
    setTestOutput('Running test suite in Python backend (tests/run_all_tests.py)...');
    try {
      const res = await fetch('/api/analyst/run-tests', { method: 'POST' });
      const data = await res.json();
      setTestOutput(data.output || data.evidence);
    } catch (e: any) {
      setTestOutput(`Error running tests: ${e.message}`);
    } finally {
      setIsRunningTests(false);
    }
  };

  const exportAnalysisReport = () => {
    const lines: string[] = [];
    lines.push('RETAIL SQL DATA ANALYST AGENT - CONVERSATION SESSION REPORT');
    lines.push(`Generated: ${new Date().toISOString()}`);
    lines.push('='.repeat(70) + '\n');

    messages.forEach((m, idx) => {
      if (m.role === 'user') {
        lines.push(`[TURN ${idx + 1}] USER QUERY: "${m.content}"`);
      } else if (m.response) {
        lines.push(`SAFE SQL GENERATED:`);
        lines.push(m.response.sanitized_sql || m.response.generated_sql);
        lines.push(`\nROW COUNT: ${m.response.query_result?.row_count || 0}`);
        lines.push(`BUSINESS SUMMARY:`);
        lines.push(m.response.business_summary);
        lines.push('-'.repeat(70) + '\n');
      }
    });

    const blob = new Blob([lines.join('\n')], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `retail_analyst_report_${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const sampleQuestions = [
    'What are the top 5 products by net sales?',
    'Now show only online channel.',
    'Which return reason is most common?',
    'Show total orders and return rate by store.',
    'Compare net sales across customer segments.',
  ];

  return (
    <div className="flex flex-col min-h-screen bg-slate-50 text-slate-900 font-sans antialiased">
      {/* 1. TOP BAR CONTRACT: [Brand title, 1-line] — [4-5 single-line nav links] — [1 primary action] */}
      <header className="sticky top-0 z-40 bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-8">
          {/* Zone 1: Brand Wordmark (Single text element, no pill badges) */}
          <div className="flex items-center gap-3 shrink-0">
            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white">
              <Database className="w-4 h-4" />
            </div>
            <span className="text-base font-semibold tracking-tight text-slate-900 whitespace-nowrap">
              RetailIQ Analyst Agent
            </span>
          </div>

          {/* Zone 2: Single-line Text Navigation Links */}
          <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-600">
            <button
              onClick={() => setActiveTab('console')}
              className={`whitespace-nowrap transition-colors pb-1 border-b-2 ${
                activeTab === 'console'
                  ? 'border-indigo-600 text-slate-900 font-semibold'
                  : 'border-transparent hover:text-slate-900'
              }`}
            >
              Analyst Console
            </button>
            <button
              onClick={() => setActiveTab('benchmark')}
              className={`whitespace-nowrap transition-colors pb-1 border-b-2 ${
                activeTab === 'benchmark'
                  ? 'border-indigo-600 text-slate-900 font-semibold'
                  : 'border-transparent hover:text-slate-900'
              }`}
            >
              Context Benchmark
            </button>
            <button
              onClick={() => setActiveTab('schema')}
              className={`whitespace-nowrap transition-colors pb-1 border-b-2 ${
                activeTab === 'schema'
                  ? 'border-indigo-600 text-slate-900 font-semibold'
                  : 'border-transparent hover:text-slate-900'
              }`}
            >
              Schema Explorer
            </button>
            <button
              onClick={() => setActiveTab('safety')}
              className={`whitespace-nowrap transition-colors pb-1 border-b-2 ${
                activeTab === 'safety'
                  ? 'border-indigo-600 text-slate-900 font-semibold'
                  : 'border-transparent hover:text-slate-900'
              }`}
            >
              Safety Validator
            </button>
            <button
              onClick={() => setActiveTab('evidence')}
              className={`whitespace-nowrap transition-colors pb-1 border-b-2 ${
                activeTab === 'evidence'
                  ? 'border-indigo-600 text-slate-900 font-semibold'
                  : 'border-transparent hover:text-slate-900'
              }`}
            >
              Tests & Evidence
            </button>
          </nav>

          {/* Zone 3: 1 Primary Action */}
          <div className="flex items-center gap-3 shrink-0">
            <button
              onClick={exportAnalysisReport}
              className="inline-flex items-center gap-2 px-3.5 py-1.5 text-xs font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 transition-colors whitespace-nowrap shadow-xs"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export Report</span>
            </button>
          </div>
        </div>
      </header>

      {/* MAIN VIEWPORT */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* TAB 1: ANALYST CONSOLE */}
        {activeTab === 'console' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-[calc(100vh-140px)] min-h-[600px]">
            {/* Left Column: Multi-Turn Conversation Thread (7 cols) */}
            <div className="lg:col-span-7 flex flex-col bg-white border border-slate-200 rounded-lg shadow-xs overflow-hidden">
              {/* Header bar of conversation */}
              <div className="px-5 py-3.5 border-b border-slate-200 flex items-center justify-between bg-slate-50/50">
                <div className="flex items-center gap-2 text-xs text-slate-500">
                  <span className="font-medium text-slate-700">Conversational Session</span>
                  <span aria-hidden="true">·</span>
                  <span>LangGraph Agent Memory Active</span>
                </div>
                <button
                  onClick={handleResetSession}
                  disabled={isLoading}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs text-slate-600 hover:text-slate-900 bg-white border border-slate-200 rounded hover:bg-slate-50 transition-colors"
                  title="Clear conversation context memory"
                >
                  <RefreshCw className="w-3 h-3" />
                  <span>Reset Context</span>
                </button>
              </div>

              {/* Message scroll container */}
              <div className="flex-1 p-5 overflow-y-auto space-y-5">
                {messages.map((msg) => (
                  <div key={msg.id} className="space-y-3">
                    {msg.role === 'user' ? (
                      <div className="flex justify-end">
                        <div className="max-w-xl bg-indigo-600 text-white rounded-lg px-4 py-2.5 text-sm shadow-xs">
                          <p className="font-medium">{msg.content}</p>
                          <div className="text-[11px] text-indigo-200 mt-1 text-right">{msg.timestamp}</div>
                        </div>
                      </div>
                    ) : (
                      <div className="flex flex-col space-y-3 max-w-2xl">
                        {/* Initial welcome text if no response payload */}
                        {msg.content && (
                          <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 text-sm text-slate-700 leading-relaxed whitespace-pre-line">
                            {msg.content}
                          </div>
                        )}

                        {/* Full Agent Response Card */}
                        {msg.response && (
                          <div className="bg-white border border-slate-200 rounded-lg shadow-xs overflow-hidden">
                            {/* Card Header: Verification metadata (Zero-pill discipline: unboxed clean text) */}
                            <div className="px-4 py-2.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between text-xs text-slate-500">
                              <div className="flex items-center gap-2">
                                <span className="font-semibold text-slate-700">
                                  {msg.response.is_followup ? 'Contextual Follow-up' : 'Initial Query'}
                                </span>
                                <span aria-hidden="true">·</span>
                                <span className={msg.response.is_safe ? 'text-emerald-700 font-medium' : 'text-rose-600 font-medium'}>
                                  {msg.response.is_safe ? 'Safe Read-Only SQL' : 'Blocked'}
                                </span>
                                <span aria-hidden="true">·</span>
                                <span className="font-mono tabular-nums">
                                  {msg.response.query_result?.execution_time_ms || 0}ms
                                </span>
                              </div>
                              <span className="text-[11px] text-slate-400">{msg.timestamp}</span>
                            </div>

                            {/* Section A: Business Summary */}
                            <div className="p-4 border-b border-slate-100 bg-indigo-50/20">
                              <div className="text-xs font-semibold text-slate-500 mb-1.5 flex items-center gap-1.5">
                                <TrendingUp className="w-3.5 h-3.5 text-indigo-600" />
                                <span>Executive Business Summary</span>
                              </div>
                              <div className="text-sm text-slate-800 leading-relaxed space-y-2">
                                {msg.response.business_summary.split('\n\n').map((paragraph, pIdx) => (
                                  <p key={pIdx} dangerouslySetInnerHTML={{ __html: paragraph.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') }} />
                                ))}
                              </div>
                            </div>

                            {/* Section B: Generated Safe SQL */}
                            <div className="p-4 border-b border-slate-100">
                              <div className="flex items-center justify-between mb-2">
                                <div className="text-xs font-semibold text-slate-500 flex items-center gap-1.5">
                                  <Code className="w-3.5 h-3.5 text-slate-600" />
                                  <span>Generated MySQL Query</span>
                                </div>
                                <button
                                  onClick={() => copyToClipboard(msg.response?.sanitized_sql || '', msg.id)}
                                  className="text-xs text-slate-500 hover:text-slate-800 inline-flex items-center gap-1"
                                >
                                  {copiedId === msg.id ? (
                                    <>
                                      <Check className="w-3 h-3 text-emerald-600" />
                                      <span className="text-emerald-600">Copied</span>
                                    </>
                                  ) : (
                                    <>
                                      <Copy className="w-3 h-3" />
                                      <span>Copy SQL</span>
                                    </>
                                  )}
                                </button>
                              </div>
                              <pre className="bg-slate-900 text-slate-100 text-xs p-3 rounded-md font-mono overflow-x-auto leading-relaxed border border-slate-800">
                                {msg.response.sanitized_sql || msg.response.generated_sql}
                              </pre>
                            </div>

                            {/* Section C: Tabular Result Preview */}
                            {msg.response.query_result && msg.response.query_result.rows.length > 0 && (
                              <div className="p-4">
                                <div className="text-xs font-semibold text-slate-500 mb-2 flex items-center justify-between">
                                  <div className="flex items-center gap-1.5">
                                    <Table className="w-3.5 h-3.5 text-slate-600" />
                                    <span>Result Records</span>
                                  </div>
                                  <span className="font-mono tabular-nums text-slate-500">
                                    {msg.response.query_result.row_count} rows returned
                                  </span>
                                </div>
                                <div className="border border-slate-200 rounded-md overflow-x-auto">
                                  <table className="w-full text-xs text-left">
                                    <thead className="bg-slate-50 text-slate-700 border-b border-slate-200">
                                      <tr>
                                        {msg.response.query_result.columns.map((col) => (
                                          <th key={col} className="px-3 py-2 font-medium whitespace-nowrap">
                                            {col}
                                          </th>
                                        ))}
                                      </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-100 font-mono tabular-nums">
                                      {msg.response.query_result.rows.slice(0, 5).map((row, rIdx) => (
                                        <tr key={rIdx} className="hover:bg-slate-50/60 transition-colors">
                                          {msg.response!.query_result!.columns.map((col) => {
                                            const val = row[col];
                                            const isNumeric = typeof val === 'number';
                                            return (
                                              <td
                                                key={col}
                                                className={`px-3 py-1.5 whitespace-nowrap ${
                                                  isNumeric ? 'text-right' : 'text-left font-sans'
                                                }`}
                                              >
                                                {isNumeric
                                                  ? col.includes('sales') || col.includes('revenue') || col.includes('price') || col.includes('aov')
                                                    ? `₹${Number(val).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                                                    : Number(val).toLocaleString()
                                                  : String(val)}
                                              </td>
                                            );
                                          })}
                                        </tr>
                                      ))}
                                    </tbody>
                                  </table>
                                </div>
                                {msg.response.query_result.rows.length > 5 && (
                                  <div className="text-[11px] text-slate-400 mt-1.5 text-right font-mono tabular-nums">
                                    + {msg.response.query_result.rows.length - 5} additional rows truncated for view
                                  </div>
                                )}
                              </div>
                            )}

                            {/* Section D: Active Filters Info */}
                            {msg.response.active_filters && Object.keys(msg.response.active_filters).some(k => msg.response!.active_filters[k]) && (
                              <div className="px-4 py-2 bg-slate-50 border-t border-slate-100 flex items-center gap-2 text-[11px] text-slate-500">
                                <span className="font-medium text-slate-600">Active Memory Context:</span>
                                {Object.entries(msg.response.active_filters)
                                  .filter(([_, v]) => v !== null && v !== undefined)
                                  .map(([k, v], i) => (
                                    <span key={k}>
                                      {i > 0 && <span className="mx-1" aria-hidden="true">·</span>}
                                      <span>{k}: <strong>{String(v)}</strong></span>
                                    </span>
                                  ))}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}

                {isLoading && (
                  <div className="flex items-center gap-3 text-slate-500 text-xs py-3">
                    <RefreshCw className="w-4 h-4 animate-spin text-indigo-600" />
                    <span>Analyzing natural language intent, generating safe SQL, and querying database...</span>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Query Input Area */}
              <div className="p-4 border-t border-slate-200 bg-white">
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleSend();
                  }}
                  className="flex items-center gap-2"
                >
                  <input
                    type="text"
                    value={inputQuery}
                    onChange={(e) => setInputQuery(e.target.value)}
                    placeholder="Ask a question (e.g. 'What are the top 5 products by net sales?')..."
                    className="flex-1 px-3.5 py-2 text-sm border border-slate-300 rounded-md focus:outline-hidden focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
                    disabled={isLoading}
                  />
                  <button
                    type="submit"
                    disabled={isLoading || !inputQuery.trim()}
                    className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50 transition-colors shrink-0 shadow-xs"
                  >
                    <span>Analyze</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </form>

                {/* Prompt suggestions strip */}
                <div className="flex items-center gap-1.5 mt-2.5 overflow-x-auto pb-1 text-xs text-slate-500">
                  <span className="shrink-0 text-[11px] text-slate-400">Suggestions:</span>
                  {sampleQuestions.slice(0, 3).map((sq) => (
                    <button
                      key={sq}
                      onClick={() => handleSend(sq)}
                      className="text-left px-2 py-0.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-xs whitespace-nowrap transition-colors"
                    >
                      {sq}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Right Column: Dataset & Safety Context Panel (5 cols) */}
            <div className="lg:col-span-5 flex flex-col gap-6">
              {/* Card 1: Relational Dataset Baseline */}
              <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-xs">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <div className="flex items-center gap-2">
                    <Database className="w-4 h-4 text-indigo-600" />
                    <h3 className="text-sm font-semibold text-slate-900">Retail Database Baseline</h3>
                  </div>
                  <span className="text-xs text-slate-500 font-mono tabular-nums">5 Relational Tables</span>
                </div>

                <div className="mt-4 space-y-2.5 text-xs">
                  <div className="flex items-center justify-between py-1 border-b border-slate-50">
                    <span className="text-slate-600 font-medium">sales_transactions</span>
                    <span className="font-mono tabular-nums text-slate-900 font-semibold">360 orders (₹406,797.71)</span>
                  </div>
                  <div className="flex items-center justify-between py-1 border-b border-slate-50">
                    <span className="text-slate-600 font-medium">customers</span>
                    <span className="font-mono tabular-nums text-slate-900">80 customer profiles</span>
                  </div>
                  <div className="flex items-center justify-between py-1 border-b border-slate-50">
                    <span className="text-slate-600 font-medium">products</span>
                    <span className="font-mono tabular-nums text-slate-900">10 catalog SKUs</span>
                  </div>
                  <div className="flex items-center justify-between py-1 border-b border-slate-50">
                    <span className="text-slate-600 font-medium">stores</span>
                    <span className="font-mono tabular-nums text-slate-900">15 stores (5 regions)</span>
                  </div>
                  <div className="flex items-center justify-between py-1">
                    <span className="text-slate-600 font-medium">returns</span>
                    <span className="font-mono tabular-nums text-slate-900">46 return items (12.8% rate)</span>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-100 text-[11px] text-slate-500 space-y-1">
                  <div><strong>Channels:</strong> Online, Mobile App, In-store, Partner</div>
                  <div><strong>Key Metric:</strong> Net Sales = units_sold × unit_price × (1 - discount%)</div>
                </div>
              </div>

              {/* Card 2: Security & Policy Enforcement */}
              <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-xs">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <div className="flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-emerald-600" />
                    <h3 className="text-sm font-semibold text-slate-900">Read-Only Safety Policy</h3>
                  </div>
                  <span className="text-xs text-emerald-700 font-medium">Active Policy</span>
                </div>

                <div className="mt-4 space-y-2 text-xs text-slate-600">
                  <div className="flex items-start gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                    <span><strong>Read-Only Whitelist:</strong> Only SELECT, WITH (CTE), and EXPLAIN operations permitted.</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                    <span><strong>Blocked Commands:</strong> DROP, DELETE, UPDATE, INSERT, ALTER, TRUNCATE, REPLACE.</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                    <span><strong>Injection Guard:</strong> Stacked multi-statement semicolons & comment evasion blocked.</span>
                  </div>
                  <div className="flex items-start gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                    <span><strong>Row Limit Cap:</strong> Enforces safe maximum limit of 100 rows per query.</span>
                  </div>
                </div>
              </div>

              {/* Card 3: Context Memory Demonstration Helper */}
              <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-xs flex-1">
                <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
                  <Layers className="w-4 h-4 text-indigo-600" />
                  <h3 className="text-sm font-semibold text-slate-900">Testing Context Memory</h3>
                </div>
                <div className="mt-3 text-xs text-slate-600 space-y-2 leading-relaxed">
                  <p>
                    The agent tracks dialogue state across multiple conversational turns using LangGraph state graph.
                  </p>
                  <p className="bg-slate-50 p-2.5 rounded border border-slate-100 text-slate-700">
                    <strong>Try this two-turn sequence:</strong>
                    <br />
                    1. Click: <em>"What are the top 5 products by net sales?"</em>
                    <br />
                    2. Then click: <em>"Now show only online channel."</em>
                  </p>
                  <p className="text-[11px] text-slate-500">
                    Notice how Turn 2 retains the product dimension and metric calculation without repeating the query!
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: CONTEXT BENCHMARK WALKTHROUGH */}
        {activeTab === 'benchmark' && (
          <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-xs space-y-6">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Multi-Turn Context Benchmark</h2>
              <p className="text-xs text-slate-500 mt-1">
                Step-by-step verification of context inheritance and elliptical follow-up resolution.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Step 1 */}
              <div className="border border-slate-200 rounded-lg p-4 bg-slate-50/50 space-y-3">
                <div className="flex items-center justify-between text-xs text-slate-500">
                  <span className="font-semibold text-indigo-700">Turn 1: Initial Question</span>
                  <span>Baseline Query</span>
                </div>
                <p className="text-sm font-medium text-slate-900">"What are the top 5 products by net sales?"</p>
                <div className="bg-slate-900 text-slate-100 p-2.5 rounded text-[11px] font-mono leading-relaxed">
                  SELECT p.product_name, SUM(st.units_sold) AS total_units_sold, ROUND(SUM(st.units_sold * st.unit_price * (1.0 - discount_pct/100)), 2) AS net_sales ... LIMIT 5;
                </div>
                <div className="text-xs text-slate-600 bg-white p-2 rounded border border-slate-200">
                  <strong>Outcome:</strong> Identifies <em>Rice 5kg</em> (₹87,871.80) and <em>Detergent</em> (₹80,003.49) as top performers.
                </div>
                <button
                  onClick={() => {
                    setActiveTab('console');
                    handleSend('What are the top 5 products by net sales?');
                  }}
                  className="w-full py-1.5 text-xs text-center font-medium bg-white hover:bg-slate-50 border border-slate-300 rounded text-slate-800 transition-colors"
                >
                  Run Turn 1 in Console
                </button>
              </div>

              {/* Step 2 */}
              <div className="border border-slate-200 rounded-lg p-4 bg-slate-50/50 space-y-3">
                <div className="flex items-center justify-between text-xs text-slate-500">
                  <span className="font-semibold text-indigo-700">Turn 2: Follow-Up Filter</span>
                  <span>Inherited Context</span>
                </div>
                <p className="text-sm font-medium text-slate-900">"Now show only online channel."</p>
                <div className="bg-slate-900 text-slate-100 p-2.5 rounded text-[11px] font-mono leading-relaxed">
                  ... WHERE st.sales_channel = 'Online' GROUP BY p.product_id ...
                </div>
                <div className="text-xs text-slate-600 bg-white p-2 rounded border border-slate-200">
                  <strong>Memory Resolution:</strong> Agent remembers product grouping from Turn 1 and injects the Online channel filter clause.
                </div>
                <button
                  onClick={() => {
                    setActiveTab('console');
                    handleSend('Now show only online channel.');
                  }}
                  className="w-full py-1.5 text-xs text-center font-medium bg-white hover:bg-slate-50 border border-slate-300 rounded text-slate-800 transition-colors"
                >
                  Run Follow-Up in Console
                </button>
              </div>

              {/* Step 3 */}
              <div className="border border-slate-200 rounded-lg p-4 bg-slate-50/50 space-y-3">
                <div className="flex items-center justify-between text-xs text-slate-500">
                  <span className="font-semibold text-indigo-700">Turn 3: Operational Analysis</span>
                  <span>Returns Root Cause</span>
                </div>
                <p className="text-sm font-medium text-slate-900">"Which return reason is most common?"</p>
                <div className="bg-slate-900 text-slate-100 p-2.5 rounded text-[11px] font-mono leading-relaxed">
                  SELECT r.return_reason, COUNT(r.return_id) AS return_count, ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM returns), 2) AS pct_of_returns ...
                </div>
                <div className="text-xs text-slate-600 bg-white p-2 rounded border border-slate-200">
                  <strong>Outcome:</strong> Highlights <em>Wrong Item</em> (12 returns, 26.09%) and <em>Late Delivery</em> (11 returns, 23.91%).
                </div>
                <button
                  onClick={() => {
                    setActiveTab('console');
                    handleSend('Which return reason is most common?');
                  }}
                  className="w-full py-1.5 text-xs text-center font-medium bg-white hover:bg-slate-50 border border-slate-300 rounded text-slate-800 transition-colors"
                >
                  Run Returns Query in Console
                </button>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: SCHEMA EXPLORER */}
        {activeTab === 'schema' && (
          <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-xs space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">Retail Database Schema</h2>
                <p className="text-xs text-slate-500 mt-1">
                  Relational tables, columns, constraints, and sample data from /data CSV sources.
                </p>
              </div>
              {/* Table Selector Tabs */}
              <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-md overflow-x-auto">
                {['sales_transactions', 'customers', 'products', 'stores', 'returns'].map((tbl) => (
                  <button
                    key={tbl}
                    onClick={() => setSelectedTable(tbl)}
                    className={`px-3 py-1.5 text-xs font-medium rounded transition-colors whitespace-nowrap ${
                      selectedTable === tbl ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    {tbl}
                  </button>
                ))}
              </div>
            </div>

            {/* Selected Table Overview */}
            {schemaData && (
              <div>
                {schemaData.tables
                  .filter((t: any) => t.name === selectedTable)
                  .map((tbl: any) => (
                    <div key={tbl.name} className="space-y-6">
                      <div className="flex items-center justify-between text-xs text-slate-500">
                        <span className="font-mono text-sm font-semibold text-slate-900">{tbl.name}</span>
                        <span className="font-mono tabular-nums font-medium text-slate-700">
                          {tbl.row_count} total records
                        </span>
                      </div>

                      {/* Columns Schema Table */}
                      <div>
                        <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                          Column Specifications
                        </h4>
                        <div className="border border-slate-200 rounded-md overflow-x-auto">
                          <table className="w-full text-xs text-left">
                            <thead className="bg-slate-50 text-slate-700 border-b border-slate-200">
                              <tr>
                                <th className="px-4 py-2 font-medium">Column Name</th>
                                <th className="px-4 py-2 font-medium">Data Type</th>
                                <th className="px-4 py-2 font-medium">Primary Key</th>
                                <th className="px-4 py-2 font-medium">Nullable</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100 font-mono">
                              {tbl.columns.map((c: any) => (
                                <tr key={c.name} className="hover:bg-slate-50">
                                  <td className="px-4 py-2 font-medium text-slate-900">{c.name}</td>
                                  <td className="px-4 py-2 text-slate-600">{c.type}</td>
                                  <td className="px-4 py-2 text-slate-600">{c.pk ? 'Yes (PK)' : 'No'}</td>
                                  <td className="px-4 py-2 text-slate-600">{c.notnull ? 'No' : 'Yes'}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>

                      {/* Sample Rows Preview */}
                      <div>
                        <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                          Sample Records Preview
                        </h4>
                        <div className="border border-slate-200 rounded-md overflow-x-auto">
                          <table className="w-full text-xs text-left">
                            <thead className="bg-slate-50 text-slate-700 border-b border-slate-200">
                              <tr>
                                {tbl.columns.map((c: any) => (
                                  <th key={c.name} className="px-3 py-2 font-medium whitespace-nowrap">
                                    {c.name}
                                  </th>
                                ))}
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100 font-mono tabular-nums">
                              {tbl.sample_rows.map((row: any, rIdx: number) => (
                                <tr key={rIdx} className="hover:bg-slate-50">
                                  {tbl.columns.map((c: any) => (
                                    <td key={c.name} className="px-3 py-1.5 whitespace-nowrap text-slate-800">
                                      {String(row[c.name])}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    </div>
                  ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 4: SAFETY VALIDATOR LAB */}
        {activeTab === 'safety' && (
          <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-xs space-y-6">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Safety & Read-Only Validator Lab</h2>
              <p className="text-xs text-slate-500 mt-1">
                Test custom SQL queries against the agent's security policies to verify read-only enforcement.
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Left Column: Input Query & Attack Samples */}
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                    Test SQL Query:
                  </label>
                  <textarea
                    rows={6}
                    value={safetyInputSql}
                    onChange={(e) => setSafetyInputSql(e.target.value)}
                    className="w-full p-3 font-mono text-xs border border-slate-300 rounded-md bg-slate-900 text-slate-100 focus:outline-hidden focus:ring-1 focus:ring-indigo-500"
                    placeholder="Enter SQL to test..."
                  />
                </div>

                <div className="flex items-center gap-3">
                  <button
                    onClick={handleRunSafetyTest}
                    disabled={isCheckingSafety}
                    className="px-4 py-2 text-xs font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 transition-colors shadow-xs"
                  >
                    {isCheckingSafety ? 'Validating...' : 'Validate Query Safety'}
                  </button>
                </div>

                <div className="pt-3 border-t border-slate-200">
                  <span className="text-xs font-semibold text-slate-700 block mb-2">
                    Preset Threat Scenarios to Test:
                  </span>
                  <div className="flex flex-wrap gap-2 text-xs">
                    <button
                      onClick={() => setSafetyInputSql('DROP TABLE customers;')}
                      className="px-2.5 py-1 bg-rose-50 text-rose-700 border border-rose-200 rounded hover:bg-rose-100 transition-colors"
                    >
                      DROP TABLE
                    </button>
                    <button
                      onClick={() => setSafetyInputSql("DELETE FROM sales_transactions WHERE units_sold > 5;")}
                      className="px-2.5 py-1 bg-rose-50 text-rose-700 border border-rose-200 rounded hover:bg-rose-100 transition-colors"
                    >
                      DELETE FROM
                    </button>
                    <button
                      onClick={() => setSafetyInputSql("UPDATE products SET base_price = 0;")}
                      className="px-2.5 py-1 bg-rose-50 text-rose-700 border border-rose-200 rounded hover:bg-rose-100 transition-colors"
                    >
                      UPDATE
                    </button>
                    <button
                      onClick={() => setSafetyInputSql("SELECT * FROM products; DROP TABLE customers;")}
                      className="px-2.5 py-1 bg-rose-50 text-rose-700 border border-rose-200 rounded hover:bg-rose-100 transition-colors"
                    >
                      Stacked Injection (;)
                    </button>
                    <button
                      onClick={() => setSafetyInputSql("SELECT * FROM sales_transactions LIMIT 500;")}
                      className="px-2.5 py-1 bg-amber-50 text-amber-700 border border-amber-200 rounded hover:bg-amber-100 transition-colors"
                    >
                      Excessive LIMIT (500)
                    </button>
                    <button
                      onClick={() => setSafetyInputSql("SELECT product_name, category, base_price FROM products ORDER BY base_price DESC;")}
                      className="px-2.5 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded hover:bg-emerald-100 transition-colors"
                    >
                      Safe Read-Only SELECT
                    </button>
                  </div>
                </div>
              </div>

              {/* Right Column: Validation Output */}
              <div className="border border-slate-200 rounded-md p-4 bg-slate-50/50 flex flex-col justify-between">
                <div>
                  <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
                    Safety Evaluation Engine Response
                  </h4>

                  {safetyCheckResult ? (
                    <div className="space-y-4">
                      <div className="flex items-center gap-2">
                        {safetyCheckResult.is_safe ? (
                          <div className="flex items-center gap-1.5 text-emerald-700 font-semibold text-sm">
                            <CheckCircle2 className="w-4 h-4" />
                            <span>APPROVED: Safe Read-Only Query</span>
                          </div>
                        ) : (
                          <div className="flex items-center gap-1.5 text-rose-700 font-semibold text-sm">
                            <XCircle className="w-4 h-4" />
                            <span>BLOCKED: Security Violation</span>
                          </div>
                        )}
                      </div>

                      <div className="text-xs text-slate-700 bg-white p-3 rounded border border-slate-200">
                        <strong>Evaluation Reason:</strong>
                        <p className="mt-1">{safetyCheckResult.reason}</p>
                      </div>

                      {safetyCheckResult.warnings && safetyCheckResult.warnings.length > 0 && (
                        <div className="text-xs text-amber-800 bg-amber-50 p-3 rounded border border-amber-200 space-y-1">
                          <strong>Notices / Sanitization:</strong>
                          {safetyCheckResult.warnings.map((w: string, idx: number) => (
                            <p key={idx}>· {w}</p>
                          ))}
                        </div>
                      )}

                      {safetyCheckResult.sanitized_sql && (
                        <div>
                          <span className="text-xs font-semibold text-slate-700 block mb-1">
                            Sanitized & Limit-Enforced Query:
                          </span>
                          <pre className="bg-slate-900 text-slate-100 p-2.5 rounded text-xs font-mono overflow-x-auto">
                            {safetyCheckResult.sanitized_sql}
                          </pre>
                        </div>
                      )}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-500 italic">
                      Click 'Validate Query Safety' or pick a preset scenario above to test the firewall.
                    </p>
                  )}
                </div>

                <div className="mt-4 pt-3 border-t border-slate-200 text-[11px] text-slate-500">
                  Engine: Python AST & Token Boundary Regex · Defined in <code>src/safety.py</code>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 5: TESTS & EVIDENCE */}
        {activeTab === 'evidence' && (
          <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-xs space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">Test Suite & Audit Evidence</h2>
                <p className="text-xs text-slate-500 mt-1">
                  Automated test runner and verification artifacts from /tests and /evidence directories.
                </p>
              </div>
              <button
                onClick={handleExecuteTests}
                disabled={isRunningTests}
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 disabled:opacity-50 transition-colors shadow-xs"
              >
                <Play className="w-3.5 h-3.5" />
                <span>{isRunningTests ? 'Executing Tests...' : 'Run All Python Tests'}</span>
              </button>
            </div>

            {/* Test Runner Terminal Output */}
            {testOutput && (
              <div>
                <div className="flex items-center justify-between text-xs font-semibold text-slate-700 mb-2">
                  <div className="flex items-center gap-1.5">
                    <Terminal className="w-4 h-4 text-slate-600" />
                    <span>Test Suite Output (25 Unit & Integration Tests)</span>
                  </div>
                  <span className="text-emerald-700 font-medium">tests/run_all_tests.py</span>
                </div>
                <pre className="bg-slate-900 text-slate-100 p-4 rounded-md text-xs font-mono overflow-x-auto leading-relaxed border border-slate-800">
                  {testOutput}
                </pre>
              </div>
            )}

            {/* Evidence Files List */}
            {evidenceData && (
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-slate-900">Recorded Evidence Artifacts</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {evidenceData.files.map((fname: string) => (
                    <div key={fname} className="border border-slate-200 rounded-lg p-4 bg-slate-50/50 space-y-2">
                      <div className="flex items-center gap-2 text-xs font-medium text-slate-900">
                        <FileText className="w-3.5 h-3.5 text-indigo-600" />
                        <span className="font-mono">{fname}</span>
                      </div>
                      <p className="text-[11px] text-slate-500 line-clamp-3">
                        {evidenceData.contents[fname]?.slice(0, 150)}...
                      </p>
                      <button
                        onClick={() => {
                          const blob = new Blob([evidenceData.contents[fname]], { type: 'text/plain' });
                          const url = URL.createObjectURL(blob);
                          const a = document.createElement('a');
                          a.href = url;
                          a.download = fname;
                          a.click();
                          URL.revokeObjectURL(url);
                        }}
                        className="text-xs text-indigo-600 hover:text-indigo-800 font-medium inline-flex items-center gap-1"
                      >
                        <Download className="w-3 h-3" />
                        <span>Download Artifact</span>
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
