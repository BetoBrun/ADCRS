services:
  backend:
    build:
      context: .
      dockerfile: infra/docker/backend.Dockerfile
    container_name: adcrs-backend
    restart: unless-stopped
    environment:
      API_CORS_ORIGINS: '["http://localhost:3000","http://localhost:5173"]'
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    networks:
      - adcrs-net

  frontend:
    build:
      context: .
      dockerfile: infra/docker/frontend.Dockerfile
    container_name: adcrs-frontend
    restart: unless-stopped
    environment:
      VITE_API_URL: http://localhost:8000/api/v1
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "3000:3000"
    depends_on:
      - backend
    command: npm run dev -- --host 0.0.0.0 --port 3000
    networks:
      - adcrs-net

networks:
  adcrs-net:
    name: adcrs-net
    driver: bridge
