import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Link, useNavigate } from "react-router-dom";
import { AlertCircle, Lock, Mail, Shield, User } from "lucide-react";
import { useAuthStore } from "../store/authStore";
import { Button } from "../components/ui/Button";
import { Card, CardContent } from "../components/ui/Card";

const registerSchema = z
  .object({
    display_name: z.string().min(2, "Full name must be at least 2 characters"),
    email: z.string().email("Please enter a valid email address"),
    password: z.string().min(8, "Password must be at least 8 characters"),
    confirm_password: z.string().min(1, "Please confirm your password"),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

type RegisterFormData = z.infer<typeof registerSchema>;

export function RegisterPage() {
  const navigate = useNavigate();
  const { register: registerUser } = useAuthStore();
  const [formError, setFormError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      display_name: "",
      email: "",
      password: "",
      confirm_password: "",
    },
  });

  const onSubmit = async (data: RegisterFormData) => {
    setFormError(null);
    try {
      await registerUser({
        display_name: data.display_name,
        email: data.email,
        password: data.password,
      });
      navigate("/app/overview", { replace: true });
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
        setFormError("Registration failed. Please check your information and try again.");
      }
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#F8FAFC] px-4 py-12">
      <div className="w-full max-w-md">
        {/* Brand Header */}
        <div className="flex flex-col items-center mb-8 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#4657D8] text-white shadow-md mb-3">
            <Shield className="h-6 w-6" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Create an AccessGuard Account
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Start automating accessibility scans and remediation
          </p>
        </div>

        <Card className="shadow-xs border-slate-200">
          <CardContent className="pt-6">
            {formError && (
              <div
                role="alert"
                className="mb-4 flex items-start gap-2.5 rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-800"
              >
                <AlertCircle className="h-4 w-4 shrink-0 text-red-600 mt-0.5" />
                <span>{formError}</span>
              </div>
            )}

            <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
              <div>
                <label
                  htmlFor="display_name"
                  className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5"
                >
                  Full Name
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                  <input
                    id="display_name"
                    type="text"
                    autoComplete="name"
                    aria-invalid={Boolean(errors.display_name)}
                    aria-describedby={errors.display_name ? "name-error" : undefined}
                    placeholder="Jane Doe"
                    {...register("display_name")}
                    className="w-full rounded-lg border border-slate-300 bg-white pl-9 pr-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-[#4657D8] focus:outline-none focus:ring-2 focus:ring-[#4657D8]/20 transition-colors"
                  />
                </div>
                {errors.display_name && (
                  <p id="name-error" className="mt-1 text-xs text-red-600" role="alert">
                    {errors.display_name.message}
                  </p>
                )}
              </div>

              <div>
                <label
                  htmlFor="email"
                  className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5"
                >
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                  <input
                    id="email"
                    type="email"
                    autoComplete="email"
                    aria-invalid={Boolean(errors.email)}
                    aria-describedby={errors.email ? "email-error" : undefined}
                    placeholder="name@company.com"
                    {...register("email")}
                    className="w-full rounded-lg border border-slate-300 bg-white pl-9 pr-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-[#4657D8] focus:outline-none focus:ring-2 focus:ring-[#4657D8]/20 transition-colors"
                  />
                </div>
                {errors.email && (
                  <p id="email-error" className="mt-1 text-xs text-red-600" role="alert">
                    {errors.email.message}
                  </p>
                )}
              </div>

              <div>
                <label
                  htmlFor="password"
                  className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5"
                >
                  Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                  <input
                    id="password"
                    type="password"
                    autoComplete="new-password"
                    aria-invalid={Boolean(errors.password)}
                    aria-describedby={errors.password ? "password-error" : undefined}
                    placeholder="At least 8 characters"
                    {...register("password")}
                    className="w-full rounded-lg border border-slate-300 bg-white pl-9 pr-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-[#4657D8] focus:outline-none focus:ring-2 focus:ring-[#4657D8]/20 transition-colors"
                  />
                </div>
                {errors.password && (
                  <p id="password-error" className="mt-1 text-xs text-red-600" role="alert">
                    {errors.password.message}
                  </p>
                )}
              </div>

              <div>
                <label
                  htmlFor="confirm_password"
                  className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5"
                >
                  Confirm Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                  <input
                    id="confirm_password"
                    type="password"
                    autoComplete="new-password"
                    aria-invalid={Boolean(errors.confirm_password)}
                    aria-describedby={errors.confirm_password ? "confirm-password-error" : undefined}
                    placeholder="Repeat password"
                    {...register("confirm_password")}
                    className="w-full rounded-lg border border-slate-300 bg-white pl-9 pr-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-[#4657D8] focus:outline-none focus:ring-2 focus:ring-[#4657D8]/20 transition-colors"
                  />
                </div>
                {errors.confirm_password && (
                  <p id="confirm-password-error" className="mt-1 text-xs text-red-600" role="alert">
                    {errors.confirm_password.message}
                  </p>
                )}
              </div>

              <Button
                type="submit"
                disabled={isSubmitting}
                className="w-full mt-2"
              >
                {isSubmitting ? "Creating account..." : "Create account"}
              </Button>
            </form>

            <div className="mt-6 pt-5 border-t border-slate-100 text-center text-xs text-slate-500">
              Already have an account?{" "}
              <Link
                to="/login"
                className="font-medium text-[#4657D8] hover:underline"
              >
                Sign in
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
