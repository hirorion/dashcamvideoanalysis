// register the grid component
Vue.component('demo-grid', {
    template: '#grid-template',
    props: {
        items: Array,
        columns: Array,
        filterKey: String
    },
    data: function () {
        var sortOrders = {};
        this.columns.forEach(function (key) {
            sortOrders[key] = 1
        })
        return {
            sortKey: '',
            sortOrders: sortOrders
        }
    },
    computed: {
        filteredItems: function () {
            var sortKey = this.sortKey;
            var filterKey = this.filterKey && this.filterKey.toLowerCase();
            var order = this.sortOrders[sortKey] || 1;
            var items = this.items;
            if (filterKey) {
                items = items.filter(function (row) {
                    return Object.keys(row).some(function (key) {
                        return String(row[key]).toLowerCase().indexOf(filterKey) > -1
                    })
                })
            }
            if (sortKey) {
                items = items.slice().sort(function (a, b) {
                    a = a[sortKey];
                    b = b[sortKey];
                    return (a === b ? 0 : a > b ? 1 : -1) * order
                })
            }
            return items
        }
    },
    filters: {
        capitalize: function (str) {
            return str.charAt(0).toUpperCase() + str.slice(1)
        }
    },
    methods: {
        sortBy: function (key) {
            this.sortKey = key;
            this.sortOrders[key] = this.sortOrders[key] * -1
        }
    }
})

//上部のコンポーネント実装部分はコピペなので割愛
//new Vue部分だけRestAPIから指定のデータを取得するように改造
var demo = new Vue({
    el: '#demo',
    data: {
        searchQuery: '',
        gridColumns: ["id", "title", 'stock_count'], // 変更
        gridData: [] // データはAPIで取ってくるので削除
    },
    created: function () { //RestAPIから取ってきてgridDataに追加する。
        var self = this; //スコープ的に必要っぽい（this.gridData.pushではエラーになる。）
        axios.get('/stocks_app/api/stock/')
            .then(function (response) {
                for (var i = 0; i < response.data.results.length; i++) {
                    self.gridData.push(response.data.results[i]);
                }
            });
    }
})
