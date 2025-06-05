<template>
  <LayoutHeader v-if="contact.data">
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs">
        <template #prefix="{ item }">
          <Icon v-if="item.icon" :icon="item.icon" class="mr-2 h-4" />
        </template>
      </Breadcrumbs>
    </template>
  </LayoutHeader>
  <div v-if="contact.data" ref="parentRef" class="flex h-full">
    <Resizer
      v-if="contact.data"
      :parent="$refs.parentRef"
      class="flex h-full flex-col overflow-hidden border-r"
    >
      <div class="border-b">
        <FileUploader
          @success="changeContactImage"
          :validateFile="validateFile"
        >
          <template #default="{ openFileSelector, error }">
            <div class="flex flex-col items-start justify-start gap-4 p-5">
              <div class="flex gap-4 items-center">
                <div class="group relative h-15.5 w-15.5">
                  <Avatar
                    size="3xl"
                    class="h-15.5 w-15.5"
                    :label="contact.data.full_name"
                    :image="contact.data.image"
                  />
                  <component
                    :is="contact.data.image ? Dropdown : 'div'"
                    v-bind="
                      contact.data.image
                        ? {
                            options: [
                              {
                                icon: 'upload',
                                label: contact.data.image
                                  ? __('Change image')
                                  : __('Upload image'),
                                onClick: openFileSelector,
                              },
                              {
                                icon: 'trash-2',
                                label: __('Remove image'),
                                onClick: () => changeContactImage(''),
                              },
                            ],
                          }
                        : { onClick: openFileSelector }
                    "
                    class="!absolute bottom-0 left-0 right-0"
                  >
                    <div
                      class="z-1 absolute bottom-0 left-0 right-0 flex h-14 cursor-pointer items-center justify-center rounded-b-full bg-black bg-opacity-40 pt-5 opacity-0 duration-300 ease-in-out group-hover:opacity-100"
                      style="
                        -webkit-clip-path: inset(22px 0 0 0);
                        clip-path: inset(22px 0 0 0);
                      "
                    >
                      <CameraIcon class="h-6 w-6 cursor-pointer text-white" />
                    </div>
                  </component>
                </div>
                <div class="flex flex-col gap-2 truncate text-ink-gray-9">
                  <div class="truncate text-2xl font-medium">
                    <span v-if="contact.data.salutation">
                      {{ contact.data.salutation + '. ' }}
                    </span>
                    <span>{{ contact.data.full_name }}</span>
                  </div>
                  <div
                    v-if="contact.data.company_name"
                    class="flex items-center gap-1.5 text-base text-ink-gray-8"
                  >
                    <Avatar
                      size="xs"
                      :label="contact.data.company_name"
                      :image="
                        getOrganization(contact.data.company_name)
                          ?.organization_logo
                      "
                    />
                    <span class="">{{ contact.data.company_name }}</span>
                  </div>
                  <ErrorMessage :message="__(error)" />
                </div>
              </div>
              <div class="flex gap-1.5">
                <Button
                  v-if="contact.data.actual_mobile_no"
                  :label="__('Make Call')"
                  size="sm"
                  @click="
                    callEnabled && makeCall(contact.data.actual_mobile_no)
                  "
                >
                  <template #prefix>
                    <PhoneIcon class="h-4 w-4" />
                  </template>
                </Button>
                <Button
                  :label="__('Delete')"
                  theme="red"
                  size="sm"
                  @click="deleteContact"
                >
                  <template #prefix>
                    <FeatherIcon name="trash-2" class="h-4 w-4" />
                  </template>
                </Button>
              </div>
            </div>
          </template>
        </FileUploader>
      </div>
      <div
        v-if="sections.data"
        class="flex flex-1 flex-col justify-between overflow-hidden"
      >
        <SidePanelLayout
          :sections="sections.data"
          doctype="Contact"
          :docname="contact.data.name"
          @reload="handleReload"
        />
      </div>
    </Resizer>
    <Tabs as="div" v-model="tabIndex" :tabs="tabs">
      <template #tab-item="{ tab, selected }">
        <button
          class="group flex items-center gap-2 border-b border-transparent py-2.5 text-base text-ink-gray-5 duration-300 ease-in-out hover:border-outline-gray-3 hover:text-ink-gray-9"
          :class="{ 'text-ink-gray-9': selected }"
        >
          <component v-if="tab.icon" :is="tab.icon" class="h-5" />
          {{ __(tab.label) }}
          <Badge
            class="group-hover:bg-surface-gray-7"
            :class="[selected ? 'bg-surface-gray-7' : 'bg-gray-600']"
            variant="solid"
            theme="gray"
            size="sm"
          >
            {{ tab.count }}
          </Badge>
        </button>
      </template>
      <template #tab-panel="{ tab }">
          <div v-if="tab.label === 'Contacts'">
            <div class="flex justify-end mb-4 mr-5 mt-5">
              <Button
                :label="__('Add Contact')"
                theme="gray"
                variant="solid"
                @click="handleAddContact"
              >
                <template #prefix>
                  <FeatherIcon name="plus" class="h-4 w-4" />
                </template>
              </Button>
            </div>
            <ContactListView
              v-if="contacts.length"
              class="mt-4"
              :rows="contacts"
              :columns="contactColumns"
              :options="{
                selectable: false,
                showTooltip: false,
                resizeColumn: true,
                onColumnResize: handleColumnResize
              }"
              @columnWidthUpdated="handleColumnWidthUpdate"
            />
            <div
              v-else
              class="grid flex-1 place-items-center text-xl font-medium text-ink-gray-4"
            >
              <div class="flex flex-col items-center justify-center space-y-3">
                <component :is="tab.icon" class="!h-10 !w-10" />
                <div>{{ __('No {0} Found', [__(tab.label)]) }}</div>
              </div>
            </div>
          </div>
          <div v-else-if="tab.label === 'Addresses'">
            <div class="flex justify-end mb-4 mr-5 mt-5">
              <Button
                :label="__('Add Address')"
                theme="gray"
                variant="solid"
                @click="handleAddAddress"
              >
                <template #prefix>
                  <FeatherIcon name="plus" class="h-4 w-4" />
                </template>
              </Button>
            </div>
            <AddressListView
              v-if="addresses.length"
              class="mt-4"
              :rows="addresses"
              :columns="addressColumns"
              :options="{
                selectable: false,
                showTooltip: false,
                resizeColumn: true,
                onColumnResize: handleAddressColumnResize
              }"
              @columnWidthUpdated="handleAddressColumnWidthUpdate"
            />
            <div
              v-else
              class="grid flex-1 place-items-center text-xl font-medium text-ink-gray-4"
            >
              <div class="flex flex-col items-center justify-center space-y-3">
                <component :is="tab.icon" class="!h-10 !w-10" />
                <div>{{ __('No {0} Found', [__(tab.label)]) }}</div>
              </div>
            </div>
          </div>
      </template>

    </Tabs>
  </div>
  <div v-else-if="contact.loading" class="flex h-full items-center justify-center">
    <div class="text-center">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
      <div class="mt-2 text-gray-600">{{ __('Loading...') }}</div>
    </div>
  </div>
  <ErrorPage
    v-else-if="errorTitle || contact.error"
    :errorTitle="errorTitle || __('Error')"
    :errorMessage="errorMessage || contact.error?.message || __('Failed to load contact')"
  />
  <AddressModal
    v-if="contact.data"
    v-model="showAddressModal"
    v-model:address="_address"
    :options="{
      linkedContact: contact.data.name,
      contactData: contact.data,
      afterInsert: async (doc) => {
        await contact.reload()
        await sections.reload()
        if (contact.data?.addresses) {
          const index = contact.data.addresses.findIndex(addr => addr.name === doc.name)
          if (index > -1) {
            contact.data.addresses[index] = doc
          } else {
            contact.data.addresses.push(doc)
          }
        }
        toast.success(doc.name === _address.value.name ? __('Address updated successfully') : __('Address added successfully'))
      }
    }"
  />
