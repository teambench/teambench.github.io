'use strict';

const { Sequelize, DataTypes } = require('sequelize');
const md5 = require('md5');

// SQLite in-memory for tests, file-based for production
const sequelize = new Sequelize({
  dialect: 'sqlite',
  storage: process.env.DB_PATH || ':memory:',
  logging: false,
});

const User = sequelize.define('User', {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true,
  },
  username: {
    type: DataTypes.STRING,
    allowNull: false,
    unique: true,
    validate: { len: [3, 32] },
  },
  email: {
    type: DataTypes.STRING,
    allowNull: false,
    unique: true,
    validate: { isEmail: true },
  },
  // VULNERABILITY: column stores MD5 hashes instead of bcrypt
  password_hash: {
    type: DataTypes.STRING,
    allowNull: false,
  },
  isAdmin: {
    type: DataTypes.BOOLEAN,
    defaultValue: false,
  },
  role: {
    type: DataTypes.STRING,
    defaultValue: 'user',
  },
}, {
  tableName: 'users',
  underscored: false,
});

// VULNERABILITY: using MD5 to hash passwords on create
// Fix: replace with bcrypt (salt rounds = 12)
User.beforeCreate(async (user) => {
  if (user.password_hash && !user.password_hash.startsWith('$2')) {
    user.password_hash = md5(user.password_hash);
  }
});

// Sync helper used by tests
User.sync = User.sync.bind(User);

module.exports = { User, sequelize };
