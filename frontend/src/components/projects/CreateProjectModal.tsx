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
            className="flex items-start gap-2.5 rounded-lg border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-[#FB7185]"
          >
            <AlertCircle className="h-4 w-4 shrink-0 text-[#FB7185] mt-0.5" />
            <span>{serverError}</span>
          </div>
        )}

        <div>
          <label
            htmlFor="project-name"
            className="block text-xs font-semibold text-[#F3F4F6] uppercase tracking-wider mb-1.5"
          >
            Project Name
          </label>
          <div className="relative">
            <Layers className="absolute left-3 top-2.5 h-4 w-4 text-[#6B7280]" />
            <input
              id="project-name"
              type="text"
              placeholder="e.g. Acme Marketing Site"
              {...register("name")}
              className={`flex h-10 w-full rounded-lg border bg-[#171C23] pl-9 pr-3 text-sm text-[#F3F4F6] placeholder:text-[#6B7280] shadow-xs focus:outline-none focus:ring-2 focus:ring-[#38BDF8] focus:border-transparent transition-colors ${
                errors.name ? "border-[#FB7185]" : "border-[#303741]"
              }`}
              aria-invalid={Boolean(errors.name)}
              aria-describedby={errors.name ? "project-name-error" : undefined}
            />
          </div>
          {errors.name && (
            <p id="project-name-error" className="mt-1 text-xs text-[#FB7185]" role="alert">
              {errors.name.message}
            </p>
          )}
        </div>

        <div>
          <label
            htmlFor="project-domain"
            className="block text-xs font-semibold text-[#F3F4F6] uppercase tracking-wider mb-1.5"
          >
            Target Base Domain
          </label>
          <div className="relative">
            <Globe className="absolute left-3 top-2.5 h-4 w-4 text-[#6B7280]" />
            <input
              id="project-domain"
              type="text"
              placeholder="e.g. acme.com or app.mysite.org"
              {...register("base_domain")}
              className={`flex h-10 w-full rounded-lg border bg-[#171C23] pl-9 pr-3 text-sm text-[#F3F4F6] placeholder:text-[#6B7280] shadow-xs focus:outline-none focus:ring-2 focus:ring-[#38BDF8] focus:border-transparent transition-colors font-mono ${
                errors.base_domain ? "border-[#FB7185]" : "border-[#303741]"
              }`}
              aria-invalid={Boolean(errors.base_domain)}
              aria-describedby={errors.base_domain ? "project-domain-error" : "domain-help"}
            />
          </div>
          <p id="domain-help" className="mt-1 text-[11px] text-[#9CA3AF]">
            Specify the fully qualified domain name. You will be provided a DNS TXT challenge to verify ownership.
          </p>
          {errors.base_domain && (
            <p id="project-domain-error" className="mt-1 text-xs text-[#FB7185]" role="alert">
              {errors.base_domain.message}
            </p>
          )}
        </div>

        <div className="flex items-center justify-end gap-3 pt-4 border-t border-[#303741]">
          <Button type="button" variant="outline" onClick={handleClose}>
            Cancel
          </Button>
          <Button type="submit" isLoading={isSubmitting}>
            Create Project
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
