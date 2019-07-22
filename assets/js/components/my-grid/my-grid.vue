<template>
<div>
    <form id="search">
        Search <input name="query" v-model="searchQuery">  <!-- v-modelはinputのsearchQueryをバインド -->
    </form>
    <my-grid
            :items="gridData"
            :columns="gridColumns"
            :filter-key="searchQuery">
    </my-grid>
</div>
</template>

<script>
    // Ajax通信ライブラリ
    import axios from 'axios/index';
    import Grid from './grid_base.vue';
    export default {
        //el: '#demo',
        data: {
            searchQuery: '',
            gridColumns: ["id", "title", 'stock_count'], // 変更
            gridData: [] // データはAPIで取ってくるので削除
        },
        created: function () { //RestAPIから取ってきてgridDataに追加する。
            var self = this; //スコープ的に必要っぽい（this.gridData.pushではエラーになる。）
            axios.get('/api/stock/')
                .then(function (response) {
                    for (var i = 0; i < response.data.results.length; i++) {
                        self.gridData.push(response.data.results[i]);
                    }
                });
        },
        components: {"my-grid": Grid},
    }

</script>

<style scoped>

</style>
