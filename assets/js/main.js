//window.Vue = require('vue');

import Vue from 'vue'
import helloWorld from './components/hello-world.vue'
import myApp from './components/my-grid/my-grid.vue'
//import DemoGrid from './grid_base.vue'

// ロードするこのJSがバインドさせるHTMLよりしたならこのaddEventは不要みたい
document.addEventListener('DOMContentLoaded',function() {
    var cont2 = new Vue(helloWorld).$mount('#hello-world');
    var cont = new Vue(myApp).$mount('#demo');
});

/*
var demo = new Vue({
    el: '#demo',
    render: h => h(myApp)
});
*/
