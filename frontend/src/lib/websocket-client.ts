import { WebSocketMessage } from '@/types';

export type WebSocketEventHandler = (message: WebSocketMessage) => void;

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectInterval: number = 5000;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private eventHandlers: Map<string, Set<WebSocketEventHandler>> = new Map();
  private isIntentionallyClosed: boolean = false;

  constructor(private baseUrl: string = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000') {}

  connectToTask(taskId: string): void {
    this.connect(`${this.baseUrl}/ws/task/${taskId}`);
  }

  connectToAllTasks(): void {
    this.connect(`${this.baseUrl}/ws/tasks`);
  }

  private connect(url: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.close();
    }

    this.isIntentionallyClosed = false;

    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.clearReconnectTimer();
        this.emit('connected', { type: 'status_update' });
      };

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          
          // Handle ping messages
          if (message.type === 'ping') {
            this.ws?.send('pong');
            return;
          }

          this.emit('message', message);
          
          // Emit specific event based on message type
          if (message.type) {
            this.emit(message.type, message);
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.emit('error', { type: 'error', error: 'WebSocket connection error' });
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.emit('disconnected', { type: 'status_update' });
        
        if (!this.isIntentionallyClosed) {
          this.scheduleReconnect(url);
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.scheduleReconnect(url);
    }
  }

  private scheduleReconnect(url: string): void {
    this.clearReconnectTimer();
    
    this.reconnectTimer = setTimeout(() => {
      console.log('Attempting to reconnect WebSocket...');
      this.connect(url);
    }, this.reconnectInterval);
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  send(data: string | object): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      const message = typeof data === 'string' ? data : JSON.stringify(data);
      this.ws.send(message);
    } else {
      console.warn('WebSocket is not connected');
    }
  }

  on(event: string, handler: WebSocketEventHandler): () => void {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, new Set());
    }
    
    this.eventHandlers.get(event)!.add(handler);
    
    // Return unsubscribe function
    return () => {
      this.eventHandlers.get(event)?.delete(handler);
    };
  }

  off(event: string, handler: WebSocketEventHandler): void {
    this.eventHandlers.get(event)?.delete(handler);
  }

  private emit(event: string, message: WebSocketMessage): void {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      handlers.forEach(handler => handler(message));
    }
  }

  disconnect(): void {
    this.isIntentionallyClosed = true;
    this.clearReconnectTimer();
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  getReadyState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED;
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// Singleton instance
export const wsClient = new WebSocketClient();