</template>

<script setup>

import AddressListView from '@/components/ListViews/AddressListView.vue'
import ContactListView from '@/components/ListViews/ContactListView.vue'

import AddressIcon from '@/components/Icons/AddressIcon.vue'
import UserIcon from '@/components/Icons/UserIcon.vue'
import ErrorPage from '@/components/ErrorPage.vue'
import Resizer from '@/components/Resizer.vue'
import Icon from '@/components/Icon.vue'
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import AddressModal from '@/components/Modals/AddressModal.vue'
import { formatDate, timeAgo } from '@/utils'
import { getView } from '@/utils/view'
import { getSettings } from '@/stores/settings'
import { getMeta } from '@/stores/meta'
import { globalStore } from '@/stores/global.js'
import { usersStore } from '@/stores/users.js'
import { organizationsStore } from '@/stores/organizations.js'
import { statusesStore } from '@/stores/statuses'
import { callEnabled } from '@/composables/settings'
import {
  Breadcrumbs,
  Avatar,
  FileUploader,
  Tabs,
  call,
  createResource,
  usePageMeta,
  Dropdown,
  toast,
} from 'frappe-ui'
import { ref, computed, h, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { errorMessage as _errorMessage } from '../utils'

const { brand } = getSettings()
const { $dialog, makeCall } = globalStore()

const { getUser } = usersStore()
const { getOrganization } = organizationsStore()
const { getDealStatus } = statusesStore()
const { doctypeMeta } = getMeta('Contact')
const triggerResize = ref(1)
const resizeEnabled = ref(true)
const props = defineProps({
  contactId: {
    type: String,
    required: true,
  },
})

const route = useRoute()
const router = useRouter()

const showAddressModal = ref(false)
const _contact = ref({})
const _address = ref({})

const errorTitle = ref('')
const errorMessage = ref('')

const contact = createResource({
  url: 'crm.api.contact.get_contact',
  cache: ['contact', props.contactId],
  params: { name: props.contactId },
  auto: true,
  transform: (data) => {
    if (!data) return null
    return {
      ...data,
      actual_mobile_no: data.mobile_no,
      mobile_no: data.mobile_no,
    }
  },
  onSuccess: () => {
    errorTitle.value = ''
    errorMessage.value = ''
  },
  onError: (err) => {
    if (err.messages?.[0]) {
      errorTitle.value = __('Not permitted')
      errorMessage.value = __(err.messages?.[0])
    } else {
      router.push({ name: 'Contacts' })
    }
  },
})

const breadcrumbs = computed(() => {
  let items = [{ label: __('Contacts'), route: { name: 'Contacts' } }]

  if (route.query.view || route.query.viewType) {
    let view = getView(route.query.view, route.query.viewType, 'Contact')
    if (view) {
      items.push({
        label: __(view.label),
        icon: view.icon,
        route: {
          name: 'Contacts',
          params: { viewType: route.query.viewType },
          query: { view: route.query.view },
        },
      })
    }
  }

  items.push({
    label: title.value,
    route: { name: 'Contact', params: { contactId: props.contactId } },
  })
  return items
})

const title = computed(() => {
  if (!contact.data) return props.contactId
  let t = doctypeMeta['Contact']?.title_field || 'name'
  return contact.data[t] || props.contactId
})

usePageMeta(() => {
  return {
    title: title.value,
    icon: brand.favicon,
  }
})

function validateFile(file) {
  let extn = file.name.split('.').pop().toLowerCase()
  if (!['png', 'jpg', 'jpeg'].includes(extn)) {
    return __('Only PNG and JPG images are allowed')
  }
}

async function changeContactImage(file) {
  await call('frappe.client.set_value', {
    doctype: 'Contact',
    name: props.contactId,
    fieldname: 'image',
    value: file?.file_url || '',
  })
  contact.reload()
}

async function deleteContact() {
  $dialog({
    title: __('Delete contact'),
    message: __('Are you sure you want to delete this contact? This will remove all links to addresses.'),
    actions: [
      {
        label: __('Delete'),
        theme: 'red',
        variant: 'solid',
        async onClick(close) {
          try {
            await call('crm.api.contact.delete_contact_safely', {
              contact_name: props.contactId
            })
            close()
            router.push({ name: 'Contacts' })
            toast.success(__('Contact deleted successfully'))
          } catch (error) {
            toast.error(error.message || __('Failed to delete contact'))
          }
        },
      },
    ],
  })
}

const tabIndex = ref(0)
const tabs = [
  {
    label: 'Contacts',
    icon: h(UserIcon, { class: 'h-4 w-4' }),
    count: computed(() => contacts.value.length),
  },
  {
    label: 'Addresses',
    icon: h(AddressIcon, { class: 'h-4 w-4' }),
    count: computed(() => addresses.value.length),
  },
]


const addresses = computed(() => {
  if (!contact.data?.addresses) return []
  return contact.data.addresses.map((address) => ({
    name: address.name,
    address_type: address.address_type,
    address_line1: address.address_line1,
    address_line2: address.address_line2,
    pincode: address.pincode,
    city: address.city,
    state: address.state,
    country: address.country,
  }))
})

const sections = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections',
  cache: ['sidePanelSections', 'Contact'],
  params: { doctype: 'Contact' },
  auto: true,
  transform: (data) => computed(() => getParsedSections(data)),
})

