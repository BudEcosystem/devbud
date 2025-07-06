"use client"

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Plus, FolderGit, Loader2 } from 'lucide-react'
import { apiClient } from '@/lib/api-client'
import { ApiError } from '@/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { RepositoryDialog } from '@/components/repositories/repository-dialog'
import { RepositoryCard } from '@/components/repositories/repository-card'

export default function RepositoriesPage() {
  const [isDialogOpen, setIsDialogOpen] = useState(false)

  const { data: repositories, isLoading, error } = useQuery({
    queryKey: ['repositories'],
    queryFn: () => apiClient.getRepositories(),
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Repositories</h2>
          <p className="text-muted-foreground">
            Manage your git repositories and track development tasks
          </p>
        </div>
        <Button onClick={() => setIsDialogOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Add Repository
        </Button>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center h-32">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      )}

      {error && (
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <p className="text-destructive">
              Failed to load repositories: {(error as unknown as ApiError).detail || 'Unknown error'}
            </p>
          </CardContent>
        </Card>
      )}

      {repositories && repositories.length === 0 && (
        <Card>
          <CardHeader className="text-center py-12">
            <div className="mx-auto w-24 h-24 bg-muted rounded-full flex items-center justify-center mb-6">
              <FolderGit className="h-12 w-12 text-muted-foreground" />
            </div>
            <CardTitle className="text-2xl mb-4">No repositories yet</CardTitle>
            <CardDescription className="text-lg">
              Add your first repository to start managing development tasks
            </CardDescription>
          </CardHeader>
          <CardContent className="text-center pb-12">
            <Button onClick={() => setIsDialogOpen(true)} size="lg">
              <Plus className="mr-2 h-5 w-5" />
              Add Your First Repository
            </Button>
          </CardContent>
        </Card>
      )}

      {repositories && repositories.length > 0 && (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {repositories.map((repo) => (
            <RepositoryCard key={repo.id} repository={repo} />
          ))}
        </div>
      )}

      <RepositoryDialog
        open={isDialogOpen}
        onOpenChange={setIsDialogOpen}
      />
    </div>
  )
}