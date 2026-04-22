FROM node:20-alpine

WORKDIR /app

COPY frontend/src /app/src
COPY frontend/package.json /app/package.json
COPY frontend/index.html /app/index.html
COPY frontend/tsconfig.json /app/tsconfig.json
COPY frontend/tsconfig.node.json /app/tsconfig.node.json
COPY frontend/vite.config.ts /app/vite.config.ts

RUN npm install

RUN npm run build

CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "3000"]
