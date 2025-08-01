// Welcome to the theme Gulp file
// more info on Gulp: http://gulpjs.com/
//
// Getting started
// Gulp requires NPM so you'll need to install NPM first if not already installed
// NPM install intro: http://blog.npmjs.org/post/85484771375/how-to-install-npm
//
// Installing Gulp: https://github.com/gulpjs/gulp/blob/master/docs/getting-started.md
// 
// 
// Once you have gulp and npm installed you can run this to get all dependencies:
// npm install 
// 
// Rest of commands are documented below:


'use strict';
 
const gulp = require("gulp");
const sass = require('gulp-sass')(require('sass'));
const postcss = require("gulp-postcss");
const autoprefixer = require("autoprefixer");
const cssnano = require("cssnano");
const sourcemaps = require("gulp-sourcemaps");
const babel = require('gulp-babel');
const minify = require("gulp-babel-minify");
const rename = require("gulp-rename");

const paths = {
  styles: {
    src: './sass/**/*.scss',
    dest: '../static/healthscore/css'
  },
  scripts: {
    src: './js/*.js',
    dest: '../static/healthscore/js'
  }
};

// Compile Sass files
function styles() {
  return gulp.src(paths.styles.src)
    .pipe(sourcemaps.init())
    .pipe(sass({
      outputStyle: 'compressed'
      }).on('error', sass.logError))
    .pipe(postcss([autoprefixer({ cascade: false }), cssnano()]))
    .pipe(sourcemaps.write('.')) 
    .pipe(gulp.dest(paths.styles.dest))
    ;
};

// Compile Javascript files
function scripts() {
  return gulp.src(paths.scripts.src)
    .pipe(babel({
      presets: ['@babel/env']
    }))
    .pipe(minify({
      'builtIns': false
    }))
    .pipe(rename({ suffix: '.min' }))
    .pipe(gulp.dest(paths.scripts.dest))
    ;
}

function watch() {
  gulp.watch(paths.styles.src, styles);
  gulp.watch(paths.scripts.src, scripts);
}

exports.styles = styles;
exports.scripts = scripts;
exports.watch = watch;

gulp.task('styles', styles);
gulp.task('scripts', scripts);
