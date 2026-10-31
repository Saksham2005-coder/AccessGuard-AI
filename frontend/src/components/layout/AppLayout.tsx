import { Suspense, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import {
  Activity,
  BookOpen,
  ChevronRight,
  FileText,
  FolderKanban,
  LayoutDashboard,
  LogOut,
  Menu,
  Radio,
  Settings,
  Shield,
  ShieldAlert,
  Sparkles,
  X,
} from "lucide-react";
import { cn } from "../../lib/utils";
import { useAuthStore } from "../../store/authStore";
import { ThemeToggle } from "../ui/ThemeToggle";

export interface NavItem {
  title: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

const navItems: NavItem[] = [
  { title: "Overview", href: "/app/overview", icon: LayoutDashboard },
  { title: "Projects", href: "/app/projects", icon: FolderKanban },
  { title: "Scans", href: "/app/scans", icon: Activity },
  { title: "Findings", href: "/app/findings", icon: ShieldAlert },
  { title: "AI Remediation", href: "/app/remediations", icon: Sparkles },
  { title: "Reports", href: "/app/reports", icon: FileText },
  { title: "Knowledge Base", href: "/app/knowledge", icon: BookOpen },
  { title: "Settings", href: "/app/settings", icon: Settings },
];

export interface AppLayoutProps {
  user?: {
    email?: string;
    display_name?: string;
  } | null;
  onLogout?: () => void;
}

export function AppLayout({ user: userProp, onLogout: onLogoutProp }: AppLayoutProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();
  const store = useAuthStore();

  const user = userProp !== undefined ? userProp : store.user;
  const onLogout = onLogoutProp !== undefined ? onLogoutProp : store.logout;

  const displayName = user?.display_name || user?.email?.split("@")[0] || "User";
  const userEmail = user?.email || "user@accessguard.ai";

  const currentNav = navItems.find((item) => location.pathname.startsWith(item.href)) || navItems[0];

  return (
    <div className="min-h-screen bg-[#111315] text-[#F3F4F6] flex flex-col md:flex-row antialiased selection:bg-[#38BDF8]/20 selection:text-[#F3F4F6]">
      {/* Accessible Skip Link */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:px-4 focus:py-2 focus:bg-[#38BDF8] focus:text-[#111315] focus:font-semibold focus:rounded-lg focus:shadow-xl focus:outline-none focus:ring-2 focus:ring-white"
      >
        Skip to main content
      </a>

      {/* Mobile Top Header */}
      <header className="md:hidden flex items-center justify-between px-4 py-3 bg-[#171A1F] border-b border-[#303741] sticky top-0 z-40">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#38BDF8]/15 border border-[#38BDF8]/30 text-[#38BDF8]">
            <Shield className="h-5 w-5" />
          </div>
          <span className="font-semibold text-sm tracking-tight text-[#F3F4F6]">
            AccessGuard AI
          </span>
        </div>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-1.5 rounded-lg text-[#9CA3AF] hover:text-[#F3F4F6] hover:bg-[#252C35] focus:outline-none focus:ring-2 focus:ring-[#38BDF8]"
            aria-label={mobileMenuOpen ? "Close navigation menu" : "Open navigation menu"}
            aria-expanded={mobileMenuOpen}
          >
            {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>
      </header>

      {/* Desktop Graphite Left Sidebar */}
      <aside className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0 z-30 bg-[#171A1F] border-r border-[#303741]">
        {/* Brand Identity Header */}
        <div className="flex h-16 items-center px-6 border-b border-[#303741] gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#38BDF8]/15 border border-[#38BDF8]/30 text-[#38BDF8] shadow-sm">
            <Shield className="h-5 w-5" />
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-1.5">
              <span className="font-semibold text-sm tracking-tight text-[#F3F4F6] leading-tight">
                AccessGuard AI
              </span>
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-[#38BDF8]" />
            </div>
            <span className="text-[11px] text-[#6B7280] font-medium tracking-wide">
              A11y Observability
            </span>
          </div>
        </div>

        {/* Navigation List */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto" aria-label="Main Navigation">
          <div className="px-3 pb-2 text-[10px] font-semibold tracking-wider uppercase text-[#6B7280]">
            Platform
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname.startsWith(item.href);
            return (
              <NavLink
                key={item.href}
                to={item.href}
                className={({ isActive: linkActive }) =>
                  cn(
                    "flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg transition-all group relative",
                    linkActive || isActive
                      ? "bg-[#38BDF8]/10 text-[#38BDF8] font-semibold border-l-2 border-[#38BDF8]"
                      : "text-[#9CA3AF] hover:bg-[#252C35] hover:text-[#F3F4F6]"
                  )
                }
              >
                <Icon
                  className={cn(
                    "h-4 w-4 shrink-0 transition-colors",
                    isActive ? "text-[#38BDF8]" : "text-[#6B7280] group-hover:text-[#F3F4F6]"
                  )}
                />
                <span>{item.title}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* User Profile & Account Footer */}
        <div className="p-3 border-t border-[#303741]">
          <div className="flex items-center justify-between p-2.5 rounded-xl bg-[#252C35]/60 border border-[#303741] hover:border-[#38BDF8]/30 transition-colors">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#38BDF8]/20 border border-[#38BDF8]/40 text-[#38BDF8] font-semibold text-xs">
                {displayName.charAt(0).toUpperCase()}
              </div>
              <div className="flex flex-col min-w-0">
                <span className="text-xs font-semibold text-[#F3F4F6] truncate">
                  {displayName}
                </span>
                <span className="text-[11px] text-[#9CA3AF] truncate">
                  {userEmail}
                </span>
              </div>
            </div>
            {onLogout && (
              <button
                type="button"
                onClick={onLogout}
                className="p-1.5 rounded-lg text-[#9CA3AF] hover:text-[#FB7185] hover:bg-[#1D2229] focus:outline-none focus:ring-2 focus:ring-[#38BDF8] transition-colors"
                title="Sign out"
                aria-label="Sign out of account"
              >
                <LogOut className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>
      </aside>

      {/* Mobile Navigation Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden fixed inset-0 z-50 flex">
          <div
            className="fixed inset-0 bg-[#111315]/80 backdrop-blur-xs transition-opacity"
            onClick={() => setMobileMenuOpen(false)}
            aria-hidden="true"
          />
          <div className="relative flex flex-col w-64 max-w-xs bg-[#171A1F] border-r border-[#303741] py-4 shadow-2xl z-10">
            <div className="flex items-center justify-between px-5 pb-4 border-b border-[#303741]">
              <div className="flex items-center gap-2.5">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[#38BDF8]/15 border border-[#38BDF8]/30 text-[#38BDF8]">
                  <Shield className="h-4 w-4" />
                </div>
                <span className="font-semibold text-sm text-[#F3F4F6]">AccessGuard AI</span>
              </div>
              <button
                type="button"
                onClick={() => setMobileMenuOpen(false)}
                className="p-1 rounded-lg text-[#9CA3AF] hover:text-[#F3F4F6] hover:bg-[#252C35]"
                aria-label="Close navigation drawer"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <nav className="flex-1 px-3 py-3 space-y-1 overflow-y-auto" aria-label="Mobile Navigation">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname.startsWith(item.href);
                return (
                  <NavLink
                    key={item.href}
                    to={item.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className={cn(
                      "flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg transition-colors",
                      isActive
                        ? "bg-[#38BDF8]/10 text-[#38BDF8] font-semibold border-l-2 border-[#38BDF8]"
                        : "text-[#9CA3AF] hover:bg-[#252C35] hover:text-[#F3F4F6]"
                    )}
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    <span>{item.title}</span>
                  </NavLink>
                );
              })}
            </nav>
            {onLogout && (
              <div className="px-4 pt-3 border-t border-[#303741]">
                <button
                  type="button"
                  onClick={() => {
                    setMobileMenuOpen(false);
                    onLogout();
                  }}
                  className="flex w-full items-center gap-2.5 px-3 py-2 text-sm font-medium text-[#FB7185] rounded-lg hover:bg-rose-500/10"
                >
                  <LogOut className="h-4 w-4" />
                  <span>Sign out</span>
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Main Content Area with Top Header */}
      <div className="flex-1 md:pl-64 flex flex-col min-w-0 bg-[#111315]">
        {/* Desktop Top Navigation Bar */}
        <header className="hidden md:flex h-14 items-center justify-between px-8 bg-[#171A1F]/80 backdrop-blur-md border-b border-[#303741] sticky top-0 z-20">
          <div className="flex items-center gap-2 text-xs text-[#9CA3AF]">
            <span className="hover:text-[#F3F4F6] transition-colors">Platform</span>
            <ChevronRight className="h-3.5 w-3.5 text-[#6B7280]" />
            <span className="text-[#38BDF8] font-medium">{currentNav.title}</span>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-[#1D2229] border border-[#303741] text-[11px] text-[#9CA3AF]">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#34D399] opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[#34D399]" />
              </span>
              <span>axe-core 4.14.0 Engine Active</span>
            </div>
            <div className="h-4 w-[1px] bg-[#303741]" />
            <div className="flex items-center gap-1.5 text-xs text-[#9CA3AF]">
              <Radio className="h-3.5 w-3.5 text-[#38BDF8]" />
              <span>Real-Time SSE</span>
            </div>
            <div className="h-4 w-[1px] bg-[#303741]" />
            <ThemeToggle />
          </div>
        </header>

        {/* Main Workspace */}
        <main id="main-content" className="flex-1 p-6 md:p-8 max-w-7xl mx-auto w-full">
          <Suspense
            fallback={
              <div className="flex min-h-[50vh] w-full items-center justify-center p-8">
                <div className="flex flex-col items-center gap-3">
                  <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#38BDF8] border-t-transparent" />
                  <span className="text-xs text-[#9CA3AF]">Loading module...</span>
                </div>
              </div>
            }
          >
            <Outlet />
          </Suspense>
        </main>
      </div>
    </div>
  );
}
