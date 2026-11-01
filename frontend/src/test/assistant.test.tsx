import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AssistantChatModal } from '../components/assistant/AssistantChatModal';
import * as assistantApi from '../api/assistant';

const mockResponse: assistantApi.AssistantMessageResponse = {
  id: 'msg-asst-123',
  conversation_id: 'conv-123',
  role: 'assistant',
  content: 'Based on your audit, you should prioritize button-name and color-contrast.',
  structured_data: {
    observed_facts: ['Project has 4 total violations.'],
    guidance_notes: ['Add aria-label to icon buttons.'],
    evidence_findings: [
      {
        finding_id: 'find-1',
        rule_id: 'button-name',
        impact: 'critical',
        selector: 'button.icon',
        description: 'Missing accessible name',
      },
    ],
    wcag_citations: [
      {
        criterion_id: '4.1.2',
        title: 'Name, Role, Value',
        guidance: 'Ensure all components have names.',
        url: 'https://www.w3.org/WAI/WCAG22/Understanding/name-role-value.html',
      },
    ],
    suggested_action: 'Navigate to remediations page.',
    limitations_notice: 'Automated test limitation disclaimer.',
  },
  created_at: '2026-11-01T12:00:00Z',
};

describe('AssistantChatModal', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders initial welcome prompt and quick action buttons', async () => {
    vi.spyOn(assistantApi, 'listProjectConversations').mockResolvedValue([]);

    render(
      <AssistantChatModal
        projectId="proj-123"
        scanId="scan-123"
        targetUrl="https://example.com"
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Conversational Accessibility Assistant')).toBeDefined();
    });

    expect(screen.getByText(/How can I assist your accessibility engineering/i)).toBeDefined();
    expect(screen.getByText(/What should I fix first/i)).toBeDefined();
    expect(screen.getByText(/Explain the contrast issues/i)).toBeDefined();
  });

  it('submits user question and renders structured assistant answer', async () => {
    vi.spyOn(assistantApi, 'listProjectConversations').mockResolvedValue([]);
    const sendSpy = vi.spyOn(assistantApi, 'sendAssistantChat').mockResolvedValue(mockResponse);

    render(
      <AssistantChatModal
        projectId="proj-123"
        scanId="scan-123"
        targetUrl="https://example.com"
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Ask about accessibility violations/i)).toBeDefined();
    });

    const input = screen.getByPlaceholderText(/Ask about accessibility violations/i);
    fireEvent.change(input, { target: { value: 'What should I fix first?' } });
    fireEvent.click(screen.getByRole('button', { name: /Send/i }));

    await waitFor(() => {
      expect(sendSpy).toHaveBeenCalledWith({
        project_id: 'proj-123',
        scan_id: 'scan-123',
        conversation_id: null,
        message: 'What should I fix first?',
      });
    });

    await waitFor(() => {
      expect(screen.getByText(/Based on your audit, you should prioritize/i)).toBeDefined();
      expect(screen.getByText('Observed Facts')).toBeDefined();
      expect(screen.getByText('Project has 4 total violations.')).toBeDefined();
      expect(screen.getByText('Remediation Guidance')).toBeDefined();
      expect(screen.getByText('button-name')).toBeDefined();
      expect(screen.getByText(/WCAG 4.1.2: Name, Role, Value/i)).toBeDefined();
    });
  });

  it('allows clicking quick prompt pill to send question immediately', async () => {
    vi.spyOn(assistantApi, 'listProjectConversations').mockResolvedValue([]);
    const sendSpy = vi.spyOn(assistantApi, 'sendAssistantChat').mockResolvedValue(mockResponse);

    render(
      <AssistantChatModal
        projectId="proj-123"
        scanId="scan-123"
        targetUrl="https://example.com"
        isOpen={true}
        onClose={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Explain the contrast issues/i)).toBeDefined();
    });

    fireEvent.click(screen.getByText(/Explain the contrast issues/i));

    await waitFor(() => {
      expect(sendSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          project_id: 'proj-123',
          message: 'Explain the contrast issues',
        })
      );
    });
  });
});
