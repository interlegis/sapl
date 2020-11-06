const path = require('path')
const each = require('lodash/fp/each')

const MomentLocalesPlugin = require('moment-locales-webpack-plugin')
const BundleTrackerPlugin = require('webpack-bundle-tracker')
const CompressionPlugin = require('compression-webpack-plugin')
const CopyPlugin = require('copy-webpack-plugin')

class RelativeBundleTrackerPlugin extends BundleTrackerPlugin {
  convertPathChunks (chunks) {
    each(each(chunk => {
      chunk.path = path.relative(this.options.path, chunk.path)
    }))(chunks)
  }

  writeOutput (compiler, contents) {
    if (contents.status === 'done') {
      this.convertPathChunks(contents.chunks)
    }
    super.writeOutput(compiler, contents)
  }
}

const dotenv = require('dotenv')
dotenv.config({
  path: './sapl/.env'
})

var FRONTEND_CUSTOM = process.env.FRONTEND_CUSTOM === undefined ? false : process.env.FRONTEND_CUSTOM === 'True'

var HOST_NAME = 'localhost'

module.exports = {
  runtimeCompiler: true,
  publicPath: process.env.NODE_ENV === 'production' ? '/static/sapl/frontend' : `http://${HOST_NAME}:8080/`,
  outputDir: FRONTEND_CUSTOM ? 'dist' : './sapl/static/sapl/frontend',

  chainWebpack: config => {
    config.plugins.delete('html')
    config.plugins.delete('preload')
    config.plugins.delete('prefetch')

    config.resolve
      .alias.set('@', path.join(__dirname + "/frontend/", 'src'))

    config
      .plugin('CopyPlugin')
      .use(CopyPlugin, [{
        patterns: [
          {
            from: path.join(__dirname + "/frontend/", 'public'),
            to: '.'
          },
        ],
      }])

    config
      .plugin('RelativeBundleTrackerPlugin')
      .use(RelativeBundleTrackerPlugin, [{
        path: '.',
        filename: FRONTEND_CUSTOM ? './webpack-stats.json' : './sapl/webpack-stats.json'
      }])

    config
      .plugin('MomentLocalesPlugin')
      .use(MomentLocalesPlugin, [{
        localesToKeep: ['pt-BR']
      }])

    if (process.env.NODE_ENV === 'production') {
      config.optimization.minimizer('terser').tap((args) => {
        args[0].terserOptions.compress.drop_console = true
        args[0].extractComments = true
        args[0].cache = true
        return args
      })

      config
        .plugin('CompressionPlugin')
        .use(CompressionPlugin, [{
        }])
    } else {
      config
        .devtool('source-map')
    }

    config.resolve.alias
      .set('__STATIC__', 'static')

    config.module
      .rule('vue')
      .use('vue-loader')
      .loader('vue-loader')
      .tap(options => {
        options.transformAssetUrls = {
          img: 'src',
          image: 'xlink:href',
          'b-img': 'src',
          'b-img-lazy': ['src', 'blank-src'],
          'b-card': 'img-src',
          'b-card-img': 'img-src',
          'b-carousel-slide': 'img-src',
          'b-embed': 'src'
        }

        return options
      })

    config.devServer
      .public('')
      .port(8080)
      .hot(true)
      .watchOptions({
        poll: true
      })
      .watchContentBase(true)
      .https(false)
      .headers({
        'Access-Control-Allow-Origin': '*'
      })
      .contentBase([
        path.join(__dirname + "/frontend/", 'public'),
        path.join(__dirname + "/frontend/", 'src', 'assets')
      ])

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
      .entry('global')
      .add('./frontend/src/__global/main.js')
      .end()

    config.entry('compilacao')
      .add('./frontend/src/__apps/compilacao/main.js')
      .end()

    config.entry('painel')
      .add('./frontend/src/__apps/painel/main.js')
      .end()

    config.entry('parlamentar')
      .add('./frontend/src/__apps/parlamentar/main.js')
      .end()
  }
}
