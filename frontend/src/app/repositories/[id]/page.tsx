"use client"

import { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, GitBranch, FolderOpen, Plus, Trash2, Edit } from 'lucide-react'
import { apiClient } from '@/lib/api-client'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { TaskDialog } from '@/components/tasks/task-dialog'
import { TaskCard } from '@/components/tasks/task-card'

export default function RepositoryDetailPage() {
  const params = useParams()
  const router = useRouter()
  const queryClient = useQueryClient()
  const repositoryId = params.id as string
  const [isTaskDialogOpen, setIsTaskDialogOpen] = useState(false)

  const { data: repository, isLoading: repoLoading } = useQuery({
    queryKey: ['repository', repositoryId],
    queryFn: () => apiClient.getRepository(repositoryId),
  })

  const { data: tasks, isLoading: tasksLoading } = useQuery({
    queryKey: ['repository-tasks', repositoryId],
    queryFn: () => apiClient.getRepositoryTasks(repositoryId),
  })

  const deleteMutation = useMutation({
    mutationFn: () => apiClient.deleteRepository(repositoryId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['repositories'] })
      router.push('/repositories')
    },
  })

  const handleDelete = () => {
    if (confirm('Are you sure you want to delete this repository?')) {
      deleteMutation.mutate()
    }
  }

  if (repoLoading) {
    return (
      <div className="container py-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    )
  }

  if (!repository) {
    return (
      <div className="container py-8">
        <Card>
          <CardContent className="pt-6">
            <p className="text-center text-muted-foreground">Repository not found</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container py-8">
      <div className="flex items-center gap-4 mb-6">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => router.push('/repositories')}
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <FolderOpen className="h-6 w-6" />
            {repository.name}
          </h1>
          <p className="text-muted-foreground">
            {repository.description || 'No description'}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <Edit className="mr-2 h-4 w-4" />
            Edit
          </Button>
          <Button
            variant="destructive"
            size="sm"
            onClick={handleDelete}
            disabled={deleteMutation.isPending}
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Delete
          </Button>
        </div>
      </div>

      <div className="grid gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Repository Details</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-medium">Path:</span>{' '}
                <code className="text-xs bg-gray-100 px-1 py-0.5 rounded">
                  {repository.path}
                </code>
              </div>
              <div>
                <span className="font-medium">Default Branch:</span>{' '}
                <span className="inline-flex items-center gap-1">
                  <GitBranch className="h-3 w-3" />
                  {repository.default_branch}
                </span>
              </div>
              <div>
                <span className="font-medium">Created:</span>{' '}
                {new Date(repository.created_at).toLocaleString()}
              </div>
              <div>
                <span className="font-medium">Updated:</span>{' '}
                {new Date(repository.updated_at).toLocaleString()}
              </div>
            </div>
          </CardContent>
        </Card>

        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">Tasks</h2>
            <Button onClick={() => setIsTaskDialogOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              New Task
            </Button>
          </div>

          {tasksLoading ? (
            <div className="animate-pulse space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-32 bg-gray-200 rounded"></div>
              ))}
            </div>
          ) : tasks && tasks.length > 0 ? (
            <div className="space-y-4">
              {tasks.map((task) => (
                <TaskCard key={task.id} task={task} />
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="pt-6">
                <p className="text-center text-muted-foreground">
                  No tasks yet. Create your first task to start generating code.
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      <TaskDialog
        open={isTaskDialogOpen}
        onOpenChange={setIsTaskDialogOpen}
        repositories={[repository]}
      />
    </div>
  )
}