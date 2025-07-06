"use client"

import Link from 'next/link'
import { formatDistanceToNow } from 'date-fns'
import { GitBranch, FolderOpen, Activity, MoreVertical } from 'lucide-react'
import { Repository } from '@/types'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

interface RepositoryCardProps {
  repository: Repository
}

export function RepositoryCard({ repository }: RepositoryCardProps) {
  return (
    <Card className="overflow-hidden hover:shadow-lg transition-all duration-300 bg-card/50 backdrop-blur supports-[backdrop-filter]:bg-card/50">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <CardTitle className="flex items-center gap-2">
              <FolderOpen className="h-5 w-5" />
              <Link 
                href={`/repositories/${repository.id}`}
                className="text-lg font-semibold hover:text-primary transition-colors"
              >
                {repository.name}
              </Link>
            </CardTitle>
            <CardDescription className="text-sm">
              {repository.description || 'AI infrastructure and orchestration platform'}
            </CardDescription>
          </div>
          <Button 
            variant="ghost" 
            size="icon"
            className="h-8 w-8 hover:bg-accent"
          >
            <MoreVertical className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4 pb-4">
        {/* Branch info */}
        <div className="flex items-center gap-2 text-sm">
          <GitBranch className="h-4 w-4 text-muted-foreground" />
          <span>{repository.default_branch}</span>
        </div>
        
        {/* Path info */}
        <div className="flex items-center gap-2 text-sm">
          <FolderOpen className="h-4 w-4 text-muted-foreground" />
          <span className="truncate font-mono text-xs text-muted-foreground" title={repository.path}>
            {repository.path}
          </span>
        </div>

        {/* Stats */}
        <div className="flex items-center justify-between pt-3 border-t">
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4" />
            <span className="text-sm">
              {repository.active_task_count || 0} active
            </span>
          </div>
          
          <span className="text-xs text-muted-foreground">
            {formatDistanceToNow(new Date(repository.updated_at), { addSuffix: true })}
          </span>
        </div>
      </CardContent>
    </Card>
  )
}