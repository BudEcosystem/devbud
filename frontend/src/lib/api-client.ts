import axios, { AxiosInstance, AxiosError } from 'axios';
import {
  Repository,
  CreateRepositoryDto,
  UpdateRepositoryDto,
  Task,
  CreateTaskDto,
  TaskOutput,
  ApiError,
} from '@/types';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token if available
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ApiError>) => {
        const customError: ApiError = {
          detail: error.response?.data?.detail || error.message || 'An error occurred',
          status_code: error.response?.status,
        };
        return Promise.reject(customError);
      }
    );
  }

  // Repository endpoints
  async getRepositories(): Promise<Repository[]> {
    const response = await this.client.get<Repository[]>('/api/v1/repositories/');
    return response.data;
  }

  async getRepository(id: string): Promise<Repository> {
    const response = await this.client.get<Repository>(`/api/v1/repositories/${id}`);
    return response.data;
  }

  async createRepository(data: CreateRepositoryDto): Promise<Repository> {
    const response = await this.client.post<Repository>('/api/v1/repositories/', data);
    return response.data;
  }

  async updateRepository(id: string, data: UpdateRepositoryDto): Promise<Repository> {
    const response = await this.client.patch<Repository>(`/api/v1/repositories/${id}`, data);
    return response.data;
  }

  async deleteRepository(id: string): Promise<void> {
    await this.client.delete(`/api/v1/repositories/${id}`);
  }

  async getRepositoryTasks(id: string): Promise<Task[]> {
    const response = await this.client.get<Task[]>(`/api/v1/repositories/${id}/tasks`);
    return response.data;
  }

  // Task endpoints
  async getTasks(repositoryId?: string, status?: string): Promise<Task[]> {
    const params = new URLSearchParams();
    if (repositoryId) params.append('repository_id', repositoryId);
    if (status) params.append('status', status);
    
    const response = await this.client.get<Task[]>(`/api/v1/tasks/?${params.toString()}`);
    return response.data;
  }

  async getTask(id: string): Promise<Task> {
    const response = await this.client.get<Task>(`/api/v1/tasks/${id}`);
    return response.data;
  }

  async createTask(data: CreateTaskDto): Promise<Task> {
    const response = await this.client.post<Task>('/api/v1/tasks/', data);
    return response.data;
  }

  async cancelTask(id: string): Promise<{ message: string }> {
    const response = await this.client.post<{ message: string }>(`/api/v1/tasks/${id}/cancel`);
    return response.data;
  }

  async getTaskOutput(id: string): Promise<TaskOutput> {
    const response = await this.client.get<TaskOutput>(`/api/v1/tasks/${id}/output`);
    return response.data;
  }

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    const response = await this.client.get<{ status: string }>('/health');
    return response.data;
  }
}

export const apiClient = new ApiClient();