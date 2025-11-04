const express = require('express');
const cors = require('cors');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3001;
const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';

// 간단한 in-memory 데이터베이스
const db = {
  users: new Map(),
  projects: new Map(),
  userIdCounter: 1,
  projectIdCounter: 1,
  
  createUser(username, email, password) {
    const id = this.userIdCounter++;
    const user = { id, username, email, password, createdAt: new Date() };
    this.users.set(id, user);
    this.users.set('email:' + email, user);
    this.users.set('username:' + username, user);
    return user;
  },
  
  getUserByEmail(email) {
    return this.users.get('email:' + email);
  },
  
  getUserByUsername(username) {
    return this.users.get('username:' + username);
  },
  
  getUserById(id) {
    return this.users.get(id);
  },
  
  createProject(userId, name, data) {
    const id = this.projectIdCounter++;
    const project = {
      id, userId, name,
      data: typeof data === 'string' ? data : JSON.stringify(data),
      createdAt: new Date(),
      updatedAt: new Date()
    };
    this.projects.set(id, project);
    return project;
  },
  
  getProjectsByUserId(userId) {
    return Array.from(this.projects.values()).filter(p => p.userId === userId);
  },
  
  getProjectById(id) {
    return this.projects.get(id);
  },
  
  updateProject(id, data) {
    const project = this.projects.get(id);
    if (project) {
      project.data = typeof data === 'string' ? data : JSON.stringify(data);
      project.updatedAt = new Date();
      this.projects.set(id, project);
    }
    return project;
  },
  
  deleteProject(id) {
    return this.projects.delete(id);
  }
};

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
app.get('/api/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'artify-backend',
    version: '1.1.0',
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
      type: 'in-memory',
      users: db.users.size / 3, // 각 유저는 3개 키로 저장됨
      projects: db.projects.size
    }
  });
});

// Auth routes
app.post('/api/register', async (req, res) => {
  try {
    const { username, email, password } = req.body;
    if (!username || !email || !password) {
      return res.status(400).json({ error: 'All fields are required' });
    }
    if (db.getUserByEmail(email)) {
      return res.status(400).json({ error: 'Email already exists' });
    }
    if (db.getUserByUsername(username)) {
      return res.status(400).json({ error: 'Username already exists' });
    }
    const hashedPassword = await bcrypt.hash(password, 10);
    const user = db.createUser(username, email, hashedPassword);
    const token = jwt.sign({ id: user.id, username: user.username, email: user.email }, JWT_SECRET, { expiresIn: '7d' });
    res.status(201).json({ message: 'User registered successfully', token, user: { id: user.id, username: user.username, email: user.email }});
  } catch (error) {
    res.status(500).json({ error: 'Server error' });
  }
});

app.post('/api/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    if (!email || !password) return res.status(400).json({ error: 'Email and password are required' });
    const user = db.getUserByEmail(email);
    if (!user) return res.status(401).json({ error: 'Invalid credentials' });
    const validPassword = await bcrypt.compare(password, user.password);
    if (!validPassword) return res.status(401).json({ error: 'Invalid credentials' });
    const token = jwt.sign({ id: user.id, username: user.username, email: user.email }, JWT_SECRET, { expiresIn: '7d' });
    res.json({ message: 'Login successful', token, user: { id: user.id, username: user.username, email: user.email }});
  } catch (error) {
    res.status(500).json({ error: 'Server error' });
  }
});

// Project routes
app.get('/api/projects', authenticateToken, (req, res) => {
  try {
    const projects = db.getProjectsByUserId(req.user.id);
    const projectList = projects.map(p => ({ id: p.id, name: p.name, createdAt: p.createdAt, updatedAt: p.updatedAt }));
    res.json({ projects: projectList });
  } catch (error) {
    res.status(500).json({ error: 'Server error' });
  }
});

app.post('/api/projects', authenticateToken, (req, res) => {
  try {
    const { name, data } = req.body;
    if (!name) return res.status(400).json({ error: 'Project name is required' });
    const project = db.createProject(req.user.id, name, data || {});
    res.status(201).json({ message: 'Project created successfully', project: { id: project.id, name: project.name, createdAt: project.createdAt, updatedAt: project.updatedAt }});
  } catch (error) {
    res.status(500).json({ error: 'Server error' });
  }
});

app.get('/api/projects/:id', authenticateToken, (req, res) => {
  try {
    const projectId = parseInt(req.params.id);
    const project = db.getProjectById(projectId);
    if (!project) return res.status(404).json({ error: 'Project not found' });
    if (project.userId !== req.user.id) return res.status(403).json({ error: 'Access denied' });
    res.json({ id: project.id, name: project.name, data: project.data, createdAt: project.createdAt, updatedAt: project.updatedAt });
  } catch (error) {
    res.status(500).json({ error: 'Server error' });
  }
});

app.put('/api/projects/:id', authenticateToken, (req, res) => {
  try {
    const projectId = parseInt(req.params.id);
    const { name, data } = req.body;
    const project = db.getProjectById(projectId);
    if (!project) return res.status(404).json({ error: 'Project not found' });
    if (project.userId !== req.user.id) return res.status(403).json({ error: 'Access denied' });
    if (name) project.name = name;
    if (data) {
      const updatedProject = db.updateProject(projectId, data);
      project.data = updatedProject.data;
      project.updatedAt = updatedProject.updatedAt;
    }
    res.json({ message: 'Project updated successfully', project: { id: project.id, name: project.name, updatedAt: project.updatedAt }});
  } catch (error) {
    res.status(500).json({ error: 'Server error' });
  }
});

app.delete('/api/projects/:id', authenticateToken, (req, res) => {
  try {
    const projectId = parseInt(req.params.id);
    const project = db.getProjectById(projectId);
    if (!project) return res.status(404).json({ error: 'Project not found' });
    if (project.userId !== req.user.id) return res.status(403).json({ error: 'Access denied' });
    db.deleteProject(projectId);
    res.json({ message: 'Project deleted successfully' });
  } catch (error) {
    res.status(500).json({ error: 'Server error' });
  }
});

app.listen(PORT, () => {
  console.log('='.repeat(50));
  console.log('🚀 Artify Backend Server Started');
  console.log('='.repeat(50));
  console.log('Port:', PORT);
  console.log('Environment:', process.env.NODE_ENV || 'development');
  console.log('JWT Secret:', JWT_SECRET ? 'Configured ✓' : 'Using default (not secure!)');
  console.log('');
  console.log('CORS Configuration:');
  console.log('- Allowed Origins:');
  console.log('  • https://artify-ruddy.vercel.app');
  console.log('  • *.vercel.app (all Vercel deployments)');
  console.log('  • localhost (development)');
  console.log('');
  console.log('In-memory database initialized');
  console.log('Ready to accept connections!');
  console.log('='.repeat(50));
});