function getParsedSections(_sections) {
  if (!contact.data) return []
  return _sections.map((section) => {
    section.columns = section.columns.map((column) => {
      column.fields = column.fields.map((field) => {
        if (field.fieldname === 'email_id') {
          return {
            ...field,
            read_only: false,
            fieldtype: 'Dropdown',
            options: (contact.data?.email_ids || []).map((email) => ({
              name: email.name,
              value: email.email_id,
              selected: email.email_id === contact.data?.email_id,
              placeholder: 'john@doe.com',
              onClick: () => {
                if (!contact.data) return
                _contact.value.email_id = email.email_id
                setAsPrimary('email', email.email_id)
              },
              onSave: (option, isNew) => {
                if (!contact.data) return
                if (isNew) {
                  createNew('email', option.value)
                  if (contact.data.email_ids?.length === 1) {
                    _contact.value.email_id = option.value
                  }
                } else {
                  editOption(
                    'Contact Email',
                    option.name,
                    'email_id',
                    option.value,
                  )
                }
              },
              onDelete: async (option, isNew) => {
                if (!contact.data) return
                contact.data.email_ids = (contact.data.email_ids || []).filter(
                  (email) => email.name !== option.name,
                )
                !isNew && (await deleteOption('Contact Email', option.name))
                if (_contact.value.email_id === option.value) {
                  if (!contact.data.email_ids?.length) {
                    _contact.value.email_id = ''
                  } else {
                    _contact.value.email_id = contact.data.email_ids.find(
                      (email) => email.is_primary,
                    )?.email_id
                  }
                }
              },
            })) || [],
            create: () => {
              if (!contact.data) return
              if (!contact.data.email_ids) contact.data.email_ids = []
              contact.data.email_ids.push({
                name: 'new-1',
                value: '',
                selected: false,
                isNew: true,
              })
            },
          }
        } else if (field.fieldname === 'mobile_no') {
          return {
            ...field,
            read_only: false,
            fieldtype: 'Dropdown',
            options: (contact.data?.phone_nos || []).map((phone) => ({
              name: phone.name,
              value: phone.phone,
              selected: phone.is_primary_mobile_no,
              onClick: async () => {
                if (!contact.data) return
                _contact.value.actual_mobile_no = phone.phone
                _contact.value.mobile_no = phone.phone
                await setAsPrimary('mobile_no', phone.phone)
                await sections.reload()
              },
              onSave: async (option, isNew) => {
                if (!contact.data) return
                if (isNew) {
                  await createNew('phone', option.value)
                  await sections.reload()
                  if (contact.data.phone_nos?.length === 1) {
                    _contact.value.actual_mobile_no = option.value
                    _contact.value.mobile_no = option.value
                  }
                } else {
                  await editOption(
                    'Contact Phone',
                    option.name,
                    'phone',
                    option.value
                  )
                  await sections.reload()
                }
              },
              onDelete: async (option, isNew) => {
                if (!contact.data) return
                contact.data.phone_nos = (contact.data.phone_nos || []).filter(
                  (phone) => phone.name !== option.name
                )
                if (!isNew) {
                  await deleteOption('Contact Phone', option.name)
                  await sections.reload()
                }
                if (_contact.value.actual_mobile_no === option.value) {
                  if (!contact.data.phone_nos?.length) {
                    _contact.value.actual_mobile_no = ''
                    _contact.value.mobile_no = ''
                  } else {
                    const primaryPhone = contact.data.phone_nos.find(
                      (phone) => phone.is_primary_mobile_no
                    )
                    if (primaryPhone) {
                      _contact.value.actual_mobile_no = primaryPhone.phone
                      _contact.value.mobile_no = primaryPhone.phone
                    }
                  }
                }
              }
            })) || [],
            create: async () => {
              if (!contact.data) return
              if (!contact.data.phone_nos) contact.data.phone_nos = []
              contact.data.phone_nos.push({
                name: 'new-1',
                value: '',
                selected: false,
                isNew: true
              })
              await sections.reload()
            }
          }
        } else if (field.fieldname === 'phone') {
          return {
            ...field,
            read_only: false,
            fieldtype: 'Dropdown',
            options: (contact.data?.phone_nos || []).map((phone) => ({
              name: phone.name,
              value: phone.phone,
              selected: phone.is_primary_phone,
              onClick: async () => {
                if (!contact.data) return
                _contact.value.actual_mobile_no = phone.phone
                _contact.value.mobile_no = phone.phone
                await setAsPrimary('phone', phone.phone)
                await sections.reload()
              },
              onSave: async (option, isNew) => {
                if (!contact.data) return
                if (isNew) {
                  await createNew('phone', option.value)
                  await sections.reload()
                  if (contact.data.phone_nos?.length === 1) {
                    _contact.value.actual_mobile_no = option.value
                    _contact.value.mobile_no = option.value
                  }
                } else {
                  await editOption(
                    'Contact Phone',
                    option.name,
                    'phone',
                    option.value
                  )
                  await sections.reload()
                }
              },
              onDelete: async (option, isNew) => {
                if (!contact.data) return
                contact.data.phone_nos = (contact.data.phone_nos || []).filter(
                  (phone) => phone.name !== option.name
                )
                if (!isNew) {
                  await deleteOption('Contact Phone', option.name)
                  await sections.reload()
                }
                if (_contact.value.actual_mobile_no === option.value) {
                  if (!contact.data.phone_nos?.length) {
                    _contact.value.actual_mobile_no = ''
                    _contact.value.mobile_no = ''
                  } else {
                    const primaryPhone = contact.data.phone_nos.find(
                      (phone) => phone.is_primary_phone
                    )
                    if (primaryPhone) {
                      _contact.value.actual_mobile_no = primaryPhone.phone
                      _contact.value.mobile_no = primaryPhone.phone
                    }
                  }
                }
              }
            })) || [],
            create: async () => {
              if (!contact.data) return
              if (!contact.data.phone_nos) contact.data.phone_nos = []
              contact.data.phone_nos.push({
                name: 'new-1',
                value: '',
                selected: false,
                isNew: true
              })
              await sections.reload()
            }
          }
        } else if (field.fieldname === 'address') {
          return {
            ...field,
            create: (value, close) => {
              _address.value = {
                address_type: 'Contact',
                address_line1: value || '',
                is_primary_address: !contact.data?.addresses?.length,
                is_shipping_address: !contact.data?.addresses?.length,
              }
              showAddressModal.value = true
              close()
            },
            edit: async (addr) => {
              try {
                _address.value = await call('frappe.client.get', {
                  doctype: 'Address',
                  name: addr,
                  fieldname: [
                    'name',
                    'address_type',
                    'address_line1',
                    'address_line2',
                    'city',
                    'state',
                    'country',
                    'pincode',
                    'is_primary_address',
                    'is_shipping_address',
                    'links'
                  ]
                })
                showAddressModal.value = true
              } catch (error) {
                toast.error(__('Failed to load address details'))
              }
            },
          }
        } else {
          return field
        }
      })
      return column
    })
    return section
  })
}

