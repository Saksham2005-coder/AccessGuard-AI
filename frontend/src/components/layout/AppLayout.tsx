import { useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import {
  Activity,
  BookOpen,
  FileText,
  FolderKanban,
  LayoutDashboard,
  LogOut,
  Menu,
  Settings,
  Shield,
  ShieldAlert,
  Sparkles,
  X,
} from "lucide-react";
import { cn } from "../../lib/utils";
import { useAuthStore } from "../../store/authStore";

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

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-[#172033] flex flex-col md:flex-row antialiased">
      {/* Skip to Content for Keyboard Accessibility */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:px-4 focus:py-2 focus:bg-[#4657D8] focus:text-white focus:rounded-md focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-white"
      >
        Skip to main content
      </a>

      {/* Mobile Top Header */}
      <header className="md:hidden flex items-center justify-between px-4 py-3 bg-white border-b border-slate-200 sticky top-0 z-40">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#4657D8] text-white">
            <Shield className="h-5 w-5" />
          </div>
          <span className="font-semibold text-base tracking-tight text-slate-900">
            AccessGuard AI
          </span>
        </div>
        <button
          type="button"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-1.5 rounded-md text-slate-600 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-[#4657D8]"
          aria-label={mobileMenuOpen ? "Close navigation menu" : "Open navigation menu"}
          aria-expanded={mobileMenuOpen}
        >
          {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </header>

      {/* Desktop Fixed Left Sidebar */}
      <aside className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0 z-30 bg-white border-r border-slate-200">
        {/* Brand Header */}
        <div className="flex h-16 items-center px-6 border-b border-slate-100 gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#4657D8] text-white shadow-xs">
            <Shield className="h-5 w-5" />
          </div>
          <div className="flex flex-col">
            <span className="font-semibold text-sm tracking-tight text-slate-900 leading-tight">
              AccessGuard AI
            </span>
            <span className="text-[11px] text-slate-400 font-medium">
              Accessibility Platform
            </span>
          </div>
        </div>

        {/* Navigation List */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto" aria-label="Main Navigation">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname.startsWith(item.href);
            return (
              <NavLink
                key={item.href}
                to={item.href}
                className={({ isActive: linkActive }) =>
                  cn(
                    "flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg transition-colors group",
                    linkActive || isActive
                      ? "bg-[#4657D8]/10 text-[#4657D8]"
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                  )
                }
              >
                <Icon
                  className={cn(
                    "h-4 w-4 shrink-0 transition-colors",
                    isActive ? "text-[#4657D8]" : "text-slate-400 group-hover:text-slate-600"
                  )}
                />
                <span>{item.title}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* User Profile / Logout Area */}
        <div className="p-3 border-t border-slate-100 relative">
          <div className="flex items-center justify-between p-2 rounded-lg bg-slate-50 hover:bg-slate-100 transition-colors">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#4657D8]/15 text-[#4657D8] font-semibold text-xs">
                {displayName.charAt(0).toUpperCase()}
              </div>
              <div className="flex flex-col min-w-0">
                <span className="text-xs font-semibold text-slate-900 truncate">
                  {displayName}
                </span>
                <span className="text-[11px] text-slate-400 truncate">
                  {userEmail}
                </span>
              </div>
            </div>
            {onLogout && (
              <button
                type="button"
                onClick={onLogout}
                className="p-1.5 rounded-md text-slate-400 hover:text-slate-700 hover:bg-white focus:outline-none focus:ring-2 focus:ring-[#4657D8] transition-colors"
                title="Sign out"
                aria-label="Sign out of account"
              >
                <LogOut className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>
      </aside>

      {/* Mobile Slide-over Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden fixed inset-0 z-50 flex">
          <div
            className="fixed inset-0 bg-slate-900/30 backdrop-blur-xs transition-opacity"
            onClick={() => setMobileMenuOpen(false)}
            aria-hidden="true"
          />
          <div className="relative flex flex-col w-64 max-w-xs bg-white py-4 shadow-xl z-10">
            <div className="flex items-center justify-between px-5 pb-4 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Shield className="h-6 w-6 text-[#4657D8]" />
                <span className="font-semibold text-sm text-slate-900">AccessGuard AI</span>
              </div>
              <button
                type="button"
                onClick={() => setMobileMenuOpen(false)}
                className="p-1 rounded-md text-slate-400 hover:bg-slate-100"
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
                        ? "bg-[#4657D8]/10 text-[#4657D8]"
                        : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                    )}
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    <span>{item.title}</span>
                  </NavLink>
                );
              })}
            </nav>
            {onLogout && (
              <div className="px-4 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => {
                    setMobileMenuOpen(false);
                    onLogout();
                  }}
                  className="flex w-full items-center gap-2.5 px-3 py-2 text-sm font-medium text-red-600 rounded-lg hover:bg-red-50"
                >
                  <LogOut className="h-4 w-4" />
                  <span>Sign out</span>
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 md:pl-64 flex flex-col min-w-0">
        <main id="main-content" className="flex-1 p-6 md:p-8 max-w-7xl mx-auto w-full">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
