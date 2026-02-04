import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: './',
  build: {
    assetsDir: '', // assets 폴더를 만들지 않고 루트에 바로 파일을 생성합니다.
  }
})
