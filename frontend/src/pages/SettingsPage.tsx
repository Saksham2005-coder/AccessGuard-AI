import { useState } from "react";
import axios from "axios";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Database,
  Shield,
  User as UserIcon,
  KeyRound,
  Check,
  AlertCircle,
  Save,
  Lock,
  RefreshCw,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { useAuthStore } from "../store/authStore";
import { updateProfileApi, changePasswordApi } from "../api/auth";

interface ApiErrorData {
  error?: { message?: string };
  detail?: Array<{ msg?: string }>;
}

export function SettingsPage() {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();

  // Profile Edit State
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [displayName, setDisplayName] = useState(user?.display_name || "");
  const [profileSuccessMsg, setProfileSuccessMsg] = useState<string | null>(null);
  const [profileErrorMsg, setProfileErrorMsg] = useState<string | null>(null);

  // Password Change State
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordSuccessMsg, setPasswordSuccessMsg] = useState<string | null>(null);
  const [passwordErrorMsg, setPasswordErrorMsg] = useState<string | null>(null);

  // Profile Mutation
  const profileMutation = useMutation({
    mutationFn: () => updateProfileApi({ display_name: displayName.trim() }),
    onSuccess: (updatedUser) => {
      // Update user state in authStore
      useAuthStore.setState({ user: updatedUser });
      queryClient.invalidateQueries({ queryKey: ["currentUser"] });
      setProfileSuccessMsg("Profile display name updated successfully.");
      setProfileErrorMsg(null);
      setIsEditingProfile(false);
    },
    onError: (err: unknown) => {
      let message = "Failed to update profile.";
      if (axios.isAxiosError<ApiErrorData>(err)) {
        message = err.response?.data?.error?.message || err.message || message;
      } else if (err instanceof Error) {
        message = err.message;
      }
      setProfileErrorMsg(message);
      setProfileSuccessMsg(null);
    },
  });

  // Password Mutation
  const passwordMutation = useMutation({
    mutationFn: () =>
      changePasswordApi({
        current_password: currentPassword,
        new_password: newPassword,
        confirm_password: confirmPassword,
      }),
    onSuccess: (res) => {
      setPasswordSuccessMsg(res.message || "Password successfully changed.");
      setPasswordErrorMsg(null);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    },
    onError: (err: unknown) => {
      let message = "Failed to change password.";
      if (axios.isAxiosError<ApiErrorData>(err)) {
        message =
          err.response?.data?.error?.message ||
          err.response?.data?.detail?.[0]?.msg ||
          err.message ||
          message;
      } else if (err instanceof Error) {
        message = err.message;
      }
      setPasswordErrorMsg(message);
      setPasswordSuccessMsg(null);
    },
  });

  const handleProfileSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setProfileSuccessMsg(null);
    setProfileErrorMsg(null);
    profileMutation.mutate();
  };

  const handlePasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordSuccessMsg(null);
    setPasswordErrorMsg(null);

    if (newPassword.length < 8) {
      setPasswordErrorMsg("New password must be at least 8 characters long.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setPasswordErrorMsg("New password and confirmation password do not match.");
      return;
    }

    passwordMutation.mutate();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-[var(--text-primary)]">Settings</h1>
        <p className="text-sm text-[var(--text-secondary)] mt-1">
          Account configuration, security boundaries, and verified system observability parameters.
        </p>
      </div>

      <div className="max-w-4xl space-y-6">
        {/* User Account & Profile Mutation */}
        <Card className="bg-[var(--bg-card)] border-[var(--border-graphite)]">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <UserIcon className="h-4 w-4 text-[var(--electric-blue)]" />
                <CardTitle className="text-base font-semibold text-[var(--text-primary)]">User Profile & Tenant Isolation</CardTitle>
              </div>
              {!isEditingProfile && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setDisplayName(user?.display_name || "");
                    setIsEditingProfile(true);
                    setProfileSuccessMsg(null);
                    setProfileErrorMsg(null);
                  }}
                >
                  Edit Profile
                </Button>
              )}
            </div>
            <CardDescription className="text-xs text-[var(--text-secondary)]">
              Authenticated identity and scoped tenant boundary configuration
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-xs">
            {profileSuccessMsg && (
              <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center gap-2">
                <Check className="h-4 w-4 shrink-0" />
                <span>{profileSuccessMsg}</span>
              </div>
            )}
            {profileErrorMsg && (
              <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{profileErrorMsg}</span>
              </div>
            )}

            {isEditingProfile ? (
              <form onSubmit={handleProfileSubmit} className="space-y-3">
                <div>
                  <label htmlFor="displayName" className="block text-xs font-medium text-[var(--text-secondary)] mb-1">
                    Display Name
                  </label>
                  <input
                    id="displayName"
                    type="text"
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    maxLength={120}
                    placeholder="Enter your full name or nickname"
                    className="w-full px-3 py-2 rounded-lg bg-[var(--bg-input)] border border-[var(--border-graphite)] text-sm text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--electric-blue)]"
                  />
                </div>

                <div className="flex items-center gap-2 pt-2">
                  <Button type="submit" variant="default" size="sm" disabled={profileMutation.isPending}>
                    {profileMutation.isPending ? <RefreshCw className="h-3.5 w-3.5 animate-spin mr-1" /> : <Save className="h-3.5 w-3.5 mr-1" />}
                    Save Changes
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setIsEditingProfile(false);
                      setProfileErrorMsg(null);
                    }}
                  >
                    Cancel
                  </Button>
                </div>
              </form>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-3 rounded-lg bg-[var(--bg-input)] border border-[var(--border-graphite)] space-y-1">
                  <span className="text-[var(--text-secondary)]">Display Name</span>
                  <div className="font-semibold text-[var(--text-primary)]">
                    {user?.display_name || "Not set"}
                  </div>
                </div>
                <div className="p-3 rounded-lg bg-[var(--bg-input)] border border-[var(--border-graphite)] space-y-1">
                  <span className="text-[var(--text-secondary)]">Account Email</span>
                  <div className="font-mono text-[var(--text-primary)]">
                    {user?.email || "user@accessguard.ai"}
                  </div>
                </div>
              </div>
            )}

            <div className="flex items-center justify-between p-3 rounded-lg bg-[var(--bg-input)] border border-[var(--border-graphite)]">
              <span className="text-[var(--text-secondary)]">Tenant Authorization</span>
              <Badge variant="success" className="text-xs">
                Enforced (owner_id scoped)
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* Change Password Form */}
        <Card className="bg-[var(--bg-card)] border-[var(--border-graphite)]">
          <CardHeader>
            <div className="flex items-center gap-2">
              <KeyRound className="h-4 w-4 text-[var(--electric-blue)]" />
              <CardTitle className="text-base font-semibold text-[var(--text-primary)]">Change Account Password</CardTitle>
            </div>
            <CardDescription className="text-xs text-[var(--text-secondary)]">
              Update password hashed with Argon2id parameters (m=64MB, t=3, p=4) and invalidate other active sessions
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-xs">
            {passwordSuccessMsg && (
              <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center gap-2">
                <Check className="h-4 w-4 shrink-0" />
                <span>{passwordSuccessMsg}</span>
              </div>
            )}
            {passwordErrorMsg && (
              <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{passwordErrorMsg}</span>
              </div>
            )}

            <form onSubmit={handlePasswordSubmit} className="space-y-3 max-w-md">
              <div>
                <label htmlFor="currentPass" className="block text-xs font-medium text-[var(--text-secondary)] mb-1">
                  Current Password
                </label>
                <input
                  id="currentPass"
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  required
                  placeholder="••••••••"
                  className="w-full px-3 py-2 rounded-lg bg-[var(--bg-input)] border border-[var(--border-graphite)] text-sm text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--electric-blue)]"
                />
              </div>

              <div>
                <label htmlFor="newPass" className="block text-xs font-medium text-[var(--text-secondary)] mb-1">
                  New Password (min 8 characters)
                </label>
                <input
                  id="newPass"
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  minLength={8}
                  placeholder="••••••••"
                  className="w-full px-3 py-2 rounded-lg bg-[var(--bg-input)] border border-[var(--border-graphite)] text-sm text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--electric-blue)]"
                />
              </div>

              <div>
                <label htmlFor="confirmPass" className="block text-xs font-medium text-[var(--text-secondary)] mb-1">
                  Confirm New Password
                </label>
                <input
                  id="confirmPass"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  minLength={8}
                  placeholder="••••••••"
                  className="w-full px-3 py-2 rounded-lg bg-[var(--bg-input)] border border-[var(--border-graphite)] text-sm text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--electric-blue)]"
                />
              </div>

              <div className="pt-1">
                <Button type="submit" variant="default" size="sm" disabled={passwordMutation.isPending}>
                  {passwordMutation.isPending ? <RefreshCw className="h-3.5 w-3.5 animate-spin mr-1" /> : <Lock className="h-3.5 w-3.5 mr-1" />}
                  Update Password
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Crawler Security Policy */}
        <Card className="bg-[var(--bg-card)] border-[var(--border-graphite)]">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Shield className="h-4 w-4 text-emerald-400" />
              <CardTitle className="text-base font-semibold text-[var(--text-primary)]">Crawler Security Policy</CardTitle>
            </div>
            <CardDescription className="text-xs text-[var(--text-secondary)]">Target domain boundaries and SSRF prevention constraints</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-xs text-[var(--text-secondary)]">
            <div className="flex items-center justify-between p-3 rounded-lg bg-[var(--bg-input)] border border-[var(--border-graphite)]">
              <div>
                <div className="font-semibold text-[var(--text-primary)]">Domain Ownership Verification</div>
                <div className="text-[11px] text-[var(--text-muted)]">Required via DNS TXT challenge record</div>
              </div>
              <Badge variant="success">Active Policy</Badge>
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg bg-[var(--bg-input)] border border-[var(--border-graphite)]">
              <div>
                <div className="font-semibold text-[var(--text-primary)]">SSRF Target IP Filter</div>
                <div className="text-[11px] text-[var(--text-muted)]">RFC 1918, loopback, and cloud IMDS (169.254.169.254) blocked</div>
              </div>
              <Badge variant="success">Strict Blocking</Badge>
            </div>

            <div className="flex items-center justify-between p-3 rounded-lg bg-[var(--bg-input)] border border-[var(--border-graphite)]">
              <div>
                <div className="font-semibold text-[var(--text-primary)]">Browser Sandbox Isolation</div>
                <div className="text-[11px] text-[var(--text-muted)]">Playwright Chromium in unprivileged container with network abort in snapshot validation</div>
              </div>
              <Badge variant="success">Isolated</Badge>
            </div>
          </CardContent>
        </Card>

        {/* Engine Observability */}
        <Card className="bg-[var(--bg-card)] border-[var(--border-graphite)]">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Database className="h-4 w-4 text-[var(--electric-blue)]" />
              <CardTitle className="text-base font-semibold text-[var(--text-primary)]">Audit Engine Configuration</CardTitle>
            </div>
            <CardDescription className="text-xs text-[var(--text-secondary)]">Runtime services and scanner limits</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div className="p-3 rounded-lg bg-[var(--bg-input)] border border-[var(--border-graphite)]">
              <span className="text-[var(--text-muted)]">Scanner Limits</span>
              <div className="font-medium text-[var(--text-primary)] mt-1">20 pages / Depth 2 (Default)</div>
            </div>
            <div className="p-3 rounded-lg bg-[var(--bg-input)] border border-[var(--border-graphite)]">
              <span className="text-[var(--text-muted)]">Axe-Core Engine Bundle</span>
              <div className="font-mono text-[var(--text-primary)] mt-1">axe-core v4.14.0 (Bundled)</div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
