const { Pool } = require('pg');

// PostgreSQL connection pool
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
});

// Test connection
pool.on('connect', () => {
  console.log('✅ Connected to PostgreSQL database');
});

pool.on('error', (err) => {
  console.error('❌ Unexpected PostgreSQL error:', err);
});

// Initialize database tables
async function initDatabase() {
  const client = await pool.connect();

  try {
    console.log('Initializing database tables...');

    // Create users table
    await client.query(`
      CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(255) UNIQUE NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Create projects table
    await client.query(`
      CREATE TABLE IF NOT EXISTS projects (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        name VARCHAR(255) NOT NULL,
        data JSONB DEFAULT '{}',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Create index on user_id for faster queries
    await client.query(`
      CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id)
    `);

    console.log('✅ Database tables initialized');
  } catch (error) {
    console.error('❌ Error initializing database:', error);
    throw error;
  } finally {
    client.release();
  }
}

// User operations
const db = {
  // Create user
  async createUser(username, email, password) {
    const result = await pool.query(
      'INSERT INTO users (username, email, password) VALUES ($1, $2, $3) RETURNING id, username, email, created_at',
      [username, email, password]
    );
    return result.rows[0];
  },

  // Get user by email
  async getUserByEmail(email) {
    const result = await pool.query(
      'SELECT * FROM users WHERE email = $1',
      [email]
    );
    return result.rows[0];
  },

  // Get user by username
  async getUserByUsername(username) {
    const result = await pool.query(
      'SELECT * FROM users WHERE username = $1',
      [username]
    );
    return result.rows[0];
  },

  // Get user by ID
  async getUserById(id) {
    const result = await pool.query(
      'SELECT id, username, email, created_at FROM users WHERE id = $1',
      [id]
    );
    return result.rows[0];
  },

  // Create project
  async createProject(userId, name, data) {
    const result = await pool.query(
      'INSERT INTO projects (user_id, name, data) VALUES ($1, $2, $3) RETURNING id, user_id, name, data, created_at, updated_at',
      [userId, name, JSON.stringify(data)]
    );
    return result.rows[0];
  },

  // Get projects by user ID
  async getProjectsByUserId(userId) {
    const result = await pool.query(
      'SELECT id, user_id, name, created_at, updated_at FROM projects WHERE user_id = $1 ORDER BY updated_at DESC',
      [userId]
    );
    return result.rows;
  },

  // Get project by ID
  async getProjectById(id) {
    const result = await pool.query(
      'SELECT * FROM projects WHERE id = $1',
      [id]
    );
    return result.rows[0];
  },

  // Update project
  async updateProject(id, data) {
    const result = await pool.query(
      'UPDATE projects SET data = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2 RETURNING id, user_id, name, data, created_at, updated_at',
      [JSON.stringify(data), id]
    );
    return result.rows[0];
  },

  // Update project name
  async updateProjectName(id, name) {
    const result = await pool.query(
      'UPDATE projects SET name = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2 RETURNING id, user_id, name, data, created_at, updated_at',
      [name, id]
    );
    return result.rows[0];
  },

  // Delete project
  async deleteProject(id) {
    const result = await pool.query(
      'DELETE FROM projects WHERE id = $1 RETURNING id',
      [id]
    );
    return result.rows.length > 0;
  },

  // Get database stats
  async getStats() {
    const usersCount = await pool.query('SELECT COUNT(*) FROM users');
    const projectsCount = await pool.query('SELECT COUNT(*) FROM projects');

    return {
      users: parseInt(usersCount.rows[0].count),
      projects: parseInt(projectsCount.rows[0].count)
    };
  }
};

module.exports = { pool, initDatabase, db };
