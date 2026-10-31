import {
  Database,
  Shield,
  User,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { useAuthStore } from "../store/authStore";

export function SettingsPage() {
  const { user } = useAuthStore();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-[#F3F4F6]">Settings</h1>
        <p className="text-sm text-[#9CA3AF] mt-1">
          Account configuration, security boundaries, and system observability parameters.
        </p>
      </div>

      <div className="max-w-4xl space-y-6">
        {/* User Account Details */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <User className="h-4 w-4 text-[#38BDF8]" />
              <CardTitle className="text-base font-semibold">User Profile & Tenant Isolation</CardTitle>
            </div>
            <CardDescription>
              Authenticated identity and scoped data isolation boundaries
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-xs">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-3 rounded-lg bg-[#171C23] border border-[#303741] space-y-1">
                <span className="text-[#9CA3AF]">Display Name</span>
                <div className="font-semibold text-[#F3F4F6]">
                  {user?.display_name || "Engineer"}
                </div>
              </div>
              <div className="p-3 rounded-lg bg-[#171C23] border border-[#303741] space-y-1">
                <span className="text-[#9CA3AF]">Account Email</span>
                <div className="font-mono text-[#F3F4F6]">
                  {user?.email || "user@accessguard.ai"}
                </div>
              </div>
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-[#171C23] border border-[#303741]">
              <span className="text-[#9CA3AF]">Tenant Authorization</span>
              <Badge variant="success" className="text-xs">
                Enforced (owner_id scoped)
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* Crawler Security Policy */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Shield className="h-4 w-4 text-[#34D399]" />
              <CardTitle className="text-base font-semibold">Crawler Security Policy</CardTitle>
            </div>
            <CardDescription>Target domain boundaries and SSRF prevention constraints</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-xs text-[#9CA3AF]">
            <div className="flex items-center justify-between p-3 rounded-lg bg-[#171C23] border border-[#303741]">
              <div>
                <div className="font-semibold text-[#F3F4F6]">Domain Ownership Verification</div>
                <div className="text-[11px] text-[#6B7280]">Required via DNS TXT challenge record</div>
              </div>
              <Badge variant="success">Active Policy</Badge>
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg bg-[#171C23] border border-[#303741]">
              <div>
                <div className="font-semibold text-[#F3F4F6]">SSRF Target IP Filter</div>
                <div className="text-[11px] text-[#6B7280]">RFC 1918, loopback, and cloud IMDS (169.254.169.254) blocked</div>
              </div>
              <Badge variant="success">Strict Blocking</Badge>
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg bg-[#171C23] border border-[#303741]">
              <div>
                <div className="font-semibold text-[#F3F4F6]">Browser Sandbox Isolation</div>
                <div className="text-[11px] text-[#6B7280]">Playwright Chromium in unprivileged container with network abort in snapshot validation</div>
              </div>
              <Badge variant="success">Isolated</Badge>
            </div>
          </CardContent>
        </Card>

        {/* Engine Observability & Secrets */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Database className="h-4 w-4 text-[#38BDF8]" />
              <CardTitle className="text-base font-semibold">Audit Engine Configuration</CardTitle>
            </div>
            <CardDescription>Underlying observability runtimes and local rule bundles</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-xs">
            <div className="flex items-center justify-between p-3 rounded-lg bg-[#171C23] border border-[#303741]">
              <span className="text-[#9CA3AF]">axe-core Bundle</span>
              <span className="font-mono text-[#F3F4F6]">4.14.0 (Offline Node module)</span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-[#171C23] border border-[#303741]">
              <span className="text-[#9CA3AF]">Vector Search Engine</span>
              <span className="font-mono text-[#F3F4F6]">Qdrant (Port 6333, 384d Cosine)</span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-[#171C23] border border-[#303741]">
              <span className="text-[#9CA3AF]">Asynchronous Broker</span>
              <span className="font-mono text-[#F3F4F6]">Redis 7 (Port 6379, Celery)</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
