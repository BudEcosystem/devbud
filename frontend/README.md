# DevBud Frontend

Modern React/Next.js frontend for the DevBud development management dashboard.

## Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS v4
- **UI Components**: Custom components inspired by shadcn/ui
- **State Management**: React Query for server state
- **API Communication**: Axios for REST, WebSocket for real-time updates
- **Icons**: Lucide React

## Features

- 📊 **Dashboard**: Overview of repositories and tasks
- 📁 **Repository Management**: Add, edit, and delete git repositories
- 🚀 **Task Management**: Create and monitor Claude Code generation tasks
- 🔄 **Real-time Updates**: Live streaming of task output via WebSocket
- 📱 **Responsive Design**: Works on desktop and mobile devices
- 🌙 **Dark Mode**: Automatic dark mode based on system preferences

## Development

### Prerequisites

- Node.js 18+ and npm
- Backend API running on http://localhost:8000

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env.local

# Start development server
npm run dev
```

The application will be available at http://localhost:3000

### Environment Variables

Create a `.env.local` file with:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript compiler check

## Project Structure

```
src/
├── app/                    # Next.js app directory
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Dashboard page
│   ├── repositories/      # Repository pages
│   └── tasks/             # Task pages
├── components/            # React components
│   ├── layout/           # Layout components
│   ├── repositories/     # Repository-specific components
│   ├── tasks/           # Task-specific components
│   └── ui/              # Reusable UI components
├── lib/                  # Utility functions and clients
│   ├── api-client.ts    # REST API client
│   ├── websocket-client.ts # WebSocket client
│   └── utils.ts         # Helper functions
└── types/               # TypeScript type definitions
```

## Key Components

### API Client (`lib/api-client.ts`)
Handles all REST API communication with proper error handling and interceptors.

### WebSocket Client (`lib/websocket-client.ts`)
Manages WebSocket connections for real-time task output streaming with automatic reconnection.

### UI Components
- `Button`, `Card`, `Input`, etc. - Reusable UI primitives
- `RepositoryCard`, `TaskCard` - Domain-specific components
- `MainNav`, `Header` - Layout components

## Pages

### Dashboard (`/`)
- Statistics overview
- Recent tasks
- Quick navigation

### Repositories (`/repositories`)
- List all repositories
- Add new repository
- Repository details with tasks

### Tasks (`/tasks`)
- List all tasks with filtering
- Create new task
- Real-time task monitoring

## Docker Support

### Development
```bash
docker-compose up frontend
```

### Production
```bash
docker build -t devbud-frontend .
docker run -p 3000:3000 devbud-frontend
```

## Deployment

The frontend can be deployed to any platform that supports Next.js:

- Vercel (recommended)
- Netlify
- AWS Amplify
- Docker container

### Build for Production

```bash
npm run build
```

This creates an optimized production build in the `.next` directory.

## Contributing

1. Follow the existing code style
2. Use TypeScript for all new code
3. Create reusable components in `components/ui`
4. Keep components small and focused
5. Use React Query for server state management

## Troubleshooting

### API Connection Issues
- Ensure backend is running on the correct port
- Check CORS settings in backend
- Verify environment variables are set correctly

### WebSocket Connection Issues
- Check browser console for connection errors
- Ensure WebSocket URL is correct
- Verify backend WebSocket endpoints are working

### Build Errors
- Clear `.next` directory and rebuild
- Check for TypeScript errors with `npm run type-check`
- Ensure all dependencies are installed

## Learn More

To learn more about the technologies used:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API
- [React Query](https://tanstack.com/query/latest) - powerful asynchronous state management
- [Tailwind CSS](https://tailwindcss.com/docs) - utility-first CSS framework
- [TypeScript](https://www.typescriptlang.org/docs) - typed superset of JavaScript