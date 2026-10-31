import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { AlertCircle, Lock, Mail, Shield } from "lucide-react";
import { useAuthStore } from "../store/authStore";
import { Button } from "../components/ui/Button";
import { Card, CardContent } from "../components/ui/Card";

const loginSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});

type LoginFormData = z.infer<typeof loginSchema>;

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuthStore();
  const [formError, setFormError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const onSubmit = async (data: LoginFormData) => {
    setFormError(null);
    try {
      await login(data);
      const from = (location.state as { from?: { pathname?: string } })?.from?.pathname || "/app/overview";
      navigate(from, { replace: true });
    } catch (err: unknown) {
      if (
        err &&
        typeof err === "object" &&
        "response" in err &&
        err.response &&
        typeof err.response === "object" &&
        "data" in err.response &&
        err.response.data &&
        typeof err.response.data === "object" &&
        "detail" in err.response.data &&
        typeof err.response.data.detail === "string"
      ) {
        setFormError(err.response.data.detail);
      } else {
        setFormError("Invalid email or password. Please try again.");
      }
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#111315] px-4 py-12 text-[#F3F4F6] selection:bg-[#38BDF8]/20 selection:text-[#F3F4F6]">
      <div className="w-full max-w-md">
        {/* Brand Header */}
        <div className="flex flex-col items-center mb-8 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#38BDF8]/15 border border-[#38BDF8]/30 text-[#38BDF8] shadow-lg shadow-[#38BDF8]/10 mb-3.5">
            <Shield className="h-6 w-6" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-[#F3F4F6]">
            Sign in to AccessGuard AI
          </h1>
          <p className="text-sm text-[#9CA3AF] mt-1">
            Enterprise accessibility observability and remediation
          </p>
        </div>

        <Card className="shadow-2xl border-[#303741] bg-[#1D2229]">
          <CardContent className="pt-6">
            {formError && (
              <div
                role="alert"
                className="mb-4 flex items-start gap-2.5 rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-[#FB7185]"
              >
                <AlertCircle className="h-4 w-4 shrink-0 text-[#FB7185] mt-0.5" />
                <span>{formError}</span>
              </div>
            )}

            <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
              <div>
                <label
                  htmlFor="email"
                  className="block text-xs font-semibold text-[#F3F4F6] uppercase tracking-wider mb-1.5"
                >
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-2.5 h-4 w-4 text-[#6B7280]" />
                  <input
                    id="email"
                    type="email"
                    autoComplete="email"
                    placeholder="engineer@company.com"
                    {...register("email")}
                    className={`flex h-10 w-full rounded-lg border bg-[#171C23] pl-9 pr-3 text-sm text-[#F3F4F6] placeholder:text-[#6B7280] shadow-xs focus:outline-none focus:ring-2 focus:ring-[#38BDF8] focus:border-transparent transition-colors ${
                      errors.email ? "border-[#FB7185]" : "border-[#303741]"
                    }`}
                    aria-invalid={Boolean(errors.email)}
                    aria-describedby={errors.email ? "email-error" : undefined}
                  />
                </div>
                {errors.email && (
                  <p id="email-error" className="mt-1 text-xs text-[#FB7185]" role="alert">
                    {errors.email.message}
                  </p>
                )}
              </div>

              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label
                    htmlFor="password"
                    className="block text-xs font-semibold text-[#F3F4F6] uppercase tracking-wider"
                  >
                    Password
                  </label>
                </div>
                <div className="relative">
                  <Lock className="absolute left-3 top-2.5 h-4 w-4 text-[#6B7280]" />
                  <input
                    id="password"
                    type="password"
                    autoComplete="current-password"
                    placeholder="••••••••"
                    {...register("password")}
                    className={`flex h-10 w-full rounded-lg border bg-[#171C23] pl-9 pr-3 text-sm text-[#F3F4F6] placeholder:text-[#6B7280] shadow-xs focus:outline-none focus:ring-2 focus:ring-[#38BDF8] focus:border-transparent transition-colors ${
                      errors.password ? "border-[#FB7185]" : "border-[#303741]"
                    }`}
                    aria-invalid={Boolean(errors.password)}
                    aria-describedby={errors.password ? "password-error" : undefined}
                  />
                </div>
                {errors.password && (
                  <p id="password-error" className="mt-1 text-xs text-[#FB7185]" role="alert">
                    {errors.password.message}
                  </p>
                )}
              </div>

              <Button
                type="submit"
                className="w-full mt-2 font-semibold"
                isLoading={isSubmitting}
              >
                Sign In
              </Button>
            </form>

            <div className="mt-6 text-center text-xs text-[#9CA3AF]">
              Don&apos;t have an account?{" "}
              <Link
                to="/register"
                className="font-semibold text-[#38BDF8] hover:text-[#0EA5E9] transition-colors"
              >
                Create Account
              </Link>
            </div>
          </CardContent>
        </Card>

        {/* Security Footer Notice */}
        <div className="mt-8 text-center text-[11px] text-[#6B7280]">
          Strict Argon2id hashing • Cryptographically signed JWT sessions
        </div>
      </div>
    </div>
  );
}
