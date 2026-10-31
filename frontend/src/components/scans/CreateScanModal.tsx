import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { AlertCircle, Link as LinkIcon, Play, ShieldAlert } from "lucide-react";
import { Dialog } from "../ui/Dialog";
import { Button } from "../ui/Button";
import { Project } from "../../api/projects";
import { createScanApi, Scan } from "../../api/scans";

const scanSchema = z.object({
  project_id: z.string().min(1, "Please select a project"),
  target_url: z
    .string()
    .url("Please enter a valid HTTP/HTTPS URL")
    .startsWith("http", "URL must start with http:// or https://"),
  max_pages: z
    .number()
    .int()
    .min(1, "Must crawl at least 1 page")
    .max(100, "Maximum limit is 100 pages"),
  max_depth: z
    .number()
    .int()
    .min(0, "Minimum depth is 0")
    .max(5, "Maximum crawl depth is 5"),
});

type ScanFormData = z.infer<typeof scanSchema>;

export interface CreateScanModalProps {
  isOpen: boolean;
  onClose: () => void;
  projects: Project[];
  preselectedProjectId?: string;
  onScanCreated: (scan: Scan) => void;
}

export function CreateScanModal({
  isOpen,
  onClose,
  projects,
  preselectedProjectId,
  onScanCreated,
}: CreateScanModalProps) {
  const [serverError, setServerError] = useState<string | null>(null);

  const defaultProjectId = preselectedProjectId || projects[0]?.id || "";
  const initialProject = projects.find((p) => p.id === defaultProjectId);
  const initialUrl = initialProject ? `https://${initialProject.base_domain}` : "";

  const [selectedProjectId, setSelectedProjectId] = useState(defaultProjectId);

  const {
    register,
    handleSubmit,
    setValue,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ScanFormData>({
    resolver: zodResolver(scanSchema),
    defaultValues: {
      project_id: defaultProjectId,
      target_url: initialUrl,
      max_pages: 20,
      max_depth: 2,
    },
  });

  const selectedProject = projects.find((p) => p.id === selectedProjectId);
  const isDomainVerified =
    selectedProject?.is_verified ||
    selectedProject?.latest_verification?.status === "verified";

  const handleProjectChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const projId = e.target.value;
    setSelectedProjectId(projId);
    setValue("project_id", projId);
    const p = projects.find((proj) => proj.id === projId);
    if (p) {
      setValue("target_url", `https://${p.base_domain}`);
    }
  };

  const handleClose = () => {
    reset();
    setServerError(null);
    onClose();
  };

  const onSubmit = async (data: ScanFormData) => {
    setServerError(null);
    try {
      const scan = await createScanApi(data.project_id, {
        target_url: data.target_url,
        max_pages: data.max_pages,
        max_depth: data.max_depth,
      });
      reset();
      onScanCreated(scan);
      handleClose();
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
        setServerError(err.response.data.detail);
      } else {
        setServerError("Failed to launch scan. Please verify target domain ownership.");
      }
    }
  };

  return (
    <Dialog
      isOpen={isOpen}
      onClose={handleClose}
      title="Configure Accessibility Scan"
      description="Launch Playwright Chromium with pinned axe-core 4.14.0 across verified web pages."
    >
      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4 pt-2">
        {serverError && (
          <div
            role="alert"
            className="flex items-start gap-2.5 rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-[#FB7185]"
          >
            <AlertCircle className="h-4 w-4 shrink-0 text-[#FB7185] mt-0.5" />
            <span>{serverError}</span>
          </div>
        )}

        {/* Project Selector */}
        <div>
          <label
            htmlFor="scan-project"
            className="block text-xs font-semibold text-[#F3F4F6] uppercase tracking-wider mb-1.5"
          >
            Target Project
          </label>
          <select
            id="scan-project"
            value={selectedProjectId}
            onChange={handleProjectChange}
            className="flex h-10 w-full rounded-lg border border-[#303741] bg-[#171C23] px-3 text-sm text-[#F3F4F6] shadow-xs focus:outline-none focus:ring-2 focus:ring-[#38BDF8] focus:border-transparent transition-colors cursor-pointer"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id} className="bg-[#1D2229] text-[#F3F4F6]">
                {p.name} ({p.base_domain})
              </option>
            ))}
          </select>
        </div>

        {/* Domain Verification Warning Banner */}
        {selectedProject && !isDomainVerified && (
          <div
            role="alert"
            className="flex items-start gap-2.5 rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-[#FBBF24]"
          >
            <ShieldAlert className="h-4 w-4 shrink-0 text-[#FBBF24] mt-0.5" />
            <div>
              <span className="font-semibold">Domain Ownership Unverified:</span>
              <p className="mt-0.5 text-[11px] text-[#9CA3AF]">
                Complete DNS TXT verification before running scans on <code className="text-[#F3F4F6] font-mono">{selectedProject.base_domain}</code>.
              </p>
            </div>
          </div>
        )}

        {/* Target URL */}
        <div>
          <label
            htmlFor="target-url"
            className="block text-xs font-semibold text-[#F3F4F6] uppercase tracking-wider mb-1.5"
          >
            Target URL
          </label>
          <div className="relative">
            <LinkIcon className="absolute left-3 top-2.5 h-4 w-4 text-[#6B7280]" />
            <input
              id="target-url"
              type="url"
              placeholder="https://example.com"
              {...register("target_url")}
              className={`flex h-10 w-full rounded-lg border bg-[#171C23] pl-9 pr-3 text-sm text-[#F3F4F6] placeholder:text-[#6B7280] shadow-xs focus:outline-none focus:ring-2 focus:ring-[#38BDF8] focus:border-transparent transition-colors font-mono ${
                errors.target_url ? "border-[#FB7185]" : "border-[#303741]"
              }`}
              aria-invalid={Boolean(errors.target_url)}
              aria-describedby={errors.target_url ? "target-url-error" : undefined}
            />
          </div>
          {errors.target_url && (
            <p id="target-url-error" className="mt-1 text-xs text-[#FB7185]" role="alert">
              {errors.target_url.message}
            </p>
          )}
        </div>

        {/* Crawl Bounds Grid */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label
              htmlFor="max-pages"
              className="block text-xs font-semibold text-[#F3F4F6] uppercase tracking-wider mb-1.5"
            >
              Max Pages (1–100)
            </label>
            <input
              id="max-pages"
              type="number"
              min={1}
              max={100}
              {...register("max_pages", { valueAsNumber: true })}
              className={`flex h-10 w-full rounded-lg border bg-[#171C23] px-3 text-sm text-[#F3F4F6] shadow-xs focus:outline-none focus:ring-2 focus:ring-[#38BDF8] focus:border-transparent font-mono transition-colors ${
                errors.max_pages ? "border-[#FB7185]" : "border-[#303741]"
              }`}
            />
            {errors.max_pages && (
              <p className="mt-1 text-xs text-[#FB7185]" role="alert">
                {errors.max_pages.message}
              </p>
            )}
          </div>

          <div>
            <label
              htmlFor="max-depth"
              className="block text-xs font-semibold text-[#F3F4F6] uppercase tracking-wider mb-1.5"
            >
              Max Depth (0–5)
            </label>
            <input
              id="max-depth"
              type="number"
              min={0}
              max={5}
              {...register("max_depth", { valueAsNumber: true })}
              className={`flex h-10 w-full rounded-lg border bg-[#171C23] px-3 text-sm text-[#F3F4F6] shadow-xs focus:outline-none focus:ring-2 focus:ring-[#38BDF8] focus:border-transparent font-mono transition-colors ${
                errors.max_depth ? "border-[#FB7185]" : "border-[#303741]"
              }`}
            />
            {errors.max_depth && (
              <p className="mt-1 text-xs text-[#FB7185]" role="alert">
                {errors.max_depth.message}
              </p>
            )}
          </div>
        </div>

        <div className="flex items-center justify-end gap-3 pt-4 border-t border-[#303741]">
          <Button type="button" variant="outline" onClick={handleClose}>
            Cancel
          </Button>
          <Button
            type="submit"
            isLoading={isSubmitting}
            disabled={!isDomainVerified}
            className="gap-2 font-semibold"
          >
            <Play className="h-4 w-4 fill-current" />
            <span>Start Scan</span>
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
