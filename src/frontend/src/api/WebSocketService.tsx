import { getApiUrl, headerBuilder } from '../api/config';

// Polling-based status stream service that preserves the existing event interface.
type EventHandler = (data: any) => void;

class WebSocketService {
  private pollInterval: ReturnType<typeof setInterval> | null = null;
  private isConnected = false;
  private activeBatchId: string | null = null;
  private lastKnownStatus: Record<string, string> = {};
  private eventHandlers: Record<string, EventHandler[]> = {};

  private async pollBatchSummary(batchId: string): Promise<void> {
    const apiUrl = getApiUrl();
    if (!apiUrl) {
      this._emit('error', new Error('API URL is null'));
      return;
    }

    try {
      const response = await fetch(`${apiUrl}/batch-summary/${batchId}`, {
        headers: headerBuilder({}),
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch batch status: ${response.status}`);
      }

      const payload = await response.json();
      const files = payload?.files || [];
      let allFilesTerminal = files.length > 0;

      for (const file of files) {
        const fileId = file?.file_id;
        const status = (file?.status || '').toLowerCase();
        if (!fileId || !status) {
          continue;
        }

        if (!['completed', 'failed', 'error'].includes(status)) {
          allFilesTerminal = false;
        }

        const previousStatus = this.lastKnownStatus[fileId];
        if (previousStatus !== status) {
          this.lastKnownStatus[fileId] = status;

          this._emit('message', {
            batch_id: batchId,
            file_id: fileId,
            agent_type: 'Polling agent',
            agent_message: `Status changed to ${status}`,
            process_status: status,
            file_result: file?.file_result || null,
          });
        }
      }

      if (allFilesTerminal) {
        this.disconnect();
      }
    } catch (error) {
      this._emit('error', error);
    }
  }

  connect(batch_id: string): void {
    if (this.isConnected && this.activeBatchId === batch_id) return;

    this.disconnect();

    this.isConnected = true;
    this.activeBatchId = batch_id;
    this.lastKnownStatus = {};
    this._emit('open', undefined);

    // Poll once immediately, then at a fixed interval.
    void this.pollBatchSummary(batch_id);
    this.pollInterval = setInterval(() => {
      if (this.isConnected && this.activeBatchId) {
        void this.pollBatchSummary(this.activeBatchId);
      }
    }, 3000);
  }

  disconnect(): void {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }

    const wasConnected = this.isConnected;
    this.isConnected = false;
    this.activeBatchId = null;
    this.lastKnownStatus = {};

    if (wasConnected) {
      this._emit('close', { reason: 'polling_stopped' });
    }
  }

  send(data: any): void {
    // Polling transport is read-only from client perspective.
    console.debug('send() is ignored in polling mode:', data);
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
