const express = require('express');
const cors = require('cors');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
require('dotenv').config();

const { initDatabase, db } = require('./database');

const app = express();
const PORT = process.env.PORT || 3001;
const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';

// CORS Middleware - 모든 Vercel 도메인 허용
const corsOptions = {
  origin: function (origin, callback) {
    const allowedOrigins = [
      'https://artify-ruddy.vercel.app',
      'http://localhost:3000',
      'http://localhost:5173',
      'http://127.0.0.1:5173',
      'http://localhost:5500'
    ];

    // Allow requests with no origin (like mobile apps or curl requests)
    if (!origin) return callback(null, true);

    // Allow all Vercel preview deployments
    if (origin.endsWith('.vercel.app')) {
      return callback(null, true);
    }

    if (allowedOrigins.indexOf(origin) !== -1) {
      callback(null, true);
    } else {
      console.log('CORS blocked origin:', origin);
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  optionsSuccessStatus: 200
};

app.use(cors(corsOptions));

// Preflight 요청 처리
app.options('*', cors(corsOptions));

app.use(express.json());

// Auth middleware
const authenticateToken = (req, res, next) => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];
  if (!token) return res.status(401).json({ error: 'Access token required' });
  jwt.verify(token, JWT_SECRET, (err, user) => {
    if (err) return res.status(403).json({ error: 'Invalid token' });
    req.user = user;
    next();
  });
};

// Health check
app.get('/api/health', async (req, res) => {
  try {
    const stats = await db.getStats();
    res.json({
      status: 'healthy',
      service: 'artify-backend',
      version: '2.0.0',
      timestamp: new Date().toISOString(),
      cors: {
        enabled: true,
        allowedOrigins: [
          'https://artify-ruddy.vercel.app',
          '*.vercel.app',
          'localhost'
        ]
      },
      database: {
        type: 'PostgreSQL',
        connected: true,
        users: stats.users,
        projects: stats.projects
      }
    });
  } catch (error) {
    res.status(500).json({
      status: 'error',
      service: 'artify-backend',
      database: {
        type: 'PostgreSQL',
        connected: false,
        error: error.message
      }
    });
  }
});

