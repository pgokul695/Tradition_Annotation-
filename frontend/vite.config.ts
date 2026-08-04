import { defineConfig } from 'vite'; import react from '@vitejs/plugin-react';
export default defineConfig({plugins:[react()],server:{host:'0.0.0.0',port:5003,strictPort:true,allowedHosts:['t3.gokulp.online'],proxy:{'/api':'http://127.0.0.1:5002','/dataset':'http://127.0.0.1:5002'}}});
