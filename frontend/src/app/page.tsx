'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // 임시: 로그인 우회, 바로 대시보드로
    router.push('/dashboard');
    
    // TODO: 로그인 기능 수정 후 아래 코드로 변경
    // const token = localStorage.getItem('access_token');
    // if (token) {
    //   router.push('/dashboard');
    // } else {
    //   router.push('/login');
    // }
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">로딩 중...</p>
      </div>
    </div>
  );
}

