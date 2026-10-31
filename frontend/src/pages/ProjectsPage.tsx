import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  Activity,
  Calendar,
  ExternalLink,
  FolderKanban,
  Globe,
  Plus,
  ShieldAlert,
  ShieldCheck,
  ShieldQuestion,
  Trash2,
} from "lucide-react";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { Card, CardContent } from "../components/ui/Card";
import { Skeleton } from "../components/ui/Skeleton";
import { EmptyState } from "../components/ui/EmptyState";
import {
  deleteProjectApi,
  listProjectsApi,
  Project,
} from "../api/projects";
import { CreateProjectModal } from "../components/projects/CreateProjectModal";
import { DomainVerificationModal } from "../components/projects/DomainVerificationModal";

export function ProjectsPage() {
  const queryClient = useQueryClient();
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [isVerificationOpen, setIsVerificationOpen] = useState(false);

  const {
    data: projectsData,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ["projects"],
    queryFn: listProjectsApi,
  });

  const deleteMutation = useMutation({
    mutationFn: deleteProjectApi,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });

  const handleOpenVerification = (project: Project) => {
    setSelectedProject(project);
    setIsVerificationOpen(true);
  };

  const handleProjectUpdated = (updated: Project) => {
    setSelectedProject(updated);
    queryClient.invalidateQueries({ queryKey: ["projects"] });
  };

  const handleDelete = async (projectId: string, name: string) => {
    if (window.confirm(`Are you sure you want to delete project "${name}"?`)) {
      await deleteMutation.mutateAsync(projectId);
    }
  };

  const projects = projectsData?.items || [];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#F3F4F6]">Projects</h1>
          <p className="text-sm text-[#9CA3AF] mt-1">
            Manage your monitored web applications, target domains, and DNS ownership challenges.
          </p>
        </div>
        <Button onClick={() => setIsCreateOpen(true)} className="gap-2 shrink-0">
          <Plus className="h-4 w-4" />
          <span>New Project</span>
        </Button>
      </div>

      {/* Loading Skeletons */}
      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" aria-busy="true">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="p-6 space-y-4">
              <Skeleton className="h-6 w-3/4" />
              <Skeleton className="h-4 w-1/2" />
              <div className="pt-4 flex justify-between">
                <Skeleton className="h-5 w-20" />
                <Skeleton className="h-8 w-24" />
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Error Banner */}
      {isError && (
        <Card className="border-rose-500/30 bg-rose-500/10 p-6 text-center">
          <div className="flex flex-col items-center gap-2">
            <ShieldAlert className="h-8 w-8 text-[#FB7185]" />
            <p className="text-sm text-[#FB7185] font-semibold">
              Failed to load projects from backend service.
            </p>
            <Button variant="outline" size="sm" onClick={() => refetch()} className="mt-2 text-xs">
              Retry Query
            </Button>
          </div>
        </Card>
      )}

      {/* Empty State */}
      {!isLoading && !isError && projects.length === 0 && (
        <EmptyState
          icon={FolderKanban}
          title="No Monitored Projects Yet"
          description="Register your first website or web application domain to begin automated WCAG audits and safe snapshot remediation."
          action={
            <Button onClick={() => setIsCreateOpen(true)} className="gap-2">
              <Plus className="h-4 w-4" />
              <span>Create First Project</span>
            </Button>
          }
        />
      )}

      {/* Projects Grid */}
      {!isLoading && !isError && projects.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {projects.map((project) => {
            const isVerified =
              project.is_verified ||
              project.latest_verification?.status === "verified";

            return (
              <Card
                key={project.id}
                className="hover:border-[#38BDF8]/40 transition-all flex flex-col justify-between group"
              >
                <CardContent className="p-6 space-y-4">
                  {/* Top row: Name & Badge */}
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <h3 className="font-semibold text-base text-[#F3F4F6] truncate group-hover:text-[#38BDF8] transition-colors">
                        {project.name}
                      </h3>
                      <div className="flex items-center gap-1.5 mt-1 text-xs text-[#9CA3AF] font-mono">
                        <Globe className="h-3.5 w-3.5 text-[#38BDF8] shrink-0" />
                        <span className="truncate">{project.base_domain}</span>
                      </div>
                    </div>
                    {isVerified ? (
                      <Badge variant="success" className="gap-1 shrink-0">
                        <ShieldCheck className="h-3 w-3" />
                        <span>Verified</span>
                      </Badge>
                    ) : (
                      <Badge variant="warning" className="gap-1 shrink-0">
                        <ShieldQuestion className="h-3 w-3" />
                        <span>Pending DNS</span>
                      </Badge>
                    )}
                  </div>

                  {/* Metadata Row */}
                  <div className="pt-2 border-t border-[#303741] space-y-2 text-xs text-[#9CA3AF]">
                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-1.5">
                        <Calendar className="h-3.5 w-3.5 text-[#6B7280]" />
                        <span>Created:</span>
                      </span>
                      <span className="text-[#F3F4F6] font-mono">
                        {new Date(project.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Target Base URL:</span>
                      <a
                        href={`https://${project.base_domain}`}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 text-[#38BDF8] hover:underline font-mono"
                      >
                        <span>https://{project.base_domain}</span>
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    </div>
                  </div>

                  {/* Actions Row */}
                  <div className="pt-4 border-t border-[#303741] flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant={isVerified ? "outline" : "default"}
                        onClick={() => handleOpenVerification(project)}
                        className="text-xs gap-1.5"
                      >
                        {isVerified ? (
                          <>
                            <ShieldCheck className="h-3.5 w-3.5 text-[#34D399]" />
                            <span>DNS Details</span>
                          </>
                        ) : (
                          <>
                            <ShieldAlert className="h-3.5 w-3.5" />
                            <span>Verify Domain</span>
                          </>
                        )}
                      </Button>

                      <Link to="/app/scans">
                        <Button size="sm" variant="outline" className="text-xs gap-1.5">
                          <Activity className="h-3.5 w-3.5 text-[#38BDF8]" />
                          <span>Scans</span>
                        </Button>
                      </Link>
                    </div>

                    <button
                      type="button"
                      onClick={() => handleDelete(project.id, project.name)}
                      className="p-2 rounded-lg text-[#6B7280] hover:text-[#FB7185] hover:bg-rose-500/10 transition-colors"
                      title="Delete project"
                      aria-label={`Delete project ${project.name}`}
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Create Project Modal */}
      <CreateProjectModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onProjectCreated={(newProject) => {
          queryClient.invalidateQueries({ queryKey: ["projects"] });
          handleOpenVerification(newProject);
        }}
      />

      {/* Domain Verification Modal */}
      <DomainVerificationModal
        project={selectedProject}
        isOpen={isVerificationOpen}
        onClose={() => {
          setIsVerificationOpen(false);
          setSelectedProject(null);
        }}
        onProjectUpdated={handleProjectUpdated}
      />
    </div>
  );
}
