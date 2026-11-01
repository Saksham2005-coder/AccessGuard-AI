import { useState, useEffect } from 'react';
import {
  GitPullRequest,
  CheckCircle2,
  AlertTriangle,
  Copy,
  Check,
  RefreshCw,
  Trash2,
  Play,
  FileText,
  Key,
} from 'lucide-react';
import { Dialog } from '../ui/Dialog';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Skeleton } from '../ui/Skeleton';
import {
  getProjectIntegration,
  connectProjectRepo,
  disconnectProjectRepo,
  listProjectReviews,
  triggerTestReview,
  GitHubIntegration,
  GitHubReviewRecord,
} from '../../api/github';
import { Project } from '../../api/projects';

interface GitHubIntegrationModalProps {
  project: Project | null;
  isOpen: boolean;
  onClose: () => void;
}

export function GitHubIntegrationModal({
  project,
  isOpen,
  onClose,
}: GitHubIntegrationModalProps) {
  const [integration, setIntegration] = useState<GitHubIntegration | null>(null);
  const [reviews, setReviews] = useState<GitHubReviewRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [testingReview, setTestingReview] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Form state
  const [repoOwner, setRepoOwner] = useState('');
  const [repoName, setRepoName] = useState('');
  const [accessToken, setAccessToken] = useState('');
  const [targetBranch, setTargetBranch] = useState('main');
  const [autoReviewPrs, setAutoReviewPrs] = useState(true);

  // Active review detail drawer
  const [selectedReview, setSelectedReview] = useState<GitHubReviewRecord | null>(null);

  // Copy states
  const [copiedUrl, setCopiedUrl] = useState(false);
  const [copiedSecret, setCopiedSecret] = useState(false);

  useEffect(() => {
    if (!project || !isOpen) return;

    let mounted = true;
    const fetchIntegrationData = async () => {
      try {
        setError(null);
        setSuccess(null);
        const [integ, revs] = await Promise.all([
          getProjectIntegration(project.id),
          listProjectReviews(project.id).catch(() => []),
        ]);
        if (mounted) {
          setIntegration(integ);
          setReviews(revs);
          if (integ) {
            setRepoOwner(integ.repo_owner);
            setRepoName(integ.repo_name);
            setTargetBranch(integ.target_branch);
            setAutoReviewPrs(integ.auto_review_prs);
          }
        }
      } catch (err: unknown) {
        if (mounted) {
          const msg = err instanceof Error ? err.message : 'Failed to load GitHub integration details';
          setError(msg);
        }
      } finally {
        if (mounted) setLoading(false);
      }
    };

    fetchIntegrationData();
    return () => {
      mounted = false;
    };
  }, [project, isOpen]);

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!project) return;
    if (!repoOwner.trim() || !repoName.trim()) {
      setError('Repository owner and name are required.');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      const res = await connectProjectRepo(project.id, {
        repo_owner: repoOwner.trim(),
        repo_name: repoName.trim(),
        access_token: accessToken.trim() || undefined,
        target_branch: targetBranch.trim() || 'main',
        auto_review_prs: autoReviewPrs,
      });
      setIntegration(res);
      setSuccess('GitHub repository connected successfully! Webhook secret generated.');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to connect GitHub repository');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDisconnect = async () => {
    if (!project || !window.confirm('Are you sure you want to disconnect this GitHub repository?')) return;

    try {
      setSubmitting(true);
      await disconnectProjectRepo(project.id);
      setIntegration(null);
      setReviews([]);
      setSuccess('GitHub integration disconnected.');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to disconnect integration');
    } finally {
      setSubmitting(false);
    }
  };

  const handleTriggerTest = async () => {
    if (!project) return;

    try {
      setTestingReview(true);
      setError(null);
      const review = await triggerTestReview(project.id, {
        pr_number: 1,
        pr_title: 'Automated Accessibility Pull Request Review',
      });
      setReviews((prev) => [review, ...prev]);
      setSelectedReview(review);
      setSuccess('Test PR accessibility review generated from latest audit findings!');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to generate test review');
    } finally {
      setTestingReview(false);
    }
  };

  const fullWebhookUrl = typeof window !== 'undefined'
    ? `${window.location.origin}/api/v1/github/webhook`
    : 'http://localhost:8000/api/v1/github/webhook';

  const copyToClipboard = async (text: string, isUrl: boolean) => {
    try {
      await navigator.clipboard.writeText(text);
      if (isUrl) {
        setCopiedUrl(true);
        setTimeout(() => setCopiedUrl(false), 2000);
      } else {
        setCopiedSecret(true);
        setTimeout(() => setCopiedSecret(false), 2000);
      }
    } catch {
      // Fallback
    }
  };

  if (!isOpen) return null;

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title="GitHub Pull Request Integration"
      description={`Project: ${project?.name || ''} (${project?.base_domain || ''})`}
      className="max-w-4xl"
    >
      <div className="space-y-5">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <GitPullRequest className="w-5 h-5 text-blue-400" />
            <span className="text-sm font-semibold text-slate-200">Integration Status:</span>
            {integration ? (
              <Badge variant="success">Connected</Badge>
            ) : (
              <Badge variant="moderate">Unlinked</Badge>
            )}
          </div>
        </div>

        {error && (
          <div className="p-3 bg-red-900/30 border border-red-700/50 rounded-lg text-red-300 text-sm flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="p-3 bg-emerald-900/30 border border-emerald-700/50 rounded-lg text-emerald-300 text-sm flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{success}</span>
          </div>
        )}

        {loading ? (
          <div className="space-y-4 py-4">
            <Skeleton className="h-28 w-full" />
            <Skeleton className="h-40 w-full" />
          </div>
        ) : (
          <div className="space-y-6">
            {/* If Connected */}
            {integration ? (
              <div className="space-y-5">
                <div className="bg-slate-900/70 border border-slate-800 rounded-lg p-5">
                  <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-800">
                    <div>
                      <div className="text-xs uppercase tracking-wider text-slate-400">Connected Repository</div>
                      <div className="text-lg font-bold text-slate-100 flex items-center gap-2 mt-0.5">
                        <GitPullRequest className="w-5 h-5 text-blue-400" />
                        {integration.repo_owner} / {integration.repo_name}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleTriggerTest}
                        disabled={testingReview}
                        className="text-xs flex items-center gap-1.5"
                      >
                        {testingReview ? (
                          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <Play className="w-3.5 h-3.5 text-emerald-400" />
                        )}
                        Test PR Review
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={handleDisconnect}
                        disabled={submitting}
                        className="text-xs text-red-400 hover:text-red-300 hover:bg-red-950/40"
                      >
                        <Trash2 className="w-3.5 h-3.5 mr-1" />
                        Disconnect
                      </Button>
                    </div>
                  </div>

                  {/* Webhook details */}
                  <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-slate-950/60 p-3 rounded-md border border-slate-800/80">
                      <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                        <span>Payload URL</span>
                        <button
                          type="button"
                          onClick={() => copyToClipboard(fullWebhookUrl, true)}
                          className="text-blue-400 hover:text-blue-300 flex items-center gap-1 text-[11px]"
                        >
                          {copiedUrl ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                          {copiedUrl ? 'Copied' : 'Copy'}
                        </button>
                      </div>
                      <div className="text-xs font-mono text-slate-200 truncate bg-slate-900 px-2 py-1.5 rounded border border-slate-800">
                        {fullWebhookUrl}
                      </div>
                    </div>

                    <div className="bg-slate-950/60 p-3 rounded-md border border-slate-800/80">
                      <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                        <span>HMAC Secret</span>
                        <button
                          type="button"
                          onClick={() =>
                            copyToClipboard(
                              integration.webhook_secret || integration.webhook_secret_preview,
                              false
                            )
                          }
                          className="text-blue-400 hover:text-blue-300 flex items-center gap-1 text-[11px]"
                        >
                          {copiedSecret ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                          {copiedSecret ? 'Copied' : 'Copy'}
                        </button>
                      </div>
                      <div className="text-xs font-mono text-slate-200 truncate bg-slate-900 px-2 py-1.5 rounded border border-slate-800">
                        {integration.webhook_secret || integration.webhook_secret_preview}
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 text-xs text-slate-400 bg-blue-950/20 border border-blue-900/30 p-3 rounded">
                    💡 <strong>Setup in GitHub:</strong> In your GitHub repository, navigate to <strong>Settings → Webhooks → Add webhook</strong>.
                    Paste the Payload URL above, set Content Type to <code>application/json</code>, enter the HMAC Secret, and select <strong>Let me select individual events → Pull requests</strong>.
                  </div>
                </div>

                {/* Review History */}
                <div>
                  <h4 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
                    <FileText className="w-4 h-4 text-blue-400" />
                    Pull Request Review Events ({reviews.length})
                  </h4>

                  {reviews.length === 0 ? (
                    <div className="text-center py-8 border border-dashed border-slate-800 rounded-lg text-slate-400 text-sm">
                      No PR reviews recorded yet. Open a pull request on your linked GitHub repo or click <strong>Test PR Review</strong> above.
                    </div>
                  ) : (
                    <div className="border border-slate-800 rounded-lg overflow-hidden">
                      <table className="w-full text-left text-xs text-slate-300">
                        <thead className="bg-slate-900/80 text-slate-400 uppercase font-semibold border-b border-slate-800">
                          <tr>
                            <th className="px-4 py-2.5">PR #</th>
                            <th className="px-4 py-2.5">Title</th>
                            <th className="px-4 py-2.5">Author</th>
                            <th className="px-4 py-2.5">Commit</th>
                            <th className="px-4 py-2.5">Status</th>
                            <th className="px-4 py-2.5 text-right">Actions</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/60">
                          {reviews.map((r) => (
                            <tr key={r.id} className="hover:bg-slate-900/40">
                              <td className="px-4 py-2.5 font-mono text-blue-400">#{r.pr_number}</td>
                              <td className="px-4 py-2.5 font-medium max-w-xs truncate">{r.pr_title}</td>
                              <td className="px-4 py-2.5 text-slate-400">{r.pr_author || 'n/a'}</td>
                              <td className="px-4 py-2.5 font-mono text-slate-400">{r.head_sha.slice(0, 7)}</td>
                              <td className="px-4 py-2.5">
                                <Badge
                                  variant={
                                    r.status === 'reviewed'
                                      ? 'success'
                                      : r.status === 'skipped'
                                      ? 'moderate'
                                      : 'serious'
                                  }
                                >
                                  {r.status}
                                </Badge>
                              </td>
                              <td className="px-4 py-2.5 text-right">
                                {r.summary_markdown && (
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => setSelectedReview(r)}
                                    className="text-xs h-7 text-blue-400 hover:text-blue-300"
                                  >
                                    View Report
                                  </Button>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              /* Connect Form */
              <form onSubmit={handleConnect} className="space-y-4">
                <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-5 space-y-4">
                  <div className="text-sm font-semibold text-slate-200">Connect GitHub Repository</div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="repo-owner-input" className="block text-xs font-medium text-slate-300 mb-1">
                        Repository Owner / Org <span className="text-red-400">*</span>
                      </label>
                      <input
                        id="repo-owner-input"
                        type="text"
                        value={repoOwner}
                        onChange={(e) => setRepoOwner(e.target.value)}
                        placeholder="e.g. acme-corp"
                        className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded text-sm text-slate-100 focus:outline-none focus:border-blue-500"
                        required
                      />
                    </div>
                    <div>
                      <label htmlFor="repo-name-input" className="block text-xs font-medium text-slate-300 mb-1">
                        Repository Name <span className="text-red-400">*</span>
                      </label>
                      <input
                        id="repo-name-input"
                        type="text"
                        value={repoName}
                        onChange={(e) => setRepoName(e.target.value)}
                        placeholder="e.g. web-app"
                        className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded text-sm text-slate-100 focus:outline-none focus:border-blue-500"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="target-branch-input" className="block text-xs font-medium text-slate-300 mb-1">Target Branch</label>
                    <input
                      id="target-branch-input"
                      type="text"
                      value={targetBranch}
                      onChange={(e) => setTargetBranch(e.target.value)}
                      placeholder="main"
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded text-sm text-slate-100 focus:outline-none focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label htmlFor="access-token-input" className="block text-xs font-medium text-slate-300 mb-1 flex items-center justify-between">
                      <span className="flex items-center gap-1">
                        <Key className="w-3.5 h-3.5 text-blue-400" />
                        GitHub Personal Access Token (Optional)
                      </span>
                      <span className="text-[11px] text-slate-500">For posting review comments</span>
                    </label>
                    <input
                      id="access-token-input"
                      type="password"
                      value={accessToken}
                      onChange={(e) => setAccessToken(e.target.value)}
                      placeholder="ghp_..."
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded text-sm text-slate-100 focus:outline-none focus:border-blue-500 font-mono text-xs"
                    />
                    <div className="text-[11px] text-slate-500 mt-1">
                      Token requires <code>pull_requests:write</code> permissions. If omitted, reviews are generated and persisted within AccessGuard.
                    </div>
                  </div>

                  <div className="flex items-center gap-2 pt-2">
                    <input
                      id="auto-review-prs-check"
                      type="checkbox"
                      checked={autoReviewPrs}
                      onChange={(e) => setAutoReviewPrs(e.target.checked)}
                      className="rounded border-slate-700 bg-slate-950 text-blue-600 focus:ring-blue-500"
                    />
                    <label htmlFor="auto-review-prs-check" className="text-xs text-slate-300 cursor-pointer">
                      Automatically evaluate accessibility and post reviews for new PRs
                    </label>
                  </div>
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <Button variant="ghost" type="button" onClick={onClose} disabled={submitting}>
                    Cancel
                  </Button>
                  <Button variant="default" type="submit" disabled={submitting}>
                    {submitting ? 'Connecting...' : 'Connect Repository'}
                  </Button>
                </div>
              </form>
            )}
          </div>
        )}

        {/* Selected Review Markdown Drawer / Dialog */}
        {selectedReview && (
          <Dialog
            isOpen={!!selectedReview}
            onClose={() => setSelectedReview(null)}
            title={`PR #${selectedReview.pr_number}: ${selectedReview.pr_title}`}
            description={`Generated Review Markdown Comment (${selectedReview.head_sha.slice(0, 8)})`}
            className="max-w-2xl"
          >
            <div className="space-y-4">
              <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 text-xs font-mono whitespace-pre-wrap text-slate-300 max-h-96 overflow-y-auto">
                {selectedReview.summary_markdown}
              </div>
              <div className="flex justify-end">
                <Button variant="outline" size="sm" onClick={() => setSelectedReview(null)}>
                  Close
                </Button>
              </div>
            </div>
          </Dialog>
        )}
      </div>
    </Dialog>
  );
}
