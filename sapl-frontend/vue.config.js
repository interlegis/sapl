const webpack = require('webpack')
const path = require('path')

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
      .hot(true)
      .watchOptions({ poll: true })
      .watchContentBase( true )
      .https(false)
      .headers({ 'Access-Control-Allow-Origin': '\*' })
      .contentBase( [path.join(__dirname, 'public'), path.join(__dirname, 'src', 'assets')] )


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
