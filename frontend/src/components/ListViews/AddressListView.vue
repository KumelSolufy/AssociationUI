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
      <ListHeader
        class="mx-3 sm:mx-5"
        @columnWidthUpdated="emit('columnWidthUpdated')"
      >
        <ListHeaderItem
          v-for="column in columns"
          :key="column.key"
          :item="column"
          @columnWidthUpdated="emit('columnWidthUpdated', column)"
        >
          <Button
            v-if="column.key == '_liked_by'"
            variant="ghosted"
            class="!h-4"
            :class="isLikeFilterApplied ? 'fill-red-500' : 'fill-white'"
            @click="() => emit('applyLikeFilter')"
          >
            <HeartIcon class="h-4 w-4" />
          </Button>
        </ListHeaderItem>
      </ListHeader>
  
      <ListRows
        class="mx-3 sm:mx-5"
        :rows="rows"
        v-slot="{ idx, column, item }"
        doctype="Address"
      >
        <ListRowItem :item="item" :align="column.align">
          <template #prefix>
            <div v-if="column.key === 'address_type'">
              <MapPinIcon class="h-4 w-4" />
            </div>
            <div v-else-if="column.key === 'phone'">
              <PhoneIcon class="h-4 w-4" />
            </div>
            <div v-else-if="column.key === 'email_id'">
              <MailIcon class="h-4 w-4" />
            </div>
          </template>
          <template #default="{ label }">
            <div
              v-if="['modified', 'creation'].includes(column.key)"
              class="truncate text-base"
              @click="
                (event) =>
                  emit('applyFilter', {
                    event,
                    idx,
                    column,
                    item,
                    firstColumn: columns[0],
                  })
              "
            >
              <Tooltip :text="item.label">
                <div>{{ item.timeAgo }}</div>
              </Tooltip>
            </div>
            <div v-else-if="column.type === 'Check'">
              <FormControl
                type="checkbox"
                :modelValue="item"
                :disabled="true"
                class="text-ink-gray-9"
              />
            </div>
            <div
              v-else
              class="truncate text-base"
              @click="
                (event) =>
                  emit('applyFilter', {
                    event,
                    idx,
                    column,
                    item,
                    firstColumn: columns[0],
                  })
              "
            >
              {{ label }}
            </div>
          </template>
        </ListRowItem>
      </ListRows>
  
      <ListSelectBanner>
        <template #actions="{ selections, unselectAll }">
          <Dropdown
            :options="listBulkActionsRef.bulkActions(selections, unselectAll)"
          >
            <Button icon="more-horizontal" variant="ghost" />
          </Dropdown>
        </template>
      </ListSelectBanner>
    </ListView>
    <ListFooter
      v-if="pageLengthCount"
      class="border-t px-3 py-2 sm:px-5"
      v-model="pageLengthCount"
      :options="{
        rowCount: options.rowCount,
        totalCount: options.totalCount,
      }"
      @loadMore="emit('loadMore')"
    />
    <ListBulkActions
      ref="listBulkActionsRef"
      v-model="list"
      doctype="Address"
      :options="{
        hideAssign: true,
      }"
    />
  </template>
  
  <script setup>
  import {
    ListView,
    ListHeader,
    ListHeaderItem,
    ListRowItem,
    ListSelectBanner,
    Button,
    FormControl,
    Tooltip,
    Dropdown,
    ListFooter,
  } from 'frappe-ui'
  import ListRows from '@/components/ListViews/ListRows.vue'
  import HeartIcon from '@/components/Icons/HeartIcon.vue'
  import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
  import MailIcon from '@/components/Icons/MailIcon.vue'
  import MapPinIcon from '@/components/Icons/MapPinIcon.vue'
  import ListBulkActions from '@/components/ListBulkActions.vue'
  import { sessionStore } from '@/stores/session'
  import { ref, computed, watch } from 'vue'
  
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
        selectable: true,
        showTooltip: true,
        resizeColumn: false,
        totalCount: 0,
        rowCount: 0,
      }),
    },
  })
  
  const emit = defineEmits([
    'loadMore',
    'updatePageCount',
    'columnWidthUpdated',
    'applyFilter',
    'applyLikeFilter',
    'likeDoc',
    'selectionsChanged',
  ])
  
  const pageLengthCount = defineModel()
  const list = defineModel('list')
  
  const isLikeFilterApplied = computed(() => {
    return list.value.params?.filters?._liked_by ? true : false
  })
  
  const { user } = sessionStore()
  
  function isLiked(item) {
    if (item) {
      let likedByMe = JSON.parse(item)
      return likedByMe.includes(user)
    }
  }
  
  watch(pageLengthCount, (val, old_value) => {
    if (val === old_value) return
    emit('updatePageCount', val)
  })
  
  const listBulkActionsRef = ref(null)
  
  defineExpose({
    customListActions: computed(
      () => listBulkActionsRef.value?.customListActions,
    ),
  })
  </script>
  