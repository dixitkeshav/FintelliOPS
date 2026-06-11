const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 3000;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private shouldReconnect = true;

  constructor(private endpoint: string) {}

  connect(onMessage: (data: unknown) => void, onError?: (error: Event) => void) {
    try {
      this.shouldReconnect = true;
      this.ws = new WebSocket(`${WS_BASE_URL}${this.endpoint}`);

      this.ws.onopen = () => {
        console.log(`WebSocket connected to ${this.endpoint}`);
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const parsed: unknown = JSON.parse(event.data);
          onMessage(parsed);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        // Avoid noisy console errors for expected disconnects in React dev unmount cycles.
        if (!this.shouldReconnect) return;
        console.error('WebSocket error:', error);
        onError?.(error);
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        if (this.shouldReconnect) {
          this.attemptReconnect(onMessage, onError);
        }
      };
    } catch (error) {
      console.error('Error creating WebSocket:', error);
    }
  }

  private attemptReconnect(onMessage: (data: unknown) => void, onError?: (error: Event) => void) {
    if (!this.shouldReconnect) return;
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      this.reconnectTimer = setTimeout(() => {
        this.connect(onMessage, onError);
      }, this.reconnectDelay);
    }
  }

  send(data: unknown) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  disconnect() {
    this.shouldReconnect = false;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}
