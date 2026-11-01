import React, { useEffect, useState, useRef } from "react";
import {
  getScreenReaderSimulationApi,
  ScreenReaderSimulationResponse,
  SemanticNode,
} from "../../api/screenReader";
import { ScanPageSummary } from "../../api/heatmap";

interface ScreenReaderSimulatorProps {
  scanId: string;
  pages: ScanPageSummary[];
  selectedPageId: string;
  onSelectPage: (pageId: string) => void;
  onInspectFinding?: (findingId: string) => void;
}

export const ScreenReaderSimulator: React.FC<ScreenReaderSimulatorProps> = ({
  scanId,
  pages,
  selectedPageId,
  onSelectPage,
  onInspectFinding,
}) => {
  const [data, setData] = useState<ScreenReaderSimulationResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"reading" | "headings" | "landmarks" | "interactive" | "hints">("reading");

  // Step-through playback state
  const [activeIndex, setActiveIndex] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(2500); // 2.5s per node

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);


  useEffect(() => {
    if (!selectedPageId) return;

    let isMounted = true;
    const fetchSimulation = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await getScreenReaderSimulationApi(scanId, selectedPageId);
        if (isMounted) {
          setData(res);
          setActiveIndex(0);
          setIsPlaying(false);
        }
      } catch (err: unknown) {
        if (isMounted) {
          const msg = err instanceof Error ? err.message : "Failed to load screen reader simulation";
          setError(msg);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchSimulation();

    return () => {
      isMounted = false;
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [scanId, selectedPageId]);

  // Handle auto-playback loop
  useEffect(() => {
    if (isPlaying && data && data.reading_order.length > 0) {
      timerRef.current = setInterval(() => {
        setActiveIndex((prev) => {
          if (prev >= data.reading_order.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, playbackSpeed);
    } else if (timerRef.current) {
      clearInterval(timerRef.current);
    }

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isPlaying, playbackSpeed, data]);

  const activeNode: SemanticNode | undefined = data?.reading_order[activeIndex];

  const formatSpeechAnnouncement = (node?: SemanticNode): string => {
    if (!node) return "No element selected";
    const roleCapitalized = node.role.charAt(0).toUpperCase() + node.role.slice(1);

    if (node.heading_level) {
      return `Heading level ${node.heading_level}, ${node.accessible_name || "unlabeled"}`;
    }

    if (node.landmark_type) {
      return `${roleCapitalized} landmark${node.accessible_name ? `, ${node.accessible_name}` : ""}`;
    }

    if (node.is_interactive) {
      const name = node.accessible_name || "unlabeled control";
      const expanded = node.attributes.aria_expanded ? ` (expanded)` : "";
      return `${roleCapitalized}, ${name}${expanded}`;
    }

    return `${roleCapitalized}: ${node.accessible_name || "unlabeled content"}`;
  };

  const handleNext = () => {
    if (!data) return;
    setActiveIndex((prev) => Math.min(prev + 1, data.reading_order.length - 1));
  };

  const handlePrev = () => {
    setActiveIndex((prev) => Math.max(prev - 1, 0));
  };

  const handleReset = () => {
    setActiveIndex(0);
    setIsPlaying(false);
  };

  return (
    <div className="space-y-6">
      {/* Top Header & Page Selector */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-xl bg-slate-900 border border-slate-800">
        <div>
          <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
            <span>Screen Reader Reading & Semantics Simulator</span>
            <span className="text-[11px] px-2 py-0.5 rounded-full bg-blue-950 border border-blue-800 text-blue-300 font-mono">
              DOM Preview
            </span>
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Structured step-through preview of browser accessibility semantics, landmarks, headings, and reading order.
          </p>
        </div>

        {pages.length > 1 && (
          <div className="flex items-center gap-2">
            <label htmlFor="sr-page-select" className="text-xs text-slate-400 font-medium">
              Page:
            </label>
            <select
              id="sr-page-select"
              value={selectedPageId}
              onChange={(e) => onSelectPage(e.target.value)}
              className="bg-slate-950 border border-slate-800 text-slate-200 text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:border-blue-500"
            >
              {pages.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.url}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Mandatory Enterprise Disclaimer Alert */}
      <div className="flex items-start gap-3 p-4 rounded-xl bg-blue-950/30 border border-blue-900/60 text-blue-200">
        <svg className="w-5 h-5 mt-0.5 text-blue-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <div className="text-xs leading-relaxed">
          <strong className="font-semibold text-blue-100">Screen-Reader-Oriented Preview: </strong>
          This preview inspects browser DOM semantics and reading order. It does not emulate real assistive technology software (NVDA, JAWS, VoiceOver, TalkBack). Speech announcements are browser approximations.
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-rose-950/50 border border-rose-800 text-sm text-rose-300">
          {error}
        </div>
      )}

      {loading && (
        <div className="flex flex-col items-center justify-center py-16 space-y-4">
          <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-slate-400">Extracting page semantic tree...</p>
        </div>
      )}

      {!loading && data && (
        <div className="space-y-4">
          {/* Sub Navigation Tabs */}
          <div className="flex border-b border-slate-800 pb-2 gap-2 overflow-x-auto text-xs">
            {[
              { id: "reading", label: `Sequential Reading Order (${data.reading_order.length})` },
              { id: "headings", label: `Headings Outline (${data.headings.length})` },
              { id: "landmarks", label: `Landmarks (${data.landmarks.length})` },
              { id: "interactive", label: `Interactive Controls (${data.interactive_elements.length})` },
              { id: "hints", label: `Review Hints (${data.review_hints.length})` },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as typeof activeTab)}
                className={`px-3 py-1.5 font-medium rounded-lg transition-colors whitespace-nowrap ${
                  activeTab === tab.id
                    ? "bg-blue-600 text-white"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab 1: Sequential Reading Order with Playback Controls */}
          {activeTab === "reading" && (
            <div className="space-y-4">
              {/* Playback Control Bar */}
              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="flex items-center gap-2">
                  <button
                    onClick={handlePrev}
                    disabled={activeIndex === 0}
                    className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium disabled:opacity-40 transition"
                    title="Previous Node"
                  >
                    ◀ Prev
                  </button>
                  <button
                    onClick={() => setIsPlaying(!isPlaying)}
                    className="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow transition"
                  >
                    {isPlaying ? "⏸ Pause" : "▶ Auto-Step"}
                  </button>
                  <button
                    onClick={handleNext}
                    disabled={activeIndex >= data.reading_order.length - 1}
                    className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium disabled:opacity-40 transition"
                    title="Next Node"
                  >
                    Next ▶
                  </button>
                  <button
                    onClick={handleReset}
                    className="px-2.5 py-1.5 rounded-lg text-slate-400 hover:text-slate-200 text-xs transition"
                  >
                    Reset
                  </button>
                </div>

                <div className="flex items-center gap-3 text-xs">
                  <span className="text-slate-400 font-mono">
                    Node <strong className="text-slate-200">{activeIndex + 1}</strong> of {data.reading_order.length}
                  </span>
                  <div className="flex items-center gap-1.5">
                    <span className="text-slate-500">Speed:</span>
                    <select
                      value={playbackSpeed}
                      onChange={(e) => setPlaybackSpeed(Number(e.target.value))}
                      className="bg-slate-950 border border-slate-800 text-slate-300 text-xs rounded px-2 py-1"
                    >
                      <option value={1500}>Fast (1.5s)</option>
                      <option value={2500}>Normal (2.5s)</option>
                      <option value={4000}>Slow (4.0s)</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Speech Announcement Box */}
              <div className="p-4 rounded-xl bg-slate-950 border-2 border-blue-500/80 shadow-md space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-blue-400 font-semibold uppercase tracking-wider flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
                    Simulated Speech Output
                  </span>
                  {activeNode?.associated_finding_id && onInspectFinding && (
                    <button
                      onClick={() => onInspectFinding(activeNode.associated_finding_id!)}
                      className="text-[11px] px-2 py-0.5 rounded bg-rose-950 border border-rose-800 text-rose-300 font-medium hover:bg-rose-900 transition"
                    >
                      Inspect Linked Finding
                    </button>
                  )}
                </div>
                <div className="p-3 rounded-lg bg-slate-900 text-slate-100 font-mono text-sm leading-relaxed">
                  "{formatSpeechAnnouncement(activeNode)}"
                </div>
                {activeNode?.potential_issue && (
                  <div className="text-xs text-rose-400 font-medium flex items-center gap-1.5">
                    <span>⚠ Review Alert:</span>
                    <span>{activeNode.potential_issue}</span>
                  </div>
                )}
              </div>

              {/* Reading Order List */}
              <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
                {data.reading_order.map((node, idx) => (
                  <div
                    key={idx}
                    onClick={() => setActiveIndex(idx)}
                    className={`p-3 rounded-xl border text-xs cursor-pointer transition flex items-center justify-between gap-3 ${
                      activeIndex === idx
                        ? "bg-slate-900 border-blue-500 shadow-sm"
                        : "bg-slate-900/60 border-slate-800/80 hover:border-slate-700"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <span className="w-6 text-center font-mono text-slate-500 font-bold">
                        {idx + 1}
                      </span>
                      <span className="px-2 py-0.5 rounded bg-slate-950 border border-slate-800 font-mono text-[11px] text-blue-300 font-semibold">
                        {node.role}
                      </span>
                      <span className="text-slate-200 font-medium truncate max-w-md">
                        {node.accessible_name || <em className="text-slate-500">(unlabeled)</em>}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      {node.heading_level && (
                        <span className="px-2 py-0.5 rounded bg-emerald-950 border border-emerald-800 text-emerald-300 text-[10px] font-mono">
                          H{node.heading_level}
                        </span>
                      )}
                      {node.landmark_type && (
                        <span className="px-2 py-0.5 rounded bg-purple-950 border border-purple-800 text-purple-300 text-[10px] font-mono">
                          {node.landmark_type}
                        </span>
                      )}
                      {node.potential_issue && (
                        <span className="px-2 py-0.5 rounded bg-rose-950 border border-rose-800 text-rose-300 text-[10px] font-semibold">
                          Alert
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tab 2: Headings Outline */}
          {activeTab === "headings" && (
            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
              <h4 className="text-sm font-semibold text-slate-200">
                Heading Outline Structure ({data.headings.length} headings)
              </h4>
              {data.headings.length === 0 ? (
                <p className="text-xs text-slate-400">No headings detected on this page.</p>
              ) : (
                <div className="space-y-2">
                  {data.headings.map((h, idx) => (
                    <div
                      key={idx}
                      style={{ paddingLeft: `${(h.level - 1) * 1.5}rem` }}
                      className="flex items-center gap-2.5 py-1 text-xs"
                    >
                      <span className="px-2 py-0.5 rounded bg-blue-950 border border-blue-800 text-blue-300 font-mono font-bold text-[11px]">
                        H{h.level}
                      </span>
                      <span className="text-slate-200 font-medium">{h.text}</span>
                      {h.is_skipped && (
                        <span className="px-2 py-0.5 rounded bg-amber-950 border border-amber-800 text-amber-300 text-[10px] font-semibold">
                          Level Skip Alert
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Tab 3: Landmarks */}
          {activeTab === "landmarks" && (
            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
              <h4 className="text-sm font-semibold text-slate-200">
                Landmarks Outline ({data.landmarks.length} landmarks)
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                {data.landmarks.map((lm, idx) => (
                  <div key={idx} className="p-3 rounded-lg bg-slate-950 border border-slate-800 space-y-1">
                    <span className="px-2 py-0.5 rounded bg-purple-950 border border-purple-800 text-purple-300 font-mono text-[11px] font-semibold">
                      {lm.landmark_type}
                    </span>
                    <p className="text-slate-300 font-medium mt-1">
                      {lm.accessible_name || "(Implicit landmark container)"}
                    </p>
                    <code className="text-[11px] text-slate-500 block truncate">{lm.selector}</code>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tab 4: Interactive Controls */}
          {activeTab === "interactive" && (
            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
              <h4 className="text-sm font-semibold text-slate-200">
                Interactive Controls ({data.interactive_elements.length})
              </h4>
              <div className="space-y-2 max-h-96 overflow-y-auto pr-1 text-xs">
                {data.interactive_elements.map((el, idx) => (
                  <div key={idx} className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-between gap-3">
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded bg-blue-950 border border-blue-800 text-blue-300 font-mono font-medium text-[11px]">
                          {el.role}
                        </span>
                        <span className="font-medium text-slate-200">
                          {el.accessible_name || <span className="text-rose-400 italic">Missing accessible name</span>}
                        </span>
                      </div>
                      <code className="text-[11px] text-slate-500 block truncate">{el.selector}</code>
                    </div>

                    {!el.has_name && (
                      <span className="px-2 py-0.5 rounded bg-rose-950 border border-rose-800 text-rose-300 text-[10px] font-bold">
                        Unlabeled
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tab 5: Review Hints */}
          {activeTab === "hints" && (
            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
              <h4 className="text-sm font-semibold text-slate-200">
                Heuristic Review Hints ({data.review_hints.length})
              </h4>
              {data.review_hints.length === 0 ? (
                <p className="text-xs text-slate-400">No semantic review hints detected for this page.</p>
              ) : (
                <div className="space-y-2 text-xs">
                  {data.review_hints.map((hint, idx) => (
                    <div key={idx} className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex items-start justify-between gap-3">
                      <div className="space-y-1">
                        <span className="px-2 py-0.5 rounded bg-amber-950 border border-amber-800 text-amber-300 text-[10px] font-bold uppercase">
                          {hint.category.replace("_", " ")}
                        </span>
                        <p className="text-slate-200 font-medium">{hint.message}</p>
                        <code className="text-[11px] text-slate-500 block truncate">{hint.selector}</code>
                      </div>

                      {hint.associated_finding_id && onInspectFinding && (
                        <button
                          onClick={() => onInspectFinding(hint.associated_finding_id!)}
                          className="px-2.5 py-1 rounded bg-blue-950 border border-blue-800 text-blue-300 hover:bg-blue-900 transition whitespace-nowrap"
                        >
                          View Finding
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
