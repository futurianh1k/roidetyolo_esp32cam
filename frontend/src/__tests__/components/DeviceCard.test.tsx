/**
 * DeviceCard 컴포넌트 테스트
 */
import React from 'react';
import { render, screen } from '@testing-library/react';
import DeviceCard from '@/components/DeviceCard';

// Device 타입 정의
const mockDevice = {
  id: 1,
  device_id: 'test_device_001',
  device_name: 'Test Camera',
  device_type: 'camera',
  ip_address: '192.168.1.100',
  rtsp_url: 'rtsp://192.168.1.100:554/stream',
  mqtt_topic: 'devices/test_device_001',
  is_online: true,
  registered_at: '2024-01-01T00:00:00Z',
  last_seen_at: '2024-01-15T12:00:00Z',
  location: 'Office Room 1',
  description: 'Test description',
};

describe('DeviceCard', () => {
  it('장비 이름이 표시되어야 함', () => {
    render(<DeviceCard device={mockDevice} />);
    
    expect(screen.getByText('Test Camera')).toBeInTheDocument();
  });

  it('장비 ID가 표시되어야 함', () => {
    render(<DeviceCard device={mockDevice} />);
    
    expect(screen.getByText(/test_device_001/)).toBeInTheDocument();
  });

  it('온라인 상태가 표시되어야 함', () => {
    render(<DeviceCard device={mockDevice} />);
    
    // 온라인 표시 확인 (텍스트 또는 아이콘)
    expect(screen.getByText(/온라인|Online/i)).toBeInTheDocument();
  });

  it('오프라인 상태가 표시되어야 함', () => {
    const offlineDevice = { ...mockDevice, is_online: false };
    render(<DeviceCard device={offlineDevice} />);
    
    expect(screen.getByText(/오프라인|Offline/i)).toBeInTheDocument();
  });

  it('위치 정보가 표시되어야 함', () => {
    render(<DeviceCard device={mockDevice} />);
    
    expect(screen.getByText('Office Room 1')).toBeInTheDocument();
  });

  it('IP 주소가 표시되어야 함', () => {
    render(<DeviceCard device={mockDevice} />);
    
    expect(screen.getByText('192.168.1.100')).toBeInTheDocument();
  });
});
