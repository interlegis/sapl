const webpack = require('webpack')
const path = require('path')

const BundleTracker = require('webpack-bundle-tracker')
const dotenv = require('dotenv')
dotenv.config({ path: '../sapl/.env' })

var THEME_CUSTOM = process.env.THEME_CUSTOM === undefined ? "sapl-oficial-theme" : process.env.THEME_CUSTOM

module.exports = {
  publicPath: 'http://localhost:8080/',
  outputDir: './dist/',

  chainWebpack: config => {

    config.optimization
      .splitChunks(false)

    config
      .plugin('BundleTracker')
      .use(BundleTracker, [{ filename: './webpack-stats.json' }])

    config.resolve.alias
      .set('__STATIC__', 'static')

    config.devServer
      .public('')
      .host('localhost')
      .port(8080)
      .hot(true)
      .watchOptions({ poll: true })
      .watchContentBase( true )
      .https(false)
      .headers({ 'Access-Control-Allow-Origin': '\*' })
      .contentBase( [
        path.join(__dirname, 'public'), 
        path.join(__dirname, 'src', 'assets'),
        path.join(__dirname, 'node_modules', THEME_CUSTOM, 'public'), 
      ] )

    config.entryPoints.delete('app')

    config.entry(THEME_CUSTOM)
      .add('./src/theme-dev/main.js')
      //.add(THEME_CUSTOM + '/src/main.js')
      .end()
    
    config.entry('global')
      .add('./src/global/main.js')
      .end()

    config.entry('compilacao')
      .add('./src/apps/compilacao/main.js')
      .end()

    /*config
      .plugin('theme')
      .use(webpack.DefinePlugin, [{
        THEME_CUSTOM: JSON.stringify(THEME_CUSTOM)
      }])
      .end()*/
      
      
  }
}
