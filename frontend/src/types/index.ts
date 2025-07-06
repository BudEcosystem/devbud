export interface Repository {
  id: string;
  name: string;
  path: string;
  default_branch: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  deleted_at?: string;
  task_count?: number;
  active_task_count?: number;
}

export interface CreateRepositoryDto {
  name: string;
  path: string;
  default_branch: string;
  description?: string;
}

export interface UpdateRepositoryDto {
  name?: string;
  default_branch?: string;
  description?: string;
}

export enum TaskStatus {
  PENDING = "pending",
  RUNNING = "running",
  COMPLETED = "completed",
  FAILED = "failed",
  CANCELLED = "cancelled",
}

export interface Task {
  id: string;
  repository_id: string;
  branch_name: string;
  instructions: string;
  status: TaskStatus;
  worktree_path?: string;
  output_log: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  repository?: {
    id: string;
    name: string;
  };
}

export interface CreateTaskDto {
  repository_id: string;
  branch_name: string;
  instructions: string;
}

export interface TaskOutput {
  task_id: string;
  output: string;
  timestamp: string;
}

export interface WebSocketMessage {
  type: "output" | "ping" | "status_update" | "error";
  task_id?: string;
  output?: string;
  timestamp?: number;
  active_tasks?: string[];
  error?: string;
}

export interface ApiError {
  detail: string;
  status_code?: number;
}