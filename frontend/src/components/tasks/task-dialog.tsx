"use client"

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Loader2 } from 'lucide-react'
import { apiClient } from '@/lib/api-client'
import { CreateTaskDto, Repository, ApiError } from '@/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

interface TaskDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  repositories: Repository[]
}

export function TaskDialog({ open, onOpenChange, repositories }: TaskDialogProps) {
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState<CreateTaskDto>({
    repository_id: '',
    branch_name: '',
    instructions: '',
  })
  const [error, setError] = useState<string | null>(null)

  const createMutation = useMutation({
    mutationFn: (data: CreateTaskDto) => apiClient.createTask(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
      onOpenChange(false)
      // Reset form
      setFormData({
        repository_id: '',
        branch_name: '',
        instructions: '',
      })
      setError(null)
    },
    onError: (error: ApiError) => {
      setError(error.detail || 'Failed to create task')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    createMutation.mutate(formData)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[625px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Create New Task</DialogTitle>
            <DialogDescription>
              Start a new Claude Code generation task on a specific branch
            </DialogDescription>
          </DialogHeader>
          
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="repository">Repository</Label>
              <Select
                value={formData.repository_id}
                onValueChange={(value) => setFormData({ ...formData, repository_id: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a repository" />
                </SelectTrigger>
                <SelectContent>
                  {repositories.map((repo) => (
                    <SelectItem key={repo.id} value={repo.id}>
                      {repo.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="grid gap-2">
              <Label htmlFor="branch">Branch Name</Label>
              <Input
                id="branch"
                value={formData.branch_name}
                onChange={(e) => setFormData({ ...formData, branch_name: e.target.value })}
                placeholder="feature-new-auth"
                required
              />
              <p className="text-sm text-muted-foreground">
                A new branch will be created for this task
              </p>
            </div>
            
            <div className="grid gap-2">
              <Label htmlFor="instructions">Instructions for Claude</Label>
              <Textarea
                id="instructions"
                value={formData.instructions}
                onChange={(e) => setFormData({ ...formData, instructions: e.target.value })}
                placeholder="Create a user authentication system with JWT tokens, login and logout endpoints..."
                rows={6}
                required
              />
              <p className="text-sm text-muted-foreground">
                Provide clear instructions for what you want Claude to implement
              </p>
            </div>
            
            {error && (
              <p className="text-sm text-destructive">{error}</p>
            )}
          </div>
          
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={createMutation.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={createMutation.isPending || !formData.repository_id}>
              {createMutation.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Create Task
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}