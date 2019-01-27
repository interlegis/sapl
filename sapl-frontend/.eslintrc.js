module.exports = {
  root: true,
  env: {
    browser: true,
    node: true,
    jquery: true
  },
  extends: [
    'plugin:vue/essential',
    'standard'
  ],
  rules: {
    'generator-star-spacing': 'off',
    'no-console': process.env.NODE_ENV === 'production' ? 'error' : 'off',
    'no-debugger': process.env.NODE_ENV === 'production' ? 'error' : 'off',
    camelcase: 0
  },
  // required to lint *.vue files
  plugins: [
    'vue'
  ],
  parserOptions: {
    parser: 'babel-eslint'
  },

  globals: {
    '$': true,
    'jQuery': true,
    '_': true
  }
}
