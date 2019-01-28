const path = require('path')
const each = require('lodash/fp/each')

/* var SplitByPathPlugin = require('webpack-split-by-path');
new SplitByPathPlugin([
  {
    name: 'vendor',
    path: path.join(__dirname, './node_modules/')
  }
]) */

const BundleTrackerPlugin = require('webpack-bundle-tracker')
class RelativeBundleTrackerPlugin extends BundleTrackerPlugin {
  convertPathChunks(chunks){
    each(each(chunk => {
      chunk.path = path.relative(this.options.path, chunk.path)
    }))(chunks)
  }
  writeOutput(compiler, contents) {
    if (contents.status === 'done')  {
      this.convertPathChunks(contents.chunks)
    }
    super.writeOutput(compiler, contents)
  }
}
// module.exports = RelativeBundleTrackerPlugin

const dotenv = require('dotenv')
dotenv.config({ path: '../sapl/.env' })

var THEME_CUSTOM = process.env.THEME_CUSTOM === undefined ? 'sapl-oficial-theme' : process.env.THEME_CUSTOM

module.exports = {
  publicPath: process.env.NODE_ENV === 'production' ? '/static/' : 'http://localhost:8080/',
  outputDir: '../sapl/static/',

  chainWebpack: config => {

    config.plugins.delete('html')
    config.plugins.delete('preload')
    config.plugins.delete('prefetch')



    config
      .mode('development')
      .devtool('cheap-module-eval-source-map')

    config
      .mode('development')
      .optimization	   
      .splitChunks(false)


    config
      .plugin('RelativeBundleTrackerPlugin')
      .use(RelativeBundleTrackerPlugin, [{ 
        path:'.',
        filename: '../webpack-stats.json' 
      }])

    config.resolve.alias
      .set('__STATIC__', 'static')

    config.devServer
      .public('')
      .host('localhost')
      .port(8080)
      .hot(true)
      .watchOptions({ poll: true })
      .watchContentBase(true)
      .https(false)
      .headers({ 'Access-Control-Allow-Origin': '*' })
      .contentBase([
        //path.join(__dirname, 'public'),
        path.join(__dirname, 'src', 'assets')
        // path.join(__dirname, 'node_modules', THEME_CUSTOM, 'public'),
        // path.join(__dirname, 'node_modules', THEME_CUSTOM, 'src', 'assets')
      ])

    config
      .plugin('copy')
      .tap(([options]) => {
        options.push(
          {
            from: path.join(__dirname, 'node_modules', THEME_CUSTOM, 'public'),
            to: path.join(__dirname, '..', 'sapl', 'static'),
            toType: 'dir',
            ignore: [
              '.DS_Store'
            ]
          })
        return [options]
      })

    config
      .plugin('provide')
      .use(require('webpack/lib/ProvidePlugin'), [{
        $: 'jquery',
        jquery: 'jquery',
        'window.jQuery': 'jquery',
        jQuery: 'jquery',
        _: 'lodash'
      }])

    config.entryPoints.delete('app')

    config
      .entry(THEME_CUSTOM)
      // .add('./src/theme-dev/main.js')
      .add(THEME_CUSTOM + '/src/main.js')
      .end()

    config
      .entry('global')
      .add('./src/global/main.js')
      .end()

    config.entry('compilacao')
      .add('./src/apps/compilacao/main.js')
      .end()

    /* config
    .plugin('theme')
    .use(webpack.DefinePlugin, [{
      THEME_CUSTOM: JSON.stringify(THEME_CUSTOM)
    }])
    .end() */
  }
}