// Auth routes
app.post('/api/register', async (req, res) => {
  try {
    const { username, email, password } = req.body;
    if (!username || !email || !password) {
      return res.status(400).json({ error: 'All fields are required' });
    }

    // Check if user already exists
    const existingEmail = await db.getUserByEmail(email);
    if (existingEmail) {
      return res.status(400).json({ error: 'Email already exists' });
    }

    const existingUsername = await db.getUserByUsername(username);
    if (existingUsername) {
      return res.status(400).json({ error: 'Username already exists' });
    }

    const hashedPassword = await bcrypt.hash(password, 10);
    const user = await db.createUser(username, email, hashedPassword);
    const token = jwt.sign({ id: user.id, username: user.username, email: user.email }, JWT_SECRET, { expiresIn: '7d' });

    res.status(201).json({
      message: 'User registered successfully',
      token,
      user: { id: user.id, username: user.username, email: user.email }
    });
  } catch (error) {
    console.error('Register error:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

app.post('/api/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    if (!email || !password) {
      return res.status(400).json({ error: 'Email and password are required' });
    }

    const user = await db.getUserByEmail(email);
    if (!user) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    const validPassword = await bcrypt.compare(password, user.password);
    if (!validPassword) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    const token = jwt.sign({ id: user.id, username: user.username, email: user.email }, JWT_SECRET, { expiresIn: '7d' });

    res.json({
      message: 'Login successful',
      token,
      user: { id: user.id, username: user.username, email: user.email }
    });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

// Project routes
app.get('/api/projects', authenticateToken, async (req, res) => {
  try {
    const projects = await db.getProjectsByUserId(req.user.id);
    res.json({ projects });
  } catch (error) {
    console.error('Get projects error:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

app.post('/api/projects', authenticateToken, async (req, res) => {
  try {
    const { name, data } = req.body;
    if (!name) {
      return res.status(400).json({ error: 'Project name is required' });
    }

    const project = await db.createProject(req.user.id, name, data || {});

    res.status(201).json({
      message: 'Project created successfully',
      project: {
        id: project.id,
        name: project.name,
        created_at: project.created_at,
        updated_at: project.updated_at
      }
    });
  } catch (error) {
    console.error('Create project error:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

app.get('/api/projects/:id', authenticateToken, async (req, res) => {
  try {
    const projectId = parseInt(req.params.id);
    const project = await db.getProjectById(projectId);

    if (!project) {
      return res.status(404).json({ error: 'Project not found' });
    }

    if (project.user_id !== req.user.id) {
      return res.status(403).json({ error: 'Access denied' });
    }

    res.json({
      id: project.id,
      name: project.name,
      data: typeof project.data === 'string' ? JSON.parse(project.data) : project.data,
      createdAt: project.created_at,
      updatedAt: project.updated_at
    });
  } catch (error) {
    console.error('Get project error:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

app.put('/api/projects/:id', authenticateToken, async (req, res) => {
  try {
    const projectId = parseInt(req.params.id);
    const { name, data } = req.body;

    const project = await db.getProjectById(projectId);
    if (!project) {
      return res.status(404).json({ error: 'Project not found' });
    }

    if (project.user_id !== req.user.id) {
      return res.status(403).json({ error: 'Access denied' });
    }

    let updatedProject;
    if (name && data) {
      updatedProject = await db.updateProject(projectId, data);
      await db.updateProjectName(projectId, name);
    } else if (name) {
      updatedProject = await db.updateProjectName(projectId, name);
    } else if (data) {
      updatedProject = await db.updateProject(projectId, data);
    }

    res.json({
      message: 'Project updated successfully',
      project: {
        id: updatedProject.id,
        name: updatedProject.name,
        updatedAt: updatedProject.updated_at
      }
    });
  } catch (error) {
    console.error('Update project error:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

app.delete('/api/projects/:id', authenticateToken, async (req, res) => {
  try {
    const projectId = parseInt(req.params.id);

    const project = await db.getProjectById(projectId);
    if (!project) {
      return res.status(404).json({ error: 'Project not found' });
    }

    if (project.user_id !== req.user.id) {
      return res.status(403).json({ error: 'Access denied' });
    }

    await db.deleteProject(projectId);
    res.json({ message: 'Project deleted successfully' });
  } catch (error) {
    console.error('Delete project error:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

// Initialize database and start server
async function startServer() {
  try {
    // Check if DATABASE_URL is set
    if (!process.env.DATABASE_URL) {
      console.error('❌ DATABASE_URL is not set in environment variables');
      console.error('Please set DATABASE_URL in .env file');
      console.error('Example: DATABASE_URL=postgresql://username:password@localhost:5432/artify_db');
      process.exit(1);
    }

    // Initialize database tables
    await initDatabase();

    // Start Express server
    app.listen(PORT, () => {
      console.log('='.repeat(50));
      console.log('🚀 Artify Backend Server Started');
      console.log('='.repeat(50));
      console.log('Port:', PORT);
      console.log('Environment:', process.env.NODE_ENV || 'development');
      console.log('JWT Secret:', JWT_SECRET !== 'your-secret-key' ? 'Configured ✓' : 'Using default (not secure!)');
      console.log('');
      console.log('CORS Configuration:');
      console.log('- Allowed Origins:');
      console.log('  • https://artify-ruddy.vercel.app');
      console.log('  • *.vercel.app (all Vercel deployments)');
      console.log('  • localhost (development)');
      console.log('');
      console.log('Database: PostgreSQL ✓');
      console.log('Ready to accept connections!');
      console.log('='.repeat(50));
    });
  } catch (error) {
    console.error('❌ Failed to start server:', error);
    process.exit(1);
  }
}

startServer();