<template>
    <div class="message">
        {{ message }}<br>

        computed test: {{ `${year}-${month}` }}
    </div>
</template>

<script>
    export default {
        //name: "helloworld",  // vueファイルの場合は自動でファイル名がname属性になるので不要
        data: function () {
            return {
                message: 'hello world'
            };
        },
        computed: {
            month() {
                return this.twoDigits((new Date()).getUTCMonth() + 1);
            },
            year() {
                return (new Date()).getUTCFullYear();
            }
        },
        methods: {
            twoDigits(num) {
                return ('0' + num).slice(-2);
            }
        },
    }
</script>

<style scoped>
    .message {
        color: red;
    }
</style>
