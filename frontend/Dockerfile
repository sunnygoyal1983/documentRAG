FROM node:18-alpine
WORKDIR /app

# copy package files first to leverage Docker cache
COPY package.json package-lock.json* ./

# install deps (including dev deps so tests can run inside container)
RUN npm install --legacy-peer-deps

# copy app sources
COPY . .

# build for production (next start requires build)
RUN npm run build || true

EXPOSE 3000
CMD ["npm", "run", "dev"]
