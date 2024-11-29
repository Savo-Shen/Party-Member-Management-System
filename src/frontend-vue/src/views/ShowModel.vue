<script setup>

import { ref } from 'vue'

// import { ModelStl } from 'vue-3d-model';

const params  = new URLSearchParams(location.search);
const model   = ref(params.get('model'));
const patientName = ref(params.get('patientName'));

</script>

<template>
<div></div>

<div id='main'>
    <div class="title">超酷口腔管理平台模型查看器</div>
    <div class="model">
        <div class="model-information">患者：{{ patientName }}</div>
        <model-stl :src="model"></model-stl>
    </div>
    
</div>

</template>

<style scoped>

</style>