async function setAsPrimary(field, value) {
  let d = await call('crm.api.contact.set_as_primary', {
    contact: contact.data.name,
    field,
    value,
  })
  if (d) {
    await contact.reload()
    await sections.reload()
    if (field === 'mobile_no') {
      _contact.value.actual_mobile_no = value
      _contact.value.mobile_no = value
    }
    toast.success(__('Contact updated'))
  }
}

async function createNew(field, value) {
  if (!value) return
  let d = await call('crm.api.contact.create_new', {
    contact: contact.data.name,
    field,
    value,
  })
  if (d) {
    await contact.reload()
    await sections.reload()
    if (field === 'phone' && contact.data?.phone_nos?.length === 1) {
      const newPhone = contact.data.phone_nos[0]
      if (newPhone.is_primary_mobile_no) {
        _contact.value.actual_mobile_no = newPhone.phone
        _contact.value.mobile_no = newPhone.phone
      }
    }
    toast.success(__('Contact updated'))
  }
}

async function editOption(doctype, name, fieldname, value) {
  let d = await call('frappe.client.set_value', {
    doctype,
    name,
    fieldname,
    value,
  })
  if (d) {
    await contact.reload()
    await sections.reload()
    toast.success(__('Contact updated'))
  }
}

async function deleteOption(doctype, name) {
  await call('frappe.client.delete', {
    doctype,
    name,
  })
  await contact.reload()
  await sections.reload()
  toast.success(__('Contact updated'))
}

