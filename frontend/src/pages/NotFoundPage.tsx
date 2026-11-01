import { Link } from "react-router-dom";
import { AlertCircle, ArrowLeft } from "lucide-react";
import { Button } from "../components/ui/Button";

export function NotFoundPage() {
  return (
    <main className="min-h-screen flex items-center justify-center bg-[#111315] px-4 py-12 text-[#F3F4F6]">
      <div className="w-full max-w-md text-center">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-[#252C35] border border-[#303741] text-[#38BDF8] mb-5 shadow-lg shadow-[#38BDF8]/5">
          <AlertCircle className="h-7 w-7 text-[#38BDF8]" />
        </div>
        <h1 className="text-3xl font-bold tracking-tight text-[#F3F4F6]">
          Page Not Found
        </h1>
        <p className="mt-2 text-sm text-[#9CA3AF]">
          Sorry, we couldn&apos;t find the page you were looking for. It may have been moved or does not exist.
        </p>
        <div className="mt-6 flex justify-center">
          <Link to="/app/overview">
            <Button variant="default" className="gap-2 font-semibold">
              <ArrowLeft className="h-4 w-4" />
              <span>Return to Overview</span>
            </Button>
          </Link>
        </div>
      </div>
    </main>
  );
}
