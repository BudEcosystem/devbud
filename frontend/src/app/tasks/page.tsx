"use client"

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Plus, Loader2, ListTodo } from 'lucide-react'
import Link from 'next/link'
import { apiClient } from '@/lib/api-client'
import { ApiError } from '@/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { TaskDialog } from '@/components/tasks/task-dialog'
import { TaskCard } from '@/components/tasks/task-card'
import { TaskStatus } from '@/types'

export default function TasksPage() {
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [statusFilter, setStatusFilter] = useState<TaskStatus | 'all'>('all')

  const { data: tasks, isLoading, error } = useQuery({
    queryKey: ['tasks', statusFilter],
    queryFn: () => {
      if (statusFilter === 'all') {
        return apiClient.getTasks()
      }
      return apiClient.getTasks(undefined, statusFilter)
    },
  })

  const { data: repositories } = useQuery({
    queryKey: ['repositories'],
    queryFn: () => apiClient.getRepositories(),
  })

  const filteredTasks = tasks || []

  return (
    <div className="container py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Tasks</h1>
          <p className="text-muted-foreground">
            Monitor and manage your Claude Code generation tasks
          </p>
        </div>
        <Button 
          onClick={() => setIsDialogOpen(true)}
          disabled={!repositories || repositories.length === 0}
        >
          <Plus className="mr-2 h-4 w-4" />
          New Task
        </Button>
      </div>

      {/* Status Filter */}
      <div className="flex items-center gap-2 mb-6">
        <span className="text-sm font-medium">Filter by status:</span>
        <div className="flex gap-2">
          <StatusFilterButton
            status="all"
            currentStatus={statusFilter}
            onClick={() => setStatusFilter('all')}
            count={tasks?.length || 0}
          />
          {Object.values(TaskStatus).map((status) => (
            <StatusFilterButton
              key={status}
              status={status}
              currentStatus={statusFilter}
              onClick={() => setStatusFilter(status)}
              count={tasks?.filter(t => t.status === status).length || 0}
            />
          ))}
        </div>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      )}

      {error && (
        <Card>
          <CardContent className="pt-6">
            <p className="text-destructive">
              Failed to load tasks: {(error as unknown as ApiError).detail || 'Unknown error'}
            </p>
          </CardContent>
        </Card>
      )}

      {!repositories || repositories.length === 0 ? (
        <Card>
          <CardHeader className="text-center">
            <ListTodo className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <CardTitle>No repositories found</CardTitle>
            <CardDescription>
              You need to add a repository before creating tasks
            </CardDescription>
          </CardHeader>
          <CardContent className="text-center">
            <Button asChild>
              <Link href="/repositories">Go to Repositories</Link>
            </Button>
          </CardContent>
        </Card>
      ) : filteredTasks.length === 0 ? (
        <Card>
          <CardHeader className="text-center">
            <ListTodo className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <CardTitle>No tasks found</CardTitle>
            <CardDescription>
              {statusFilter === 'all' 
                ? 'Create your first task to start generating code with Claude'
                : `No ${statusFilter} tasks found`}
            </CardDescription>
          </CardHeader>
          {statusFilter === 'all' && (
            <CardContent className="text-center">
              <Button onClick={() => setIsDialogOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Create Task
              </Button>
            </CardContent>
          )}
        </Card>
      ) : (
        <div className="grid gap-6">
          {filteredTasks.map((task) => (
            <TaskCard key={task.id} task={task} />
          ))}
        </div>
      )}

      <TaskDialog
        open={isDialogOpen}
        onOpenChange={setIsDialogOpen}
        repositories={repositories || []}
      />
    </div>
  )
}

function StatusFilterButton({
  status,
  currentStatus,
  onClick,
  count,
}: {
  status: TaskStatus | 'all'
  currentStatus: TaskStatus | 'all'
  onClick: () => void
  count: number
}) {
  const isActive = status === currentStatus
  
  return (
    <Button
      variant={isActive ? 'default' : 'outline'}
      size="sm"
      onClick={onClick}
      className="capitalize"
    >
      {status} ({count})
    </Button>
  )
}