async function updateField(fieldname, value) {
  await call('frappe.client.set_value', {
    doctype: 'Contact',
    name: props.contactId,
    fieldname,
    value,
  })
  toast.success(__('Contact updated'))

  contact.reload()
}

const addressColumns = ref([
  { label: 'Address Type', key: 'address_type', width: '10rem' },
  { label: 'Address Line 1', key: 'address_line1', width: '12rem' },
  { label: 'Address Line 2', key: 'address_line2', width: '12rem' },
  { label: 'Pincode', key: 'pincode', width: '8rem' },
  { label: 'City', key: 'city', width: '10rem' },
  { label: 'State', key: 'state', width: '10rem' },
  { label: 'Country', key: 'country', width: '10rem' },
])

const contactColumns = ref([
  { label: __('Last Name'), key: 'custom_last_name', width: '8rem' },
  { label: __('Name'), key: 'custom_name', width: '8rem' },
  { label: __('Title'), key: 'custom_title', width: '7rem' },
  { label: __('Email'), key: 'custom_email', width: '10rem' },
  { label: __('Phone'), key: 'custom_telefon', width: '8rem' },
  { label: __('Function'), key: 'custom_function', width: '8rem' },
  { label: __('Number'), key: 'phone', width: '8rem' },
])

const contacts = computed(() => {
  if (!contact.data?.phone_nos) return []
  return contact.data.phone_nos.map((phone) => ({
    name: phone.name,
    phone: phone.phone,
    custom_name: phone.custom_name || '',
    custom_last_name: phone.custom_last_name || '',
    custom_email: phone.custom_email || '',
    custom_title: phone.custom_title || '',
    custom_telefon: phone.custom_telefon || '',
    custom_function: phone.custom_function || '',
  }))
})

