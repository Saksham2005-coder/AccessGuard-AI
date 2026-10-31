import { Link } from "react-router-dom";
import { AlertCircle, ArrowLeft } from "lucide-react";
import { Button } from "../components/ui/Button";

export function NotFoundPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#F8FAFC] px-4 py-12">
      <div className="w-full max-w-md text-center">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-slate-100 text-slate-600 mb-5">
          <AlertCircle className="h-7 w-7 text-slate-500" />
        </div>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900">
          Page Not Found
        </h1>
        <p className="mt-2 text-sm text-slate-500">
          Sorry, we couldn&apos;t find the page you were looking for. It may have been moved or does not exist.
        </p>
        <div className="mt-6 flex justify-center">
          <Link to="/app/overview">
            <Button variant="default" className="gap-2">
              <ArrowLeft className="h-4 w-4" />
              Return to Overview
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
