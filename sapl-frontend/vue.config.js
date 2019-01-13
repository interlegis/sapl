const webpack = require('webpack')

const BundleTracker = require('webpack-bundle-tracker')
const dotenv = require('dotenv')
dotenv.config({ path: '../sapl/.env' })

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
      .hotOnly(true)
      .watchOptions({ poll: 1000 })
      .https(false)
      .headers({ 'Access-Control-Allow-Origin': '\*' })

    config.entryPoints.delete('app')
    
      // then add your own
    config.entry('hellow')
      .add('./src/hellow/main.js')
      .end()
      
    config.entry('theme')
      .add('./src/theme/main.js')
      .end()
      
    config
      .plugin('theme')
      .use(webpack.DefinePlugin, [{
        THEME_CUSTOM: JSON.stringify(process.env.THEME_CUSTOM)
      }])
      .end()
  }
}
