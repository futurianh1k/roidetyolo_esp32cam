/**
 * WebSocket 클라이언트
 * 실시간 장비 상태 업데이트
 */

import { io, Socket } from 'socket.io-client';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

class WebSocketClient {
  private socket: Socket | null = null;
  private token: string | null = null;

  connect(accessToken: string) {
    if (this.socket?.connected) {
      return;
    }

    this.token = accessToken;
    this.socket = io(`${WS_URL}/ws`, {
      query: { token: accessToken },
      transports: ['websocket'],
    });

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
    });

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
    });

    this.socket.on('error', (error) => {
      console.error('WebSocket error:', error);
    });
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  subscribeDevice(deviceId: number) {
    if (this.socket?.connected) {
      this.socket.emit('message', JSON.stringify({
        type: 'subscribe_device',
        device_id: deviceId,
      }));
    }
  }

  unsubscribeDevice(deviceId: number) {
    if (this.socket?.connected) {
      this.socket.emit('message', JSON.stringify({
        type: 'unsubscribe_device',
        device_id: deviceId,
      }));
    }
  }

  onMessage(callback: (message: any) => void) {
    if (this.socket) {
      this.socket.on('message', (data: string) => {
        try {
          const message = JSON.parse(data);
          callback(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      });
    }
  }

  sendPing() {
    if (this.socket?.connected) {
      this.socket.emit('message', JSON.stringify({ type: 'ping' }));
    }
  }
}

export const wsClient = new WebSocketClient();
export default wsClient;

