import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  FolderKanban,
  Globe,
  Plus,
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
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Projects</h1>
          <p className="text-sm text-slate-500 mt-1">
            Manage your monitored web applications, target domains, and DNS ownership challenges.
          </p>
        </div>
        <Button onClick={() => setIsCreateOpen(true)} className="gap-2 shrink-0">
          <Plus className="h-4 w-4" />
          <span>New Project</span>
        </Button>
      </div>

      {/* Loading Skeleton */}
      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" aria-busy="true">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="p-5 space-y-3">
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
        <Card className="border-red-200 bg-red-50 p-6 text-center">
          <p className="text-sm text-red-800 font-medium mb-3">
            Failed to load projects. Please try refreshing.
          </p>
          <Button variant="outline" onClick={() => refetch()} className="mx-auto text-xs">
            Retry Loading
          </Button>
        </Card>
      )}

      {/* Empty State */}
      {!isLoading && !isError && projects.length === 0 && (
        <EmptyState
          icon={FolderKanban}
          title="No projects configured"
          description="Create your first project to verify domain ownership and unlock automated accessibility crawler audits."
          action={
            <Button onClick={() => setIsCreateOpen(true)} className="gap-2">
              <Plus className="h-4 w-4" />
              <span>Create Project</span>
            </Button>
          }
        />
      )}

      {/* Projects Grid */}
      {!isLoading && !isError && projects.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {projects.map((project) => {
            const isVerified = project.is_verified || project.latest_verification?.status === "verified";
            return (
              <Card
                key={project.id}
                className="flex flex-col justify-between hover:shadow-md transition-shadow border-slate-200"
              >
                <CardContent className="pt-5 space-y-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-1">
                      <h2 className="text-base font-semibold text-slate-900 line-clamp-1">
                        {project.name}
                      </h2>
                      <div className="flex items-center gap-1.5 text-xs text-slate-500 font-mono">
                        <Globe className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                        <span>{project.base_domain}</span>
                      </div>
                    </div>
                    <Badge variant={isVerified ? "success" : "warning"} className="shrink-0">
                      {isVerified ? "Verified" : "Pending DNS"}
                    </Badge>
                  </div>

                  <div className="text-xs text-slate-500 pt-1">
                    {isVerified ? (
                      <div className="flex items-center gap-1.5 text-emerald-700">
                        <ShieldCheck className="h-4 w-4" />
                        <span>Authorized for multi-page crawling</span>
                      </div>
                    ) : (
                      <div className="flex items-center gap-1.5 text-amber-700">
                        <ShieldQuestion className="h-4 w-4" />
                        <span>DNS TXT verification required</span>
                      </div>
                    )}
                  </div>
                </CardContent>

                <div className="flex items-center justify-between px-5 py-3.5 border-t border-slate-100 bg-slate-50/50 rounded-b-lg">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleOpenVerification(project)}
                    className="text-xs"
                  >
                    DNS Verification
                  </Button>

                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(project.id, project.name)}
                    className="text-xs text-red-600 hover:text-red-700 hover:bg-red-50 p-1.5"
                    aria-label={`Delete project ${project.name}`}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Creation Modal */}
      <CreateProjectModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onProjectCreated={(newProject) => {
          queryClient.invalidateQueries({ queryKey: ["projects"] });
          handleOpenVerification(newProject);
        }}
      />

      {/* Verification Details Modal */}
      <DomainVerificationModal
        project={selectedProject}
        isOpen={isVerificationOpen}
        onClose={() => setIsVerificationOpen(false)}
        onProjectUpdated={handleProjectUpdated}
      />
    </div>
  );
}
