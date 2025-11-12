const express = require('express');
const cors = require('cors');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const rateLimit = require('express-rate-limit');
const swaggerUi = require('swagger-ui-express');
const swaggerJsdoc = require('swagger-jsdoc');
require('dotenv').config();

const { initDatabase, db } = require('./database');

const app = express();
const PORT = process.env.PORT || 3001;
const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';

// Swagger configuration
const swaggerOptions = {
  definition: {
    openapi: '3.0.0',
    info: {
      title: 'Artify Backend API',
      version: '2.0.0',
      description: 'Node.js Express + PostgreSQL 기반 인증 및 프로젝트 관리 API',
      contact: {
        name: 'Artify Team',
      },
    },
    servers: [
      {
        url: `http://localhost:${PORT}`,
        description: 'Development server',
      },
      {
        url: 'https://artify-backend.onrender.com',
        description: 'Production server',
      },
    ],
    components: {
      securitySchemes: {
        bearerAuth: {
          type: 'http',
          scheme: 'bearer',
          bearerFormat: 'JWT',
        },
      },
    },
    security: [
      {
        bearerAuth: [],
      },
    ],
  },
  apis: ['./server.js'], // Path to the API docs
};

const swaggerSpec = swaggerJsdoc(swaggerOptions);

// Rate limiting configuration
const generalLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP, please try again later.',
  standardHeaders: true,
  legacyHeaders: false,
});

const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 5, // Limit each IP to 5 login/register attempts per windowMs
  message: 'Too many authentication attempts, please try again later.',
  standardHeaders: true,
  legacyHeaders: false,
});

const projectLimiter = rateLimit({
  windowMs: 1 * 60 * 1000, // 1 minute
  max: 30, // Limit each IP to 30 project operations per minute
  message: 'Too many project operations, please slow down.',
  standardHeaders: true,
  legacyHeaders: false,
});

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

// Swagger UI
app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec, {
  explorer: true,
  customCss: '.swagger-ui .topbar { display: none }',
  customSiteTitle: 'Artify Backend API Docs',
}));

// Apply general rate limiting to all routes
app.use('/api/', generalLimiter);

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

/**
 * @swagger
 * /api/health:
 *   get:
 *     summary: 서버 상태 확인
 *     description: 서버와 데이터베이스 연결 상태를 확인합니다
 *     tags: [System]
 *     security: []
 *     responses:
 *       200:
 *         description: 서버 정상 작동
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 status:
 *                   type: string
 *                   example: healthy
 *                 service:
 *                   type: string
 *                   example: artify-backend
 *                 version:
 *                   type: string
 *                   example: 2.0.0
 *                 database:
 *                   type: object
 *                   properties:
 *                     type:
 *                       type: string
 *                       example: PostgreSQL
 *                     connected:
 *                       type: boolean
 *                       example: true
 */
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

/**
 * @swagger
 * /api/register:
 *   post:
 *     summary: 회원가입
 *     description: 새 사용자를 등록합니다
 *     tags: [Auth]
 *     security: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - username
 *               - email
 *               - password
 *             properties:
 *               username:
 *                 type: string
 *                 example: johndoe
 *               email:
 *                 type: string
 *                 format: email
 *                 example: john@example.com
 *               password:
 *                 type: string
 *                 format: password
 *                 example: securePassword123
 *     responses:
 *       201:
 *         description: 회원가입 성공
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 message:
 *                   type: string
 *                   example: User registered successfully
 *                 token:
 *                   type: string
 *                   example: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
 *                 user:
 *                   type: object
 *                   properties:
 *                     id:
 *                       type: integer
 *                       example: 1
 *                     username:
 *                       type: string
 *                       example: johndoe
 *                     email:
 *                       type: string
 *                       example: john@example.com
 *       400:
 *         description: 잘못된 요청 (필수 필드 누락 또는 중복)
 */
// Auth routes
app.post('/api/register', authLimiter, async (req, res) => {
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

/**
 * @swagger
 * /api/login:
 *   post:
 *     summary: 로그인
 *     description: 기존 사용자로 로그인합니다
 *     tags: [Auth]
 *     security: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - email
 *               - password
 *             properties:
 *               email:
 *                 type: string
 *                 format: email
 *                 example: john@example.com
 *               password:
 *                 type: string
 *                 format: password
 *                 example: securePassword123
 *     responses:
 *       200:
 *         description: 로그인 성공
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 message:
 *                   type: string
 *                 token:
 *                   type: string
 *                 user:
 *                   type: object
 *       401:
 *         description: 인증 실패
 */
app.post('/api/login', authLimiter, async (req, res) => {
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

/**
 * @swagger
 * /api/projects:
 *   get:
 *     summary: 프로젝트 목록 조회
 *     description: 현재 사용자의 모든 프로젝트를 조회합니다
 *     tags: [Projects]
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: 프로젝트 목록 조회 성공
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 projects:
 *                   type: array
 *                   items:
 *                     type: object
 *                     properties:
 *                       id:
 *                         type: integer
 *                       name:
 *                         type: string
 *                       created_at:
 *                         type: string
 *                         format: date-time
 *                       updated_at:
 *                         type: string
 *                         format: date-time
 *       401:
 *         description: 인증 필요
 */
// Optional auth middleware - allows both authenticated and non-authenticated requests
const optionalAuth = (req, res, next) => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];

  if (token) {
    jwt.verify(token, JWT_SECRET, (err, user) => {
      if (!err) {
        req.user = user;
      }
    });
  }
  next();
};

// Project routes
app.get('/api/projects', projectLimiter, optionalAuth, async (req, res) => {
  try {
    // If user is authenticated, return their projects
    if (req.user && req.user.id) {
      const projects = await db.getProjectsByUserId(req.user.id);
      res.json({ projects });
    } else {
      // If not authenticated, return empty array
      res.json({ projects: [] });
    }
  } catch (error) {
    console.error('Get projects error:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

/**
 * @swagger
 * /api/projects:
 *   post:
 *     summary: 프로젝트 생성
 *     description: 새 프로젝트를 생성합니다
 *     tags: [Projects]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - name
 *             properties:
 *               name:
 *                 type: string
 *                 example: 여름 세일 캠페인
 *               data:
 *                 type: object
 *                 properties:
 *                   canvas:
 *                     type: object
 *                   settings:
 *                     type: object
 *     responses:
 *       201:
 *         description: 프로젝트 생성 성공
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 message:
 *                   type: string
 *                 project:
 *                   type: object
 *       400:
 *         description: 프로젝트명 누락
 *       401:
 *         description: 인증 필요
 */
app.post('/api/projects', projectLimiter, authenticateToken, async (req, res) => {
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

app.get('/api/projects/:id', projectLimiter, authenticateToken, async (req, res) => {
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

app.put('/api/projects/:id', projectLimiter, authenticateToken, async (req, res) => {
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

app.delete('/api/projects/:id', projectLimiter, authenticateToken, async (req, res) => {
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