import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { AlertCircle, Globe, Link as LinkIcon, Play, ShieldAlert } from "lucide-react";
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
        setServerError("Failed to initiate scan. Ensure the target domain is verified.");
      }
    }
  };

  return (
    <Dialog
      isOpen={isOpen}
      onClose={handleClose}
      title="Initiate Accessibility Scan"
      description="Launch an automated multi-page Playwright crawler with pinned axe-core 4.14.0 evaluation."
      className="max-w-lg"
    >
      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4 pt-2">
        {serverError && (
          <div
            role="alert"
            className="flex items-start gap-2.5 rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-800"
          >
            <AlertCircle className="h-4 w-4 shrink-0 text-red-600 mt-0.5" />
            <span>{serverError}</span>
          </div>
        )}

        {/* Project Selector */}
        <div>
          <label
            htmlFor="scan-project"
            className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5"
          >
            Monitored Project
          </label>
          <div className="relative">
            <Globe className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <select
              id="scan-project"
              {...register("project_id")}
              onChange={handleProjectChange}
              className="w-full rounded-lg border border-slate-300 bg-white pl-9 pr-8 py-2 text-sm text-slate-900 focus:border-[#4657D8] focus:outline-none focus:ring-2 focus:ring-[#4657D8]/20 transition-colors"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.base_domain})
                </option>
              ))}
            </select>
          </div>
          {errors.project_id && (
            <p className="mt-1 text-xs text-red-600">{errors.project_id.message}</p>
          )}

          {selectedProject && !isDomainVerified && (
            <div className="mt-2 flex items-center gap-2 p-2.5 rounded-md border border-amber-200 bg-amber-50 text-xs text-amber-800">
              <ShieldAlert className="h-4 w-4 shrink-0 text-amber-600" />
              <span>
                Domain <strong>{selectedProject.base_domain}</strong> is not verified. Complete DNS TXT verification before running scans.
              </span>
            </div>
          )}
        </div>

        {/* Target URL */}
        <div>
          <label
            htmlFor="target-url"
            className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5"
          >
            Target Entrypoint URL
          </label>
          <div className="relative">
            <LinkIcon className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              id="target-url"
              type="url"
              placeholder="https://example.com"
              aria-invalid={Boolean(errors.target_url)}
              aria-describedby={errors.target_url ? "target-url-error" : undefined}
              {...register("target_url")}
              className="w-full rounded-lg border border-slate-300 bg-white pl-9 pr-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-[#4657D8] focus:outline-none focus:ring-2 focus:ring-[#4657D8]/20 transition-colors"
            />
          </div>
          {errors.target_url && (
            <p id="target-url-error" className="mt-1 text-xs text-red-600">
              {errors.target_url.message}
            </p>
          )}
        </div>

        {/* Crawl Parameters Grid */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label
              htmlFor="max-pages"
              className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5"
            >
              Max Pages
            </label>
            <input
              id="max-pages"
              type="number"
              min={1}
              max={100}
              {...register("max_pages", { valueAsNumber: true })}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[#4657D8] focus:outline-none focus:ring-2 focus:ring-[#4657D8]/20 transition-colors"
            />
            {errors.max_pages && (
              <p className="mt-1 text-xs text-red-600">{errors.max_pages.message}</p>
            )}
          </div>

          <div>
            <label
              htmlFor="max-depth"
              className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5"
            >
              Max Depth
            </label>
            <input
              id="max-depth"
              type="number"
              min={0}
              max={5}
              {...register("max_depth", { valueAsNumber: true })}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-[#4657D8] focus:outline-none focus:ring-2 focus:ring-[#4657D8]/20 transition-colors"
            />
            {errors.max_depth && (
              <p className="mt-1 text-xs text-red-600">{errors.max_depth.message}</p>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
          <Button
            type="button"
            variant="outline"
            onClick={handleClose}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            disabled={isSubmitting || !isDomainVerified}
            className="gap-2"
          >
            <Play className="h-4 w-4" />
            <span>{isSubmitting ? "Launching..." : "Start Scan"}</span>
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
