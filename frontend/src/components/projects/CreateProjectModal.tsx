import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { AlertCircle, Globe, Layers } from "lucide-react";
import { Dialog } from "../ui/Dialog";
import { Button } from "../ui/Button";
import { createProjectApi, Project } from "../../api/projects";

const projectSchema = z.object({
  name: z.string().min(1, "Project name is required").max(160, "Name is too long"),
  base_domain: z
    .string()
    .min(3, "Domain is required")
    .regex(
      /^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$/,
      "Please enter a valid domain (e.g. 'example.com' or 'app.mysite.org')"
    ),
});

type ProjectFormData = z.infer<typeof projectSchema>;

export interface CreateProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onProjectCreated: (project: Project) => void;
}

export function CreateProjectModal({
  isOpen,
  onClose,
  onProjectCreated,
}: CreateProjectModalProps) {
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ProjectFormData>({
    resolver: zodResolver(projectSchema),
    defaultValues: {
      name: "",
      base_domain: "",
    },
  });

  const handleClose = () => {
    reset();
    setServerError(null);
    onClose();
  };

  const onSubmit = async (data: ProjectFormData) => {
    setServerError(null);
    try {
      const newProject = await createProjectApi(data);
      reset();
      onProjectCreated(newProject);
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
        setServerError("Failed to create project. Please verify the domain and try again.");
      }
    }
  };

  return (
    <Dialog
      isOpen={isOpen}
      onClose={handleClose}
      title="Create New Monitored Project"
      description="Register a web domain to configure automated accessibility scanning and verify ownership."
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

        <div>
          <label
            htmlFor="project-name"
            className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5"
          >
            Project Name
          </label>
          <div className="relative">
            <Layers className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              id="project-name"
              type="text"
              placeholder="e.g. Acme Marketing Website"
              aria-invalid={Boolean(errors.name)}
              aria-describedby={errors.name ? "project-name-error" : undefined}
              {...register("name")}
              className="w-full rounded-lg border border-slate-300 bg-white pl-9 pr-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-[#4657D8] focus:outline-none focus:ring-2 focus:ring-[#4657D8]/20 transition-colors"
            />
          </div>
          {errors.name && (
            <p id="project-name-error" className="mt-1 text-xs text-red-600" role="alert">
              {errors.name.message}
            </p>
          )}
        </div>

        <div>
          <label
            htmlFor="project-domain"
            className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5"
          >
            Target Base Domain
          </label>
          <div className="relative">
            <Globe className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              id="project-domain"
              type="text"
              placeholder="e.g. acme.com"
              aria-invalid={Boolean(errors.base_domain)}
              aria-describedby={errors.base_domain ? "project-domain-error" : undefined}
              {...register("base_domain")}
              className="w-full rounded-lg border border-slate-300 bg-white pl-9 pr-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-[#4657D8] focus:outline-none focus:ring-2 focus:ring-[#4657D8]/20 transition-colors"
            />
          </div>
          <p className="mt-1 text-xs text-slate-500">
            Ownership must be confirmed via DNS TXT record before scans can target subpaths.
          </p>
          {errors.base_domain && (
            <p id="project-domain-error" className="mt-1 text-xs text-red-600" role="alert">
              {errors.base_domain.message}
            </p>
          )}
        </div>

        <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
          <Button
            type="button"
            variant="outline"
            onClick={handleClose}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Creating..." : "Create Project"}
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
