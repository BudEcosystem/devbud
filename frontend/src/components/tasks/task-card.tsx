"use client"

import { useState } from 'react'
import Link from 'next/link'
import { formatDistanceToNow } from 'date-fns'
import { GitBranch, Clock, Terminal, AlertCircle, CheckCircle, XCircle, Loader2, Trash2, X } from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Task, TaskStatus } from '@/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { cn } from '@/lib/utils'
import { apiClient } from '@/lib/api-client'

interface TaskCardProps {
  task: Task
}

export function TaskCard({ task }: TaskCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const queryClient = useQueryClient()

  const deleteMutation = useMutation({
    mutationFn: () => apiClient.deleteTask(task.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
      setShowDeleteDialog(false)
    },
  })

  const cancelMutation = useMutation({
    mutationFn: () => apiClient.cancelTask(task.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })

  const statusIcon = {
    [TaskStatus.PENDING]: <Clock className="h-5 w-5 text-gray-500" />,
    [TaskStatus.RUNNING]: <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />,
    [TaskStatus.COMPLETED]: <CheckCircle className="h-5 w-5 text-green-500" />,
    [TaskStatus.FAILED]: <XCircle className="h-5 w-5 text-red-500" />,
    [TaskStatus.CANCELLED]: <AlertCircle className="h-5 w-5 text-yellow-500" />,
  }

  const statusColor = {
    [TaskStatus.PENDING]: 'border-gray-200',
    [TaskStatus.RUNNING]: 'border-blue-200 bg-blue-50/50 dark:bg-blue-950/20',
    [TaskStatus.COMPLETED]: 'border-green-200',
    [TaskStatus.FAILED]: 'border-red-200',
    [TaskStatus.CANCELLED]: 'border-yellow-200',
  }

  return (
    <Card className={cn("transition-all", statusColor[task.status])}>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            {statusIcon[task.status]}
            <div className="space-y-1">
              <CardTitle className="text-lg flex items-center gap-2">
                <GitBranch className="h-4 w-4" />
                {task.branch_name}
              </CardTitle>
              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                <span>{task.repository?.name}</span>
                <span>•</span>
                <span>
                  Created {formatDistanceToNow(new Date(task.created_at), { addSuffix: true })}
                </span>
                {task.completed_at && (
                  <>
                    <span>•</span>
                    <span>
                      Completed {formatDistanceToNow(new Date(task.completed_at), { addSuffix: true })}
                    </span>
                  </>
                )}
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {task.status === TaskStatus.RUNNING && (
              <Link href={`/tasks/${task.id}`}>
                <Button size="sm">
                  <Terminal className="mr-2 h-4 w-4" />
                  View Output
                </Button>
              </Link>
            )}
            {(task.status === TaskStatus.PENDING || task.status === TaskStatus.RUNNING) && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => cancelMutation.mutate()}
                disabled={cancelMutation.isPending}
              >
                {cancelMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <>
                    <X className="mr-2 h-4 w-4" />
                    Cancel
                  </>
                )}
              </Button>
            )}
            {task.status !== TaskStatus.RUNNING && task.status !== TaskStatus.PENDING && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => setShowDeleteDialog(true)}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        <div className="space-y-3">
          <div>
            <h4 className="text-sm font-medium mb-1">Instructions</h4>
            <p className="text-sm text-muted-foreground whitespace-pre-wrap">
              {isExpanded || task.instructions.length <= 200
                ? task.instructions
                : task.instructions.slice(0, 200) + '...'}
            </p>
            {task.instructions.length > 200 && (
              <Button
                variant="link"
                size="sm"
                className="px-0 h-auto"
                onClick={() => setIsExpanded(!isExpanded)}
              >
                {isExpanded ? 'Show less' : 'Show more'}
              </Button>
            )}
          </div>

          {task.output_log && (
            <div>
              <h4 className="text-sm font-medium mb-1">Latest Output</h4>
              <pre className="text-xs bg-muted p-3 rounded-md overflow-x-auto max-h-32 overflow-y-auto">
                {task.output_log.split('\n').slice(-10).join('\n')}
              </pre>
            </div>
          )}
        </div>
      </CardContent>

      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Task</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this task? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2 py-4">
            <p className="text-sm">
              <strong>Branch:</strong> {task.branch_name}
            </p>
            <p className="text-sm">
              <strong>Status:</strong> {task.status}
            </p>
            <p className="text-sm">
              <strong>Created:</strong> {formatDistanceToNow(new Date(task.created_at), { addSuffix: true })}
            </p>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDeleteDialog(false)}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => deleteMutation.mutate()}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Deleting...
                </>
              ) : (
                'Delete'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  )
}