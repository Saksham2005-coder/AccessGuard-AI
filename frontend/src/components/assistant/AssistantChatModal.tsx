import { useState, useEffect, useRef } from 'react';
import {
  Bot,
  User,
  Send,
  Sparkles,
  BookOpen,
  CheckCircle2,
  AlertTriangle,
  Lightbulb,
  ArrowRight,
  ExternalLink,
  Trash2,
  RefreshCw,
} from 'lucide-react';
import { Dialog } from '../ui/Dialog';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import {
  sendAssistantChat,
  listProjectConversations,
  deleteConversation,
  AssistantMessageResponse,
} from '../../api/assistant';

interface AssistantChatModalProps {
  projectId: string;
  scanId?: string | null;
  targetUrl?: string;
  isOpen: boolean;
  onClose: () => void;
}

const QUICK_PROMPTS = [
  '🎯 What should I fix first?',
  '🎨 Explain the contrast issues',
  '⌨️ How can I improve keyboard navigation?',
  '📊 Give me an overview of scan findings',
];

export function AssistantChatModal({
  projectId,
  scanId,
  targetUrl,
  isOpen,
  onClose,
}: AssistantChatModalProps) {
  const [messages, setMessages] = useState<AssistantMessageResponse[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!projectId || !isOpen) return;

    let mounted = true;
    const loadRecentConversation = async () => {
      try {
        setLoading(true);
        setError(null);
        const convs = await listProjectConversations(projectId);
        if (mounted && convs.length > 0) {
          const recent = convs[0];
          setConversationId(recent.id);
          setMessages(recent.messages);
        }
      } catch (err: unknown) {
        if (mounted) {
          setError(err instanceof Error ? err.message : 'Failed to load conversation history');
        }
      } finally {
        if (mounted) setLoading(false);
      }
    };

    loadRecentConversation();
    return () => {
      mounted = false;
    };
  }, [projectId, isOpen]);

  useEffect(() => {
    if (typeof messagesEndRef.current?.scrollIntoView === 'function') {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const handleSendMessage = async (textToSend?: string) => {
    const text = textToSend || inputMessage;
    if (!text.trim() || submitting) return;

    // Optimistically show user message
    const optimisticUserMsg: AssistantMessageResponse = {
      id: `opt-${messages.length + 1}`,
      conversation_id: conversationId || '',
      role: 'user',
      content: text.trim(),
      structured_data: null,
      created_at: '',
    };

    setMessages((prev) => [...prev, optimisticUserMsg]);
    setInputMessage('');
    setSubmitting(true);
    setError(null);

    try {
      const response = await sendAssistantChat({
        project_id: projectId,
        scan_id: scanId,
        conversation_id: conversationId,
        message: text.trim(),
      });
      setConversationId(response.conversation_id);
      setMessages((prev) => [...prev, response]);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to get response from assistant');
    } finally {
      setSubmitting(false);
    }
  };

  const handleClearConversation = async () => {
    if (!conversationId) {
      setMessages([]);
      return;
    }

    try {
      await deleteConversation(conversationId);
      setConversationId(null);
      setMessages([]);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to clear conversation');
    }
  };

  if (!isOpen) return null;

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title="Conversational Accessibility Assistant"
      description={`Evidence-grounded WCAG intelligence for ${targetUrl || 'your project'}`}
      className="max-w-4xl"
    >
      <div className="flex flex-col h-[75vh]">
        {/* Context bar */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-800 text-xs text-slate-400">
          <div className="flex items-center gap-2">
            <Bot className="w-4 h-4 text-blue-400" />
            <span>Scope:</span>
            {scanId ? (
              <Badge variant="outline" className="font-mono text-[11px]">
                Scan #{scanId.slice(0, 8)}
              </Badge>
            ) : (
              <Badge variant="outline" className="text-[11px]">
                Latest Project Baseline
              </Badge>
            )}
            {targetUrl && (
              <span className="font-mono text-slate-300 truncate max-w-xs">{targetUrl}</span>
            )}
          </div>

          {messages.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClearConversation}
              className="text-xs text-slate-400 hover:text-red-400 flex items-center gap-1 h-7"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Clear Thread
            </Button>
          )}
        </div>

        {error && (
          <div className="p-3 my-2 bg-red-900/30 border border-red-700/50 rounded-lg text-red-300 text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Message Thread */}
        <div className="flex-1 overflow-y-auto py-4 space-y-4 pr-1">
          {loading ? (
            <div className="flex items-center justify-center h-48 text-slate-400 text-sm gap-2">
              <RefreshCw className="w-4 h-4 animate-spin text-blue-400" />
              Loading conversation context...
            </div>
          ) : messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center p-6 space-y-4">
              <div className="w-12 h-12 rounded-full bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                <Sparkles className="w-6 h-6" />
              </div>
              <div className="max-w-md space-y-1">
                <h4 className="text-sm font-semibold text-slate-200">How can I assist your accessibility engineering?</h4>
                <p className="text-xs text-slate-400">
                  Ask questions about specific violations, WCAG 2.2 success criteria, or remediation priorities grounded in your audit evidence.
                </p>
              </div>

              {/* Quick Prompts */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-lg pt-2">
                {QUICK_PROMPTS.map((prompt) => (
                  <button
                    key={prompt}
                    type="button"
                    onClick={() => handleSendMessage(prompt.slice(2).trim())}
                    className="p-2.5 text-left text-xs bg-slate-900/80 hover:bg-slate-800 border border-slate-800 rounded-lg text-slate-300 transition-colors"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.role === 'assistant' && (
                  <div className="w-7 h-7 rounded-full bg-blue-600/20 border border-blue-500/30 flex items-center justify-center shrink-0 text-blue-400 mt-1">
                    <Bot className="w-4 h-4" />
                  </div>
                )}

                <div
                  className={`max-w-[85%] rounded-xl p-4 text-xs space-y-3 ${
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white ml-12'
                      : 'bg-slate-900/90 border border-slate-800 text-slate-200 mr-4'
                  }`}
                >
                  {/* Message content */}
                  <div className="whitespace-pre-wrap leading-relaxed font-sans">{msg.content}</div>

                  {/* Structured data rendering for assistant */}
                  {msg.role === 'assistant' && msg.structured_data && (
                    <div className="space-y-3 pt-2 border-t border-slate-800/80 text-xs">
                      {/* Observed Facts */}
                      {msg.structured_data.observed_facts.length > 0 && (
                        <div className="bg-slate-950/60 p-2.5 rounded border border-slate-800 space-y-1">
                          <div className="text-[11px] font-semibold text-blue-400 uppercase tracking-wider flex items-center gap-1">
                            <CheckCircle2 className="w-3.5 h-3.5 text-blue-400" />
                            Observed Facts
                          </div>
                          {msg.structured_data.observed_facts.map((fact, idx) => (
                            <div key={idx} className="text-slate-300 pl-4 relative before:content-['•'] before:absolute before:left-1 before:text-blue-400">
                              {fact}
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Guidance Notes */}
                      {msg.structured_data.guidance_notes.length > 0 && (
                        <div className="bg-slate-950/60 p-2.5 rounded border border-slate-800 space-y-1">
                          <div className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider flex items-center gap-1">
                            <Lightbulb className="w-3.5 h-3.5 text-emerald-400" />
                            Remediation Guidance
                          </div>
                          {msg.structured_data.guidance_notes.map((guide, idx) => (
                            <div key={idx} className="text-slate-300 pl-4 relative before:content-['•'] before:absolute before:left-1 before:text-emerald-400">
                              {guide}
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Evidence Findings */}
                      {msg.structured_data.evidence_findings.length > 0 && (
                        <div>
                          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                            Grounded Findings Evidence ({msg.structured_data.evidence_findings.length})
                          </div>
                          <div className="grid grid-cols-1 gap-1.5">
                            {msg.structured_data.evidence_findings.map((f) => (
                              <div
                                key={f.finding_id}
                                className="bg-slate-950/80 p-2 rounded border border-slate-800/80 flex items-start justify-between gap-2"
                              >
                                <div className="space-y-0.5 min-w-0">
                                  <div className="font-mono text-blue-400 font-semibold truncate">
                                    {f.rule_id}
                                  </div>
                                  <div className="text-slate-400 truncate text-[11px]">
                                    {f.selector || f.description}
                                  </div>
                                </div>
                                <Badge
                                  variant={
                                    f.impact === 'critical'
                                      ? 'critical'
                                      : f.impact === 'serious'
                                      ? 'serious'
                                      : 'moderate'
                                  }
                                  className="text-[10px] shrink-0"
                                >
                                  {f.impact}
                                </Badge>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* WCAG Citations */}
                      {msg.structured_data.wcag_citations.length > 0 && (
                        <div>
                          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5 flex items-center gap-1">
                            <BookOpen className="w-3 h-3 text-purple-400" />
                            Authoritative Citations
                          </div>
                          <div className="flex flex-wrap gap-1.5">
                            {msg.structured_data.wcag_citations.map((c) => (
                              <a
                                key={c.criterion_id}
                                href={c.url || '#'}
                                target="_blank"
                                rel="noreferrer"
                                className="inline-flex items-center gap-1 px-2 py-1 bg-purple-950/40 hover:bg-purple-900/50 border border-purple-800/50 rounded text-purple-300 text-[11px] transition-colors"
                              >
                                <span>WCAG {c.criterion_id}: {c.title}</span>
                                {c.url && <ExternalLink className="w-2.5 h-2.5 opacity-70" />}
                              </a>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Suggested Action */}
                      {msg.structured_data.suggested_action && (
                        <div className="p-2 bg-blue-950/30 border border-blue-900/40 rounded flex items-center gap-2 text-blue-300">
                          <ArrowRight className="w-3.5 h-3.5 shrink-0 text-blue-400" />
                          <span className="font-medium">{msg.structured_data.suggested_action}</span>
                        </div>
                      )}

                      {/* Limitations Notice */}
                      <div className="text-[10px] text-slate-500 italic pt-1">
                        ⚠️ {msg.structured_data.limitations_notice}
                      </div>
                    </div>
                  )}
                </div>

                {msg.role === 'user' && (
                  <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center shrink-0 text-white mt-1">
                    <User className="w-4 h-4" />
                  </div>
                )}
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="pt-3 border-t border-slate-800 flex items-center gap-2"
        >
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Ask about accessibility violations, remediation priority, or WCAG criteria..."
            disabled={submitting}
            className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 disabled:opacity-50"
          />
          <Button
            type="submit"
            disabled={!inputMessage.trim() || submitting}
            className="px-4 py-2 gap-1.5 text-xs"
          >
            {submitting ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Send className="w-3.5 h-3.5" />
            )}
            <span>Send</span>
          </Button>
        </form>
      </div>
    </Dialog>
  );
}
