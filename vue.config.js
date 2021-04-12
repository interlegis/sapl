const each = require("lodash/fp/each");
const path = require("path");
const shell = require('shelljs');

const MomentLocalesPlugin = require("moment-locales-webpack-plugin");
const BundleTrackerPlugin = require("webpack-bundle-tracker");
const CompressionPlugin = require("compression-webpack-plugin");
const CopyPlugin = require("copy-webpack-plugin");

class RelativeBundleTrackerPlugin extends BundleTrackerPlugin {
  convertPathChunks(chunks) {
    each(
      each((chunk) => {
        chunk.path = path.relative(this.options.path, chunk.path);
      })
    )(chunks);
  }

  writeOutput(compiler, contents) {
    if (contents.status === "done") {
      this.convertPathChunks(contents.chunks);
    }
    super.writeOutput(compiler, contents);
  }
}

const dotenv = require("dotenv");
dotenv.config({
  path: "./sapl/.env",
});

var HOST_NAME = "localhost";

module.exports = {
  runtimeCompiler: true,
  publicPath:
    process.env.NODE_ENV === "production"
      ? "/static/sapl/frontend"
      : `http://${HOST_NAME}:8080/`,
  outputDir: "./sapl/static/sapl/frontend",

  chainWebpack: (config) => {
    config.plugins.delete("html");
    config.plugins.delete("preload");
    config.plugins.delete("prefetch");

    config.resolve.alias.set("@", path.join(__dirname + "/frontend/", "src"));

    config.plugin("copy").use(CopyPlugin, [
      [
        {
          from: path.join(__dirname + "/frontend/", "public"),
          to: ".",
        },

        {
          from:  path.join(__dirname, "/node_modules/tinymce/skins"),
          to: "js/skins/[path][name].[ext]",
        },
      ],
    ]);

    config
      .plugin("RelativeBundleTrackerPlugin")
      .use(RelativeBundleTrackerPlugin, [
        {
          path: ".",
          filename: `./frontend/${
            process.env.DEBUG === "True" &&
            process.env.NODE_ENV !== "production"
              ? "dev-"
              : ""
          }webpack-stats.json`,
        },
      ]);

    config.plugin("MomentLocalesPlugin").use(MomentLocalesPlugin, [
      {
        localesToKeep: ["pt-BR"],
      },
    ]);

    config.resolve.alias.set("__STATIC__", "static");

    config.devServer
      .public("")
      .port(8080)
      .hot(true)
      .watchOptions({
        poll: true,
      })
      .watchContentBase(true)
      .https(false)
      .headers({
        "Access-Control-Allow-Origin": "*",
      })
      .contentBase([
        path.join(__dirname + "/frontend/", "public"),
        path.join(__dirname + "/frontend/", "src", "assets"),
      ]);

    config.plugin("provide").use(require("webpack/lib/ProvidePlugin"), [
      {
        $: "jquery",
        jquery: "jquery",
        "window.jQuery": "jquery",
        jQuery: "jquery",
        _: "lodash",
      },
    ]);

    if (process.env.NODE_ENV === "production") {
      config.optimization.minimizer("terser").tap((args) => {
        args[0].terserOptions.compress.drop_console = true;
        args[0].extractComments = true;
        args[0].cache = true;
        return args;
      });

      config.plugin("CompressionPlugin").use(CompressionPlugin, [{}]);

      shell.rm('frontend/dev-webpack-stats.json')

    } else {
      config.devtool("source-map");
    }

    config.entryPoints.delete("app");

    config
      .entry("global")
      .add("./frontend/src/__global/main.js")
      .end();

    config
      .entry("compilacao")
      .add("./frontend/src/__apps/compilacao/main.js")
      .end();

    config
      .entry("painel")
      .add("./frontend/src/__apps/painel/main.js")
      .end();

    config
      .entry("parlamentar")
      .add("./frontend/src/__apps/parlamentar/main.js")
      .end();
  },
};
