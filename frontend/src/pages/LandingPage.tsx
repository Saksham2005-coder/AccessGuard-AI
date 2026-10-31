import { Link } from "react-router-dom";
import {
  Shield,
  ArrowRight,
  Lock,
} from "lucide-react";
import { useAuthStore } from "../store/authStore";
import { ThemeToggle } from "../components/ui/ThemeToggle";

export function LandingPage() {
  const { isAuthenticated } = useAuthStore();

  return (
    <div className="min-h-screen bg-[var(--bg-app)] text-[var(--text-primary)] flex flex-col selection:bg-[var(--electric-blue)]/20 selection:text-[var(--text-primary)]">
      {/* Navigation Header */}
      <header className="sticky top-0 z-40 w-full border-b border-[var(--border-graphite)] bg-[var(--bg-sidebar)]/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[var(--electric-blue)]/15 border border-[var(--electric-blue)]/30 text-[var(--electric-blue)] shadow-sm">
              <Shield className="h-5 w-5" />
            </div>
            <span className="font-bold text-lg tracking-tight text-[var(--text-primary)]">
              AccessGuard <span className="text-[var(--electric-blue)]">AI</span>
            </span>
          </div>

          <div className="flex items-center gap-4">
            <ThemeToggle />
            {isAuthenticated ? (
              <Link
                to="/app/overview"
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold text-[var(--bg-app)] bg-[var(--electric-blue)] hover:bg-[var(--electric-hover)] rounded-lg shadow-sm transition-colors"
              >
                Go to Dashboard
                <ArrowRight className="h-4 w-4" />
              </Link>
            ) : (
              <>
                <Link
                  to="/login"
                  className="px-3.5 py-1.5 text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
                >
                  Sign In
                </Link>
                <Link
                  to="/register"
                  className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold text-[var(--bg-app)] bg-[var(--electric-blue)] hover:bg-[var(--electric-hover)] rounded-lg shadow-sm transition-colors"
                >
                  Get Started
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20 sm:py-28 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[var(--border-graphite)] bg-[var(--bg-card)] text-xs text-[var(--text-secondary)] mb-6 shadow-sm">
          <span className="flex h-2 w-2 rounded-full bg-emerald-400" />
          <span>WCAG 2.2 AA & Section 508 Automated Compliance</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-[var(--text-primary)] leading-[1.15]">
          Automated Web Accessibility <br className="hidden sm:inline" />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-400 to-cyan-300">
            Scanning & AI-Assisted Remediation
          </span>
        </h1>

        <p className="mt-6 text-lg sm:text-xl text-[var(--text-secondary)] max-w-3xl mx-auto leading-relaxed">
          AccessGuard AI continuously audits target web applications using Playwright and axe-core,
          retrieves normative W3C guidance via RAG, and produces safe, human-reviewed code remediation
          patches evaluated in isolated sandboxes.
        </p>

        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            to={isAuthenticated ? "/app/overview" : "/register"}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 text-base font-semibold text-[var(--bg-app)] bg-[var(--electric-blue)] hover:bg-[var(--electric-hover)] rounded-xl shadow-lg transition-all"
          >
            {isAuthenticated ? "Launch Dashboard" : "Start Free Audit"}
            <ArrowRight className="h-5 w-5" />
          </Link>
          <Link
            to={isAuthenticated ? "/app/scans" : "/login"}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 text-base font-semibold text-[var(--text-primary)] bg-[var(--bg-card)] hover:bg-[var(--bg-elevated)] border border-[var(--border-graphite)] rounded-xl transition-all"
          >
            {isAuthenticated ? "View Active Scans" : "Sign In to Account"}
          </Link>
        </div>

        <div className="mt-6 text-xs text-[var(--text-muted)] flex items-center justify-center gap-4">
          <span>✓ Cryptographic DNS TXT verification</span>
          <span>•</span>
          <span>✓ Strict SSRF defense</span>
          <span>•</span>
          <span>✓ Isolated DOM snapshots</span>
        </div>
      </section>

      {/* 5-Step Workflow Section */}
      <section className="py-16 bg-[var(--bg-card)]/50 border-y border-[var(--border-graphite)]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-14">
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-[var(--text-primary)]">
              The 5-Step Remediation Lifecycle
            </h2>
            <p className="mt-3 text-sm sm:text-base text-[var(--text-secondary)]">
              From automated headless browser detection to post-remediation regression testing.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
            <div className="rounded-xl border border-[var(--border-graphite)] bg-[var(--bg-card)] p-5 flex flex-col">
              <div className="h-8 w-8 rounded-lg bg-sky-500/15 border border-sky-500/30 text-sky-400 flex items-center justify-center font-bold text-sm mb-4">
                1
              </div>
              <h3 className="font-semibold text-base text-[var(--text-primary)] mb-2">Scan</h3>
              <p className="text-xs text-[var(--text-secondary)] leading-relaxed flex-1">
                Playwright and locally bundled axe-core crawl authorized domains within strict depth and rate bounds.
              </p>
            </div>

            <div className="rounded-xl border border-[var(--border-graphite)] bg-[var(--bg-card)] p-5 flex flex-col">
              <div className="h-8 w-8 rounded-lg bg-cyan-500/15 border border-cyan-500/30 text-cyan-400 flex items-center justify-center font-bold text-sm mb-4">
                2
              </div>
              <h3 className="font-semibold text-base text-[var(--text-primary)] mb-2">Understand</h3>
              <p className="text-xs text-[var(--text-secondary)] leading-relaxed flex-1">
                The RAG system retrieves dense and lexical citations from official W3C WCAG 2.2 standards and techniques.
              </p>
            </div>

            <div className="rounded-xl border border-[var(--border-graphite)] bg-[var(--bg-card)] p-5 flex flex-col">
              <div className="h-8 w-8 rounded-lg bg-indigo-500/15 border border-indigo-500/30 text-indigo-400 flex items-center justify-center font-bold text-sm mb-4">
                3
              </div>
              <h3 className="font-semibold text-base text-[var(--text-primary)] mb-2">Propose</h3>
              <p className="text-xs text-[var(--text-secondary)] leading-relaxed flex-1">
                AI generates grounded code patches and HTML modifications adhering to strict patch allowlists.
              </p>
            </div>

            <div className="rounded-xl border border-[var(--border-graphite)] bg-[var(--bg-card)] p-5 flex flex-col">
              <div className="h-8 w-8 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 flex items-center justify-center font-bold text-sm mb-4">
                4
              </div>
              <h3 className="font-semibold text-base text-[var(--text-primary)] mb-2">Review</h3>
              <p className="text-xs text-[var(--text-secondary)] leading-relaxed flex-1">
                Humans-in-the-loop inspect side-by-side diffs, accept proposals, or provide mandatory rejection feedback.
              </p>
            </div>

            <div className="rounded-xl border border-[var(--border-graphite)] bg-[var(--bg-card)] p-5 flex flex-col">
              <div className="h-8 w-8 rounded-lg bg-purple-500/15 border border-purple-500/30 text-purple-400 flex items-center justify-center font-bold text-sm mb-4">
                5
              </div>
              <h3 className="font-semibold text-base text-[var(--text-primary)] mb-2">Validate</h3>
              <p className="text-xs text-[var(--text-secondary)] leading-relaxed flex-1">
                Patches are applied only to an isolated snapshot and re-audited to report resolved and remaining issues.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Security & Isolation Callout */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto">
        <div className="rounded-2xl border border-[var(--border-graphite)] bg-[var(--bg-sidebar)] p-8 sm:p-12 relative overflow-hidden">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <div className="max-w-2xl">
              <div className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[var(--electric-blue)] mb-3">
                <Lock className="h-4 w-4" />
                <span>Enterprise Security Safeguards</span>
              </div>
              <h2 className="text-xl sm:text-2xl font-bold text-[var(--text-primary)]">
                Built with Zero-Trust Domain Authorization & Sandbox Isolation
              </h2>
              <p className="mt-3 text-sm text-[var(--text-secondary)] leading-relaxed">
                We strictly enforce DNS TXT ownership challenge validation before any crawler execution begins.
                Snapshot re-audits execute within sandboxed headless browser sessions that prohibit external network egress,
                ensuring production code and customer data are never exposed or compromised.
              </p>
            </div>

            <Link
              to={isAuthenticated ? "/app/overview" : "/register"}
              className="shrink-0 inline-flex items-center gap-2 px-5 py-3 text-sm font-semibold text-[var(--bg-app)] bg-[var(--electric-blue)] hover:bg-[var(--electric-hover)] rounded-xl transition-colors"
            >
              Get Started Now
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* Honest Compliance Notice */}
      <section className="py-8 px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto text-center border-t border-[var(--border-graphite)]/50">
        <div className="rounded-lg bg-[var(--bg-elevated)] p-4 border border-[var(--border-graphite)] text-xs text-[var(--text-muted)] leading-relaxed">
          <strong className="text-[var(--text-secondary)]">Important Compliance Transparency Notice:</strong> Automated accessibility tools evaluate a subset of measurable WCAG success criteria (such as contrast, form labeling, image text alternatives, and landmark semantics). Automated scanning does not constitute full legal certification under the Americans with Disabilities Act (ADA), Section 508, or European Standard EN 301 549, and should be paired with human assistive technology evaluation.
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-auto border-t border-[var(--border-graphite)] bg-[var(--bg-sidebar)] py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-[var(--text-muted)]">
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-[var(--electric-blue)]" />
            <span>AccessGuard AI © 2026. All rights reserved.</span>
          </div>
          <div className="flex items-center gap-6">
            <Link to="/login" className="hover:text-[var(--text-primary)] transition-colors">
              Sign In
            </Link>
            <Link to="/register" className="hover:text-[var(--text-primary)] transition-colors">
              Create Account
            </Link>
            <a
              href="https://www.w3.org/WAI/standards-guidelines/wcag/"
              target="_blank"
              rel="noreferrer"
              className="hover:text-[var(--text-primary)] transition-colors"
            >
              W3C WCAG 2.2
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
