import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { GitHubIntegrationModal } from '../components/github/GitHubIntegrationModal';
import * as githubApi from '../api/github';
import { Project } from '../api/projects';

const mockProject: Project = {
  id: 'proj-github-123',
  name: 'Acme Portal',
  base_domain: 'acme.com',
  is_verified: true,
  latest_verification: null,
  created_at: '2026-11-01T12:00:00Z',
  updated_at: '2026-11-01T12:00:00Z',
  archived_at: null,
};

const mockIntegration: githubApi.GitHubIntegration = {
  id: 'integ-123',
  project_id: 'proj-github-123',
  repo_owner: 'acme-corp',
  repo_name: 'portal-frontend',
  installation_id: null,
  webhook_secret_preview: 'whsec_...1234',
  webhook_secret: 'whsec_full_secret_1234567890',
  webhook_url: '/api/v1/github/webhook',
  has_token: true,
  target_branch: 'main',
  enabled: true,
  auto_review_prs: true,
  created_at: '2026-11-01T12:00:00Z',
  updated_at: '2026-11-01T12:00:00Z',
};

const mockReviews: githubApi.GitHubReviewRecord[] = [
  {
    id: 'rev-1',
    integration_id: 'integ-123',
    project_id: 'proj-github-123',
    delivery_id: 'del-1',
    pr_number: 42,
    pr_title: 'Add checkout form',
    pr_author: 'alice',
    head_sha: 'a1b2c3d4e5f6',
    base_sha: '001122334455',
    scan_id: 'scan-1',
    status: 'reviewed',
    comment_id: 'comment-999',
    summary_markdown: '## 🛡️ AccessGuard AI — Accessibility Review\n\nAll clear!',
    error_message: null,
    created_at: '2026-11-01T12:30:00Z',
  },
];

describe('GitHubIntegrationModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders unlinked form when no repository is connected', async () => {
    vi.spyOn(githubApi, 'getProjectIntegration').mockResolvedValue(null);
    vi.spyOn(githubApi, 'listProjectReviews').mockResolvedValue([]);

    render(
      <GitHubIntegrationModal
        project={mockProject}
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Connect GitHub Repository')).toBeDefined();
    });

    expect(screen.getByText('Unlinked')).toBeDefined();
    expect(screen.getByLabelText(/Repository Owner/i)).toBeDefined();
    expect(screen.getByLabelText(/Repository Name/i)).toBeDefined();
  });

  it('renders connected repository info and webhook details when integration exists', async () => {
    vi.spyOn(githubApi, 'getProjectIntegration').mockResolvedValue(mockIntegration);
    vi.spyOn(githubApi, 'listProjectReviews').mockResolvedValue(mockReviews);

    render(
      <GitHubIntegrationModal
        project={mockProject}
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeDefined();
      expect(screen.getByText('acme-corp / portal-frontend')).toBeDefined();
    });

    expect(screen.getByText('whsec_full_secret_1234567890')).toBeDefined();
    expect(screen.getByText('#42')).toBeDefined();
    expect(screen.getByText('Add checkout form')).toBeDefined();
    expect(screen.getByText('reviewed')).toBeDefined();
  });

  it('allows submitting connection form to link a repository', async () => {
    vi.spyOn(githubApi, 'getProjectIntegration').mockResolvedValue(null);
    vi.spyOn(githubApi, 'listProjectReviews').mockResolvedValue([]);
    const connectSpy = vi.spyOn(githubApi, 'connectProjectRepo').mockResolvedValue(mockIntegration);

    render(
      <GitHubIntegrationModal
        project={mockProject}
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Connect GitHub Repository')).toBeDefined();
    });

    fireEvent.change(screen.getByLabelText(/Repository Owner/i), {
      target: { value: 'acme-corp' },
    });
    fireEvent.change(screen.getByLabelText(/Repository Name/i), {
      target: { value: 'portal-frontend' },
    });

    fireEvent.click(screen.getByRole('button', { name: /Connect Repository/i }));

    await waitFor(() => {
      expect(connectSpy).toHaveBeenCalledWith('proj-github-123', expect.objectContaining({
        repo_owner: 'acme-corp',
        repo_name: 'portal-frontend',
      }));
    });
  });

  it('displays markdown review drawer when clicking View Report', async () => {
    vi.spyOn(githubApi, 'getProjectIntegration').mockResolvedValue(mockIntegration);
    vi.spyOn(githubApi, 'listProjectReviews').mockResolvedValue(mockReviews);

    render(
      <GitHubIntegrationModal
        project={mockProject}
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('View Report')).toBeDefined();
    });

    fireEvent.click(screen.getByText('View Report'));

    await waitFor(() => {
      expect(screen.getByText(/All clear!/i)).toBeDefined();
    });
  });
});
