const HOST_NAME = 'localhost'
const dotenv = require('dotenv')

const path = require('path')
const fs = require('fs')

const BundleTrackerPlugin = require('webpack-bundle-tracker')
const CompressionPlugin = require('compression-webpack-plugin')
const CopyPlugin = require('copy-webpack-plugin')
const MomentLocalesPlugin = require('moment-locales-webpack-plugin')
const TerserPlugin = require('terser-webpack-plugin')

dotenv.config({
  path: './sapl/.env'
})

module.exports = {
  runtimeCompiler: true,
  publicPath:
    process.env.NODE_ENV === 'production'
      ? '/static/sapl/frontend'
      : `http://${HOST_NAME}:8080/`,
  outputDir: './sapl/static/sapl/frontend',

  productionSourceMap: false,
  css: {
    sourceMap: true
  },
  devServer: {
    port: '8080',
    hot: true,
    https: false,
    headers: {
      'Access-Control-Allow-Origin': '*'
    },
    static: {
      directory: path.join(__dirname, 'frontend', 'src', 'assets'),
      publicPath: ''
      // path.join(__dirname + '/frontend/', 'src', 'assets'),
    }
  },

  chainWebpack: (config) => {
    config.plugins.delete('html')
    config.plugins.delete('preload')
    config.plugins.delete('prefetch')

    config.resolve.alias.set('@', path.join(__dirname, 'frontend', 'src'))
    config.resolve.alias.set('__STATIC__', 'static')

    config
      .plugin('BundleTrackerPlugin')
      .use(BundleTrackerPlugin, [
        {
          path: '.',
          filename: `./frontend/${
            process.env.DEBUG === 'True' &&
            process.env.NODE_ENV !== 'production'
              ? 'dev-'
              : ''
          }webpack-stats.json`
        }
      ])

    config.plugin('provide').use(require('webpack').ProvidePlugin, [
      {
        $: 'jquery',
        jquery: 'jquery',
        'window.jQuery': 'jquery',
        jQuery: 'jquery',
        _: 'lodash'
      }
    ])

    config.plugin('MomentLocalesPlugin').use(MomentLocalesPlugin, [
      {
        localesToKeep: ['pt-BR']
      }
    ])

    config.plugin('copy').use(CopyPlugin, [
      {
        patterns: [
          {
            from: path.join(__dirname, 'frontend', 'src', 'assets'),
            to: '.'
          },
          {
            from: path.join(__dirname, 'node_modules/tinymce/skins'),
            to: 'js/skins/[path][name][ext]'
          }
        ]
      }
    ])

    if (process.env.NODE_ENV === 'production') {
      fs.unlink('frontend/dev-webpack-stats.json', function (err) {
        if (err && err.code !== 'ENOENT') {
          console.error('Error occurred while trying to remove file')
        }
      })

      config
        .plugin('CompressionPlugin')
        .use(CompressionPlugin, [{}])

      config
        .optimization
        .minimizer('terser')
        .use(TerserPlugin, [{
          extractComments: true,
          minify: TerserPlugin.uglifyJsMinify
        }])
    }

    config.entryPoints.delete('app')

    config
      .entry('global')
      .add('./frontend/src/__global/main.js')
      .end()

    config
      .entry('parlamentar')
      .add('./frontend/src/__apps/parlamentar/main.js')
      .end()

    config
      .entry('painel')
      .add('./frontend/src/__apps/painel/main.js')
      .end()

    config
      .entry('compilacao')
      .add('./frontend/src/__apps/compilacao/main.js')
      .end()
  }
}
