var path = require("path");
var webpack = require('webpack');
var BundleTracker = require('webpack-bundle-tracker');
var VueLoaderPlugin = require('vue-loader/lib/plugin');

var env = process.env.NODE_ENV;

module.exports = {
    context: __dirname,

    mode: env,

    entry: './assets/js/main.js', // これがエントリーポイント

    devtool: 'source-map',

    output: { // コンパイルされたファイルの設定
        path: path.resolve('./assets/bundles/'),
        filename: "[name]-[hash].js", // キャッシュ対策f
    },

    module: {
        rules: [
            {
                test: /\.js$/,
                loader: 'babel-loader',
            },
            {
                test: /\.vue$/,
                loader: 'vue-loader'
            },
            {
                test: /\.scss$/,
                use: [
                    'style-loader',
                    'css-loader',
                    'sass-loader'
                ]
            },
            {
                test: /\.css$/,
                use: [
                    "vue-style-loader",
                    'style-loader',
                    {
                        loader: 'css-loader',
                        options: {
                            url: false,
                            sourceMap: true
                        }
                    }
                ]
            },
        ]
    },

    plugins: [
        new BundleTracker({filename: './webpack-stats.json'}),
        // .vueファイルを読み込めるようにする
        new VueLoaderPlugin()
    ],

    resolve: {
        extensions: ['.js', '.vue'],
        modules: [
            "node_modules"
        ],
        alias: {
            // 完全には理解できてないですが、
            // 下記エイリアス設定しないとvue走りません
            'vue$': 'vue/dist/vue.js',
        }
    }

}
