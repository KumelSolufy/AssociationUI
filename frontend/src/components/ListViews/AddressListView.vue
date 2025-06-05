<template>
    <ListView
      :class="$attrs.class"
      :columns="columns"
      :rows="rows"
      :options="{
        selectable: options.selectable,
        showTooltip: options.showTooltip,
        resizeColumn: options.resizeColumn,
      }"
      row-key="name"
      @update:selections="(selections) => emit('selectionsChanged', selections)"
    >
      <ListHeader class="sm:mx-5 mx-3">
        <ListHeaderItem
          v-for="column in columns"
          :key="column.key"
          :item="column"
        />
      </ListHeader>
  
      <ListRows :rows="rows" v-slot="{ column, item }" doctype="Address">
        <ListRowItem :item="item" :align="column.align">
          <template #default="{ label }">
            <div class="truncate text-base">
              {{ label }}
            </div>
          </template>
        </ListRowItem>
      </ListRows>
  
      <ListSelectBanner>
        <template #actions="{ selections, unselectAll }">
          <!-- Add address-specific bulk actions if any -->
        </template>
      </ListSelectBanner>
    </ListView>
  </template>
  
  <script setup>
  import {
    ListView,
    ListHeader,
    ListHeaderItem,
    ListRowItem,
    ListSelectBanner,
  } from 'frappe-ui'
  import ListRows from '@/components/ListViews/ListRows.vue'
  
  const props = defineProps({
    rows: {
      type: Array,
      required: true,
    },
    columns: {
      type: Array,
      required: true,
    },
    options: {
      type: Object,
      default: () => ({
        selectable: false,
        showTooltip: false,
        resizeColumn: false,
      }),
    },
  })
  
  const emit = defineEmits(['selectionsChanged'])
  </script>
  