async function handleReload() {
  await contact.reload()
  await sections.reload()
}

function handleAddAddress() {
  _address.value = {
    address_type: 'Contact',
    is_primary_address: !addresses.length,
    is_shipping_address: !addresses.length,
    links: [{
      link_doctype: 'Contact',
      link_name: contact.data.name,
      link_title: contact.data.full_name
    }]
  }
  showAddressModal.value = true
}

function handleAddContact() {
  toast.info(__('Contact creation functionality coming soon'))
}


onMounted(() => {

  const savedContactWidths = localStorage.getItem('contactColumnsWidth')
  if (savedContactWidths) {
    try {
      const widths = JSON.parse(savedContactWidths)
      contactColumns.value = contactColumns.value.map(col => ({
        ...col,
        width: widths[col.key] || col.width
      }))
    } catch (e) {
      console.error('Error loading saved contact column widths:', e)
    }
  }

  // Load address column widths
  const savedAddressWidths = localStorage.getItem('addressColumnsWidth')
  if (savedAddressWidths) {
    try {
      const widths = JSON.parse(savedAddressWidths)
      addressColumns.value = addressColumns.value.map(col => ({
        ...col,
        width: widths[col.key] || col.width
      }))
    } catch (e) {
      console.error('Error loading saved address column widths:', e)
    }
  }
})

function handleColumnWidthUpdate(column) {
  // Save the new column width to localStorage
  const widths = contactColumns.value.reduce((acc, col) => {
    acc[col.key] = col.width
    return acc
  }, {})
  localStorage.setItem('contactColumnsWidth', JSON.stringify(widths))
}

function handleColumnResize(column, newWidth) {
  const col = contactColumns.value.find(c => c.key === column.key)
  if (col) {
    col.width = newWidth
    handleColumnWidthUpdate(column)
  }
}

function handleAddressColumnWidthUpdate(column) {
  // Save the new column width to localStorage
  const widths = addressColumns.value.reduce((acc, col) => {
    acc[col.key] = col.width
    return acc
  }, {})
  localStorage.setItem('addressColumnsWidth', JSON.stringify(widths))
}

function handleAddressColumnResize(column, newWidth) {
  const col = addressColumns.value.find(c => c.key === column.key)
  if (col) {
    col.width = newWidth
    handleAddressColumnWidthUpdate(column)
  }
}
</script>

<style scoped>
.animate-spin {
  animation: spin 1s linear infinite;
}
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
