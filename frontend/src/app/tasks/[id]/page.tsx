"use client"

import { useEffect, useState, useRef } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Terminal, Download, Square } from 'lucide-react'
import { apiClient } from '@/lib/api-client'
import { wsClient } from '@/lib/websocket-client'
import { WebSocketMessage, TaskStatus } from '@/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function TaskDetailPage() {
  const params = useParams()
  const router = useRouter()
  const taskId = params.id as string
  const [output, setOutput] = useState<string[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const outputRef = useRef<HTMLPreElement>(null)
  const shouldAutoScroll = useRef(true)

  const { data: task, isLoading } = useQuery({
    queryKey: ['task', taskId],
    queryFn: () => apiClient.getTask(taskId),
  })

  // WebSocket connection
  useEffect(() => {
    if (!task || task.status !== TaskStatus.RUNNING) return

    // Connect to task WebSocket
    wsClient.connectToTask(taskId)

    // Handle WebSocket events
    const unsubscribeMessage = wsClient.on('message', (message: WebSocketMessage) => {
      if (message.type === 'output' && message.output) {
        setOutput(prev => [...prev, message.output!])
      }
    })

    const unsubscribeConnected = wsClient.on('connected', () => {
      setIsConnected(true)
    })

    const unsubscribeDisconnected = wsClient.on('disconnected', () => {
      setIsConnected(false)
    })

    // Load initial output
    apiClient.getTaskOutput(taskId).then(result => {
      if (result.output) {
        setOutput(result.output.split('\n'))
      }
    })

    return () => {
      unsubscribeMessage()
      unsubscribeConnected()
      unsubscribeDisconnected()
      wsClient.disconnect()
    }
  }, [taskId, task?.status, task])

  // Auto-scroll to bottom when new output arrives
  useEffect(() => {
    if (shouldAutoScroll.current && outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight
    }
  }, [output])

  const handleScroll = () => {
    if (outputRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = outputRef.current
      // Check if user is near the bottom (within 50px)
      shouldAutoScroll.current = scrollHeight - scrollTop - clientHeight < 50
    }
  }

  const handleCancelTask = async () => {
    try {
      await apiClient.cancelTask(taskId)
      router.push('/tasks')
    } catch (error) {
      console.error('Failed to cancel task:', error)
    }
  }

  const downloadOutput = () => {
    const blob = new Blob([output.join('\n')], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `task-${taskId}-output.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  if (isLoading) {
    return (
      <div className="container py-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    )
  }

  if (!task) {
    return (
      <div className="container py-8">
        <Card>
          <CardContent className="pt-6">
            <p className="text-center text-muted-foreground">Task not found</p>
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
          onClick={() => router.push('/tasks')}
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold">{task.branch_name}</h1>
          <p className="text-muted-foreground">
            {task.repository?.name} • {task.status}
            {isConnected && task.status === TaskStatus.RUNNING && (
              <span className="ml-2 text-green-600">● Connected</span>
            )}
          </p>
        </div>
        <div className="flex gap-2">
          {task.status === TaskStatus.RUNNING && (
            <Button variant="destructive" size="sm" onClick={handleCancelTask}>
              <Square className="mr-2 h-4 w-4" />
              Cancel Task
            </Button>
          )}
          <Button variant="outline" size="sm" onClick={downloadOutput}>
            <Download className="mr-2 h-4 w-4" />
            Download Output
          </Button>
        </div>
      </div>

      <div className="grid gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Task Details</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-medium mb-1">Instructions</h4>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                  {task.instructions}
                </p>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium">Created:</span>{' '}
                  {new Date(task.created_at).toLocaleString()}
                </div>
                {task.started_at && (
                  <div>
                    <span className="font-medium">Started:</span>{' '}
                    {new Date(task.started_at).toLocaleString()}
                  </div>
                )}
                {task.completed_at && (
                  <div>
                    <span className="font-medium">Completed:</span>{' '}
                    {new Date(task.completed_at).toLocaleString()}
                  </div>
                )}
                {task.worktree_path && (
                  <div>
                    <span className="font-medium">Worktree:</span>{' '}
                    <code className="text-xs bg-gray-100 px-1 py-0.5 rounded">
                      {task.worktree_path}
                    </code>
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Terminal className="h-5 w-5" />
              Output
            </CardTitle>
            <CardDescription>
              {task.status === TaskStatus.RUNNING
                ? 'Live output from Claude Code'
                : 'Task output log'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <pre
              ref={outputRef}
              onScroll={handleScroll}
              className="bg-black text-green-400 p-4 rounded-md overflow-auto max-h-[600px] text-sm font-mono"
            >
              {output.length > 0 ? output.join('\n') : 'Waiting for output...'}
              {task.status === TaskStatus.RUNNING && (
                <span className="animate-pulse">▊</span>
              )}
            </pre>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}