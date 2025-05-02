import { getApiUrl } from "./config";

// WebSocketService.ts
type EventHandler = (data: any) => void;

class WebSocketService {
  private socket: WebSocket | null = null;
  private eventHandlers: Record<string, EventHandler[]> = {};

  connect(batch_id: string): void {
    let apiUrl = getApiUrl() as string | null;
    
    console.log('API URL: websocket', apiUrl);
    if (apiUrl) {
      apiUrl = apiUrl.replace(/^https?/, match => match === "https" ? "wss" : "ws");
    } else {
      throw new Error('API URL is null');
    }
    console.log('Connecting to WebSocket:', apiUrl);
    if (this.socket) return; // Prevent duplicate connections
    this.socket = new WebSocket(`${apiUrl}/socket/${batch_id}`);

    this.socket.onopen = () => {
      console.log('WebSocket connection opened.');
      this._emit('open', undefined);
    };

    this.socket.onmessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        this._emit('message', data);
      } catch (err) {
        console.error('Error parsing message:', err);
      }
    };

    this.socket.onerror = (error: Event) => {
      console.error('WebSocket error:', error);
      this._emit('error', error);
    };

    this.socket.onclose = (event: CloseEvent) => {
      console.log('WebSocket closed:', event);
      this._emit('close', event);
      this.socket = null;
    };
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
      console.log('WebSocket connection closed manually.');
    }
  }

  send(data: any): void {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data));
    } else {
      console.error('WebSocket is not open. Cannot send:', data);
    }
  }

  on(event: string, handler: EventHandler): void {
    if (!this.eventHandlers[event]) {
      this.eventHandlers[event] = [];
    }
    this.eventHandlers[event].push(handler);
  }

  off(event: string, handler: EventHandler): void {
    if (!this.eventHandlers[event]) return;
    this.eventHandlers[event] = this.eventHandlers[event].filter(h => h !== handler);
  }

  private _emit(event: string, data: any): void {
    if (this.eventHandlers[event]) {
      this.eventHandlers[event].forEach(handler => handler(data));
    }
  }
}

const webSocketService = new WebSocketService();
export default webSocketService;
