/**
 * Jest 설정
 * @type {import('jest').Config}
 */
const config = {
  // 테스트 환경
  testEnvironment: 'jsdom',

  // 설정 파일
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],

  // 모듈 경로 별칭 (tsconfig paths와 매칭)
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    // CSS 모듈 모킹
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
  },

  // TypeScript 변환
  transform: {
    '^.+\\.(ts|tsx)$': ['ts-jest', {
      tsconfig: 'tsconfig.json',
    }],
  },

  // 테스트 파일 패턴
  testMatch: [
    '**/__tests__/**/*.(ts|tsx)',
    '**/?(*.)+(spec|test).(ts|tsx)',
  ],

  // 무시할 경로
  testPathIgnorePatterns: [
    '<rootDir>/node_modules/',
    '<rootDir>/.next/',
  ],

  // 커버리지 설정
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/index.ts',
  ],

  // 커버리지 임계값
  coverageThreshold: {
    global: {
      branches: 50,
      functions: 50,
      lines: 50,
      statements: 50,
    },
  },
};

module.exports = config;
