"use client"

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Loader2 } from 'lucide-react'
import { apiClient } from '@/lib/api-client'
import { CreateRepositoryDto, ApiError } from '@/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

interface RepositoryDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function RepositoryDialog({ open, onOpenChange }: RepositoryDialogProps) {
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState<CreateRepositoryDto>({
    name: '',
    path: '',
    default_branch: 'main',
    description: '',
  })
  const [error, setError] = useState<string | null>(null)

  const createMutation = useMutation({
    mutationFn: (data: CreateRepositoryDto) => apiClient.createRepository(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['repositories'] })
      onOpenChange(false)
      // Reset form
      setFormData({
        name: '',
        path: '',
        default_branch: 'main',
        description: '',
      })
      setError(null)
    },
    onError: (error: ApiError) => {
      setError(error.detail || 'Failed to create repository')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    createMutation.mutate(formData)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[525px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Add Repository</DialogTitle>
            <DialogDescription>
              Add a git repository to manage development tasks
            </DialogDescription>
          </DialogHeader>
          
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name">Repository Name</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="my-awesome-project"
                required
              />
            </div>
            
            <div className="grid gap-2">
              <Label htmlFor="path">Repository Path</Label>
              <Input
                id="path"
                value={formData.path}
                onChange={(e) => setFormData({ ...formData, path: e.target.value })}
                placeholder="/home/username/my-project"
                required
              />
              <p className="text-sm text-muted-foreground">
                Absolute path to the git repository on the server
              </p>
            </div>
            
            <div className="grid gap-2">
              <Label htmlFor="branch">Default Branch</Label>
              <Input
                id="branch"
                value={formData.default_branch}
                onChange={(e) => setFormData({ ...formData, default_branch: e.target.value })}
                placeholder="main"
                required
              />
            </div>
            
            <div className="grid gap-2">
              <Label htmlFor="description">Description (optional)</Label>
              <Input
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Brief description of the repository"
              />
            </div>
            
            {error && (
              <p className="text-sm text-destructive bg-destructive/10 p-2 rounded">{error}</p>
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
            <Button 
              type="submit" 
              disabled={createMutation.isPending}
            >
              {createMutation.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Add Repository
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}