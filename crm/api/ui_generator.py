import os
import re
import frappe
from frappe import _
from frappe.utils import random_string
from frappe.model.document import Document

@frappe.whitelist()
def generate_ui_for_doctype(doctype_name, module_name=None):
    """Insert a generated class into the existing doctype .py file"""
    generator = CRMUIGenerator()

    try:
        if not doctype_name:
            frappe.throw(_("Doctype name is required"))

        # Convert to PascalCase
        pascal_case_name = "".join(word.capitalize() for word in doctype_name.split("_"))
        print("PascalCase name:", pascal_case_name)

        # Get correct app path - ensure we're using the CRM app path
        app_path = frappe.get_app_path("crm")  # This should return /home/kumel/ui/frappe-bench/apps/crm/crm
        doctype_dir = os.path.join(app_path, "fcrm", "doctype", doctype_name.lower())
        doctype_path = os.path.join(doctype_dir, f"{doctype_name.lower()}.py")

        print(f"App path: {app_path}")
        print(f"Doctype dir: {doctype_dir}")
        print(f"Target file path: {doctype_path}")

        if not os.path.exists(doctype_path):
            frappe.throw(_("Doctype .py file does not exist: {0}").format(doctype_path))

        # Build the class content
        doctype_class_code = f'''# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import random_string


class {pascal_case_name}(Document):
    def validate(self):
        if not self.name:
            frappe.throw(_("Name is required"))

    @classmethod
    def default_list_data(cls):
        fields = frappe.get_meta("{doctype_name}").fields
        data_fields = [
            field for field in fields
            if field.fieldtype not in ["Section Break", "Column Break", "Tab Break"]
            and field.fieldname not in ["name", "owner", "modified", "modified_by", "creation", "idx"]
        ]

        columns = []
        rows = []

        columns.extend([
            {{
                "label": "{pascal_case_name} Name",
                "fieldname": "name",
                "fieldtype": "Data",
                "width": 200,
                "key": "name"
            }},
            {{
                "label": "Modified",
                "fieldname": "modified",
                "fieldtype": "Datetime",
                "width": 150,
                "key": "modified"
            }}
        ])
        rows.extend(["name", "modified"])

        for field in data_fields:
            if field.fieldname != "name":
                columns.append({{
                    "label": field.label,
                    "fieldname": field.fieldname,
                    "fieldtype": field.fieldtype,
                    "width": 200,
                    "key": field.fieldname
                }})
                rows.append(field.fieldname)

        return {{
            "columns": columns,
            "rows": rows,
            "order_by": "modified desc"
        }}

    def after_insert(self):
        if not frappe.db.exists("CRM Fields Layout", {{"dt": "{doctype_name}", "type": "Quick Entry"}}):
            self.create_default_layout("Quick Entry")
        if not frappe.db.exists("CRM Fields Layout", {{"dt": "{doctype_name}", "type": "Required Fields"}}):
            self.create_default_layout("Required Fields")

    def create_default_layout(self, layout_type):
        fields = frappe.get_meta("{doctype_name}").fields
        layout = []

        if layout_type == "Required Fields":
            fields = [f for f in fields if f.reqd]

        tab = {{
            "name": "tab_" + random_string(4),
            "sections": [{{
                "name": "section_" + random_string(4),
                "columns": [{{
                    "name": "column_" + random_string(4),
                    "fields": []
                }}]
            }}]
        }}

        for field in fields:
            if field.fieldtype not in ["Section Break", "Column Break", "Tab Break"]:
                if layout_type == "Required Fields" and not field.reqd:
                    continue
                tab["sections"][0]["columns"][0]["fields"].append(field.fieldname)

        layout.append(tab)

        doc = frappe.new_doc("CRM Fields Layout")
        doc.update({{
            "dt": "{doctype_name}",
            "type": layout_type,
            "layout": frappe.as_json(layout)
        }})
        doc.insert(ignore_permissions=True)

    @frappe.whitelist()
    def get_quick_entry_fields(self):
        from crm.fcrm.doctype.crm_fields_layout.crm_fields_layout import get_fields_layout
        return get_fields_layout("{doctype_name}", "Quick Entry")

    @frappe.whitelist()
    def get_required_fields(self):
        from crm.fcrm.doctype.crm_fields_layout.crm_fields_layout import get_fields_layout
        return get_fields_layout("{doctype_name}", "Required Fields")'''

        # Read the current content
        with open(doctype_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Find the existing class
        class_start = content.find(f"class {pascal_case_name}(Document):")
        if class_start != -1:
            # Find the end of the class (next class or end of file)
            next_class = content.find("class ", class_start + 1)
            if next_class != -1:
                # Replace from class start to next class
                content = content[:class_start] + doctype_class_code + "\n\n" + content[next_class:]
            else:
                # Replace from class start to end of file
                content = content[:class_start] + doctype_class_code

            # Write back the updated content
            with open(doctype_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ Updated class {pascal_case_name} in {doctype_path}")
        else:
            print(f"⚠️ Could not find class {pascal_case_name} in {doctype_path}")

        # Reload Doctype
        try:
            frappe.reload_doc("crm", "fcrm", "doctype", doctype_name.lower(), doctype_name.lower())
            print(f"✅ Reloaded doctype {doctype_name}")
        except Exception as reload_err:
            print(f"⚠️ Error reloading doctype: {reload_err}")
            frappe.log_error(f"Doctype reload error for {doctype_name}: {reload_err}")

        # Call frontend generator
        generator._generate_ui_components(doctype_name, module_name)

    except Exception as e:
        import traceback
        error_msg = f"❌ Error generating UI for {doctype_name}: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        frappe.log_error(error_msg)
        frappe.throw(_(f"Error generating UI for {doctype_name}: {str(e)}"))

class CRMUIGenerator:
    def __init__(self):
        self.app_path = frappe.get_app_path("crm")
        self.frontend_path = os.path.join(self.app_path, "..", "frontend")
        self.src_path = os.path.join(self.frontend_path, "src")
        self.pages_path = os.path.join(self.src_path, "pages")
        self.components_path = os.path.join(self.src_path, "components")
        self.list_views_path = os.path.join(self.components_path, "ListViews")
        self.icons_path = os.path.join(self.components_path, "Icons")
        self.api_path = os.path.join(self.src_path, "api")
        self.stores_path = os.path.join(self.src_path, "stores")
        self.composables_path = os.path.join(self.src_path, "composables")
        self.utils_path = os.path.join(self.src_path, "utils")
        self.tests_path = os.path.join(self.frontend_path, "tests")
        
    def pascal_case(self, s):
        """Convert string to PascalCase"""
        words = re.findall(r'[a-zA-Z0-9]+', s)
        return ''.join(word.capitalize() for word in words)
        
    def camel_case(self, s):
        """Convert string to camelCase"""
        pascal = self.pascal_case(s)
        return pascal[0].lower() + pascal[1:]
        
    def kebab_case(self, s):
        """Convert string to kebab-case"""
        words = re.findall(r'[a-zA-Z0-9]+', s)
        return '-'.join(word.lower() for word in words)
        
    def _generate_ui_components(self, doctype_name, module_name=None):
        """Internal method to generate UI components for a doctype"""
        try:
            # Check if it's a child doctype
            meta = frappe.get_meta(doctype_name)
            if meta.istable:
                print(f"Doctype {doctype_name} is a child table, skipping UI generation")
                return

            # Create frontend API file
            print(f"Creating frontend API for {doctype_name}")
            self.create_frontend_api(doctype_name)
            
            # Create other UI components only if they don't exist
            store_file = os.path.join(self.stores_path, f"{doctype_name.lower()}.js")
            if not os.path.exists(store_file):
                print(f"Creating store for {doctype_name}")
                self.create_store(doctype_name)
            
            composable_file = os.path.join(self.composables_path, f"use{self.pascal_case(doctype_name)}.js")
            if not os.path.exists(composable_file):
                print(f"Creating composables for {doctype_name}")
                self.create_composables(doctype_name)
            
            utils_file = os.path.join(self.utils_path, f"{doctype_name.lower()}.js")
            if not os.path.exists(utils_file):
                print(f"Creating utils for {doctype_name}")
                self.create_utils(doctype_name)
            
            icon_file = os.path.join(self.icons_path, f"{self.pascal_case(doctype_name)}Icon.vue")
            if not os.path.exists(icon_file):
                print(f"Creating icon for {doctype_name}")
                self.create_icon(doctype_name)
            
            list_view_file = os.path.join(self.list_views_path, f"{self.pascal_case(doctype_name)}ListView.vue")
            if not os.path.exists(list_view_file):
                print(f"Creating list view for {doctype_name}")
                self.create_list_view(doctype_name)
            
            modal_file = os.path.join(self.components_path, "Modals", f"{self.pascal_case(doctype_name)}Modal.vue")
            if not os.path.exists(modal_file):
                print(f"Creating modal for {doctype_name}")
                self.create_modal(doctype_name)
            
            page_file = os.path.join(self.pages_path, f"{self.pascal_case(doctype_name)}s.vue")
            if not os.path.exists(page_file):
                print(f"Creating page for {doctype_name}")
                self.create_page(doctype_name)
            
            detail_page_file = os.path.join(self.pages_path, f"{self.pascal_case(doctype_name)}.vue")
            if not os.path.exists(detail_page_file):
                print(f"Creating detail page for {doctype_name}")
                self.create_detail_page(doctype_name)
            
            mobile_file = os.path.join(self.pages_path, f"{self.pascal_case(doctype_name)}Mobile.vue")
            if not os.path.exists(mobile_file):
                print(f"Creating mobile view for {doctype_name}")
                self.create_mobile_view(doctype_name)
            
            # Create field layout and API endpoints always
            print(f"Creating field layout for {doctype_name}")
            self.create_field_layout(doctype_name)
            
            print(f"Creating API endpoints for {doctype_name}")
            self.create_api_endpoints(doctype_name)
            
            # Add telemetry if available
            print(f"Adding telemetry for {doctype_name}")
            self.add_telemetry(doctype_name)
            
            # Create tests if they don't exist
            test_file = os.path.join(self.tests_path, f"{doctype_name.lower()}.test.js")
            if not os.path.exists(test_file):
                print(f"Creating tests for {doctype_name}")
                self.create_tests(doctype_name)
            
            # Update router and sidebar
            print(f"Updating router for {doctype_name}")
            router_updated = self.update_router(doctype_name)
            
            print(f"Updating sidebar for {doctype_name}")
            sidebar_updated = self.update_sidebar(doctype_name)
            
            status_msg = f"UI components generated for {doctype_name}\n"
            if router_updated:
                status_msg += "Router updated successfully.\n"
            if sidebar_updated:
                status_msg += "Sidebar updated successfully.\n"
                
            print(status_msg)
            frappe.msgprint(_(status_msg))

        except Exception as e:
            frappe.log_error(f"Error generating UI components for {doctype_name}: {str(e)}")
            frappe.throw(_(f"Error generating UI components for {doctype_name}: {str(e)}"))

    def create_store(self, doctype_name):
        """Create Vuex store for the doctype"""
        store_name = f"{doctype_name.lower()}.js"
        store_file = os.path.join(self.stores_path, store_name)
        
        if os.path.exists(store_file):
            frappe.msgprint(_("Store for {0} already exists").format(doctype_name))
            return
            
        os.makedirs(os.path.dirname(store_file), exist_ok=True)
        
        store_template = f"""import {{ defineStore }} from 'pinia'
import {{ createResource }} from 'frappe-ui'

export const use{self.pascal_case(doctype_name)}Store = defineStore('{doctype_name.lower()}', {{
    state: () => ({{
        items: {{}},
        loading: false,
        error: null,
        selected: null
    }}),
    
    getters: {{
        get{self.pascal_case(doctype_name)}: (state) => (name) => state.items[name],
        isLoading: (state) => state.loading,
        hasError: (state) => state.error !== null,
        getSelected: (state) => state.selected
    }},
    
    actions: {{
        async fetch{self.pascal_case(doctype_name)}(name) {{
            this.loading = true
            this.error = null
            try {{
                const resource = createResource({{
                    url: 'crm.api.{doctype_name.lower()}.get_{doctype_name.lower()}',
                    params: {{ name }},
                    cache: ['{doctype_name.lower()}', name],
                    auto: true
                }})
                await resource.fetch()
                this.items[name] = resource.data
            }} catch (error) {{
                this.error = error
                console.error('Error fetching {doctype_name}:', error)
            }} finally {{
                this.loading = false
            }}
        }},
        
        setSelected(name) {{
            this.selected = name
        }},
        
        clearSelected() {{
            this.selected = null
        }}
    }}
}})
"""
        with open(store_file, "w") as f:
            f.write(store_template)

    def create_composables(self, doctype_name):
        """Create composables for the doctype"""
        composable_name = f"use{self.pascal_case(doctype_name)}.js"
        composable_file = os.path.join(self.composables_path, composable_name)
        
        if os.path.exists(composable_file):
            frappe.msgprint(_("Composable for {0} already exists").format(doctype_name))
            return
            
        os.makedirs(os.path.dirname(composable_file), exist_ok=True)
        
        composable_template = f"""import {{ ref, computed }} from 'vue'
import {{ use{self.pascal_case(doctype_name)}Store }} from '@/stores/{doctype_name.lower()}'
import {{ formatDate, timeAgo }} from '@/utils'

export function use{self.pascal_case(doctype_name)}() {{
    const store = use{self.pascal_case(doctype_name)}Store()
    
    const loading = computed(() => store.isLoading)
    const error = computed(() => store.hasError)
    const selected = computed(() => store.getSelected)
    
    async function fetch{self.pascal_case(doctype_name)}(name) {{
        await store.fetch{self.pascal_case(doctype_name)}(name)
    }}
    
    function setSelected(name) {{
        store.setSelected(name)
    }}
    
    function clearSelected() {{
        store.clearSelected()
    }}
    
    function formatData(data) {{
        if (!data) return null
        return {{
            ...data,
            modified: {{
                label: formatDate(data.modified),
                timeAgo: timeAgo(data.modified)
            }}
        }}
    }}
    
    return {{
        loading,
        error,
        selected,
        fetch{self.pascal_case(doctype_name)},
        setSelected,
        clearSelected,
        formatData
    }}
}}
"""
        with open(composable_file, "w") as f:
            f.write(composable_template)

    def create_utils(self, doctype_name):
        """Create utility functions for the doctype"""
        utils_name = f"{doctype_name.lower()}.js"
        utils_file = os.path.join(self.utils_path, utils_name)
        
        if os.path.exists(utils_file):
            frappe.msgprint(_("Utils for {0} already exists").format(doctype_name))
            return
            
        os.makedirs(os.path.dirname(utils_file), exist_ok=True)
        
        utils_template = f"""import {{ formatDate, timeAgo }} from '@/utils'

export function format{self.pascal_case(doctype_name)}Data(data) {{
    if (!data) return null
    
    return {{
        ...data,
        modified: {{
            label: formatDate(data.modified),
            timeAgo: timeAgo(data.modified)
        }},
        created: {{
            label: formatDate(data.creation),
            timeAgo: timeAgo(data.creation)
        }}
    }}
}}

export function validate{self.pascal_case(doctype_name)}Data(data) {{
    const errors = []
    
    if (!data.name) {{
        errors.push('Name is required')
    }}
    
    // Add more validation based on doctype meta
    // Example validations:
    // if (!data.email) {{
    //     errors.push('Email is required')
    // }}
    // if (data.email && !isValidEmail(data.email)) {{
    //     errors.push('Invalid email format')
    // }}
    
    return errors
}}

export function get{self.pascal_case(doctype_name)}Breadcrumbs(name, route) {{
    return [
        {{
            label: '{self.pascal_case(doctype_name)}s',
            route: {{ name: '{self.pascal_case(doctype_name)}s' }}
        }},
        {{
            label: name,
            route: {{
                name: '{self.pascal_case(doctype_name)}',
                params: {{ {doctype_name.lower()}Id: name }}
            }}
        }}
    ]
}}
"""
        with open(utils_file, "w") as f:
            f.write(utils_template)

    def create_icon(self, doctype_name):
        """Create an icon component for the doctype"""
        icon_name = f"{self.pascal_case(doctype_name)}Icon"
        icon_file = os.path.join(self.icons_path, f"{icon_name}.vue")
        
        if os.path.exists(icon_file):
            frappe.msgprint(_("Icon for {0} already exists").format(doctype_name))
            return
            
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(icon_file), exist_ok=True)
            
        icon_template = """<template>
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
    class="feather feather-file"
  >
    <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path>
    <polyline points="13 2 13 9 20 9"></polyline>
  </svg>
</template>
"""
        with open(icon_file, "w") as f:
            f.write(icon_template)
            
    def create_list_view(self, doctype_name):
        """Create a list view component for the doctype"""
        list_view_name = f"{self.pascal_case(doctype_name)}ListView"
        list_view_file = os.path.join(self.list_views_path, f"{list_view_name}.vue")
        
        if os.path.exists(list_view_file):
            frappe.msgprint(_("List view for {0} already exists").format(doctype_name))
            return
            
        os.makedirs(os.path.dirname(list_view_file), exist_ok=True)
            
        list_view_template = f"""<template>
  <ListView
    v-bind="$attrs"
    :columns="columns"
    :rows="rows"
    :options="options"
    @loadMore="$emit('loadMore')"
    @columnWidthUpdated="$emit('columnWidthUpdated')"
    @updatePageCount="$emit('updatePageCount', $event)"
    @applyFilter="$emit('applyFilter', $event)"
    @applyLikeFilter="$emit('applyLikeFilter', $event)"
    @likeDoc="$emit('likeDoc', $event)"
    @selectionsChanged="$emit('selectionsChanged', $event)"
  >
    <template #cell-name="{{ row }}">
      <div class="flex items-center gap-2">
        <Avatar
          :image="row.name?.image"
          :label="row.name?.label || row.name"
          size="sm"
        />
        <router-link
          :to="{{
            name: '{self.pascal_case(doctype_name)}',
            params: {{ {doctype_name.lower()}Id: row.name }},
          }}"
          class="text-ink-gray-9 hover:text-ink-gray-9"
        >
          {{ row.name?.label || row.name }}
        </router-link>
      </div>
    </template>
    
    <template #cell-email="{{ row }}">
      <a :href="'mailto:' + row.email" class="text-blue-600 hover:underline">
        {{ row.email }}
      </a>
    </template>
    
    <template #cell-mobile_no="{{ row }}">
      <a :href="'tel:' + row.mobile_no" class="text-blue-600 hover:underline">
        {{ row.mobile_no }}
      </a>
    </template>
    
    <template #cell-modified="{{ row }}">
      <div class="flex flex-col">
        <span>{{ row.modified?.label }}</span>
        <span class="text-xs text-gray-500">{{ row.modified?.timeAgo }}</span>
      </div>
    </template>
    
    <template #customActions>
      <slot name="customActions"></slot>
    </template>
  </ListView>
</template>

<script setup>
import {{ ListView, Avatar }} from 'frappe-ui'
import {{ formatDate, timeAgo }} from '@/utils'
import {{ use{self.pascal_case(doctype_name)} }} from '@/composables/use{self.pascal_case(doctype_name)}'

const props = defineProps({{
  rows: {{
    type: Array,
    default: () => [],
  }},
  columns: {{
    type: Array,
    default: () => [],
  }},
  options: {{
    type: Object,
    default: () => ({{}}),
  }},
  list: {{
    type: Object,
    default: () => ({{}}),
  }},
}})

const {{ formatData }} = use{self.pascal_case(doctype_name)}()

defineEmits([
  'loadMore',
  'columnWidthUpdated',
  'updatePageCount',
  'applyFilter',
  'applyLikeFilter',
  'likeDoc',
  'selectionsChanged',
  'update:list',
])
</script>
"""
        with open(list_view_file, "w") as f:
            f.write(list_view_template)
            
    def create_modal(self, doctype_name):
        """Create a modal component for the doctype"""
        modal_name = f"{self.pascal_case(doctype_name)}Modal"
        modal_file = os.path.join(self.components_path, "Modals", f"{modal_name}.vue")
        
        if os.path.exists(modal_file):
            frappe.msgprint(_("Modal for {0} already exists").format(doctype_name))
            return
        
        os.makedirs(os.path.dirname(modal_file), exist_ok=True)
        
        # Get the field that should be required (usually name or customer_name)
        meta = frappe.get_meta(doctype_name)
        required_field = "name"  # default
        for field in meta.fields:
            if field.reqd and field.fieldname in ["name", f"{doctype_name.lower()}_name"]:
                required_field = field.fieldname
                break
        
        modal_template = f"""<template>
  <Dialog v-model="show" :options="{{ size: 'xl' }}">
    <template #body>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
              {{{{ __('New {doctype_name}') }}}}
            </h3>
          </div>
          <div class="flex items-center gap-1">
            <Button
              v-if="isManager() && !isMobileView"
              variant="ghost"
              class="w-7"
              @click="openQuickEntryModal"
            >
              <EditIcon class="h-4 w-4" />
            </Button>
            <Button variant="ghost" class="w-7" @click="show = false">
              <FeatherIcon name="x" class="h-4 w-4" />
            </Button>
          </div>
        </div>
        <div v-if="error" class="mb-4 rounded bg-red-50 p-4 text-red-700">
          {{{{ error }}}}
        </div>
        <FieldLayout
          v-if="tabs.data?.length"
          :tabs="tabs.data"
          :data="_{doctype_name.lower()}"
          doctype="{doctype_name}"
          @update:data="(val) => (_{doctype_name.lower()} = val)"
        />
      </div>
      <div class="px-4 pb-7 pt-4 sm:px-6">
        <div class="space-y-2">
          <Button
            class="w-full"
            variant="solid"
            :label="__('Create')"
            :loading="loading"
            @click="create{self.pascal_case(doctype_name)}"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import {{ usersStore }} from '@/stores/users'
import {{ isMobileView }} from '@/composables/settings'
import {{ capture }} from '@/telemetry'
import {{ call, createResource }} from 'frappe-ui'
import {{ ref, nextTick, watch }} from 'vue'
import {{ useRouter }} from 'vue-router'

const props = defineProps({{
  {doctype_name.lower()}: {{
    type: Object,
    default: () => ({{}}),
  }},
  options: {{
    type: Object,
    default: () => ({{
      afterInsert: () => {{}},
    }}),
  }},
}})

const {{ isManager }} = usersStore()
const router = useRouter()
const show = defineModel()
const loading = ref(false)
const error = ref('')
const _{doctype_name.lower()} = ref({{}})

async function create{self.pascal_case(doctype_name)}() {{
  loading.value = true
  error.value = ''
  
  try {{
    const doc = await call('frappe.client.insert', {{
      doc: {{
        doctype: '{doctype_name}',
        ..._{doctype_name.lower()}.value,
      }},
    }})
    
    if (doc.name) {{
      capture('{doctype_name.lower()}_created')
      handle{self.pascal_case(doctype_name)}Update(doc)
    }}
  }} catch (e) {{
    error.value = e.message || __('Error creating {doctype_name}')
    console.error('Error creating {doctype_name}:', e)
  }} finally {{
    loading.value = false
  }}
}}

function handle{self.pascal_case(doctype_name)}Update(doc) {{
  // Reload the parent component's data to refresh the list
  props.{doctype_name.lower()}?.reload?.()
  // Close the modal
  show.value = false
  // Call afterInsert callback if provided
  props.options.afterInsert && props.options.afterInsert(doc)
}}

const tabs = createResource({{
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['QuickEntry', '{doctype_name}'],
  params: {{ doctype: '{doctype_name}', type: 'Quick Entry' }},
  auto: true,
  transform: (_tabs) => {{
    return _tabs.forEach((tab) => {{
      tab.sections.forEach((section) => {{
        section.columns.forEach((column) => {{
          column.fields.forEach((field) => {{
            if (field.fieldtype === 'Table') {{
              _{doctype_name.lower()}.value[field.fieldname] = []
            }}
          }})
        }})
      }})
    }})
  }},
}})

watch(
  () => show.value,
  (value) => {{
    if (!value) {{
      error.value = ''
      return
    }}
    nextTick(() => {{
      _{doctype_name.lower()}.value = {{ ...props.{doctype_name.lower()}.data }}
    }})
  }},
)

const showQuickEntryModal = defineModel('showQuickEntryModal')

function openQuickEntryModal() {{
  showQuickEntryModal.value = true
  nextTick(() => (show.value = false))
}}
</script>

<style scoped>
:deep(:has(> .dropdown-button)) {{
  width: 100%;
}}
</style>
"""
        with open(modal_file, "w") as f:
            f.write(modal_template)

    def create_api_endpoints(self, doctype_name):
        """Create API endpoints for the doctype"""
        # Create API file in the doctype directory
        api_name = "api.py"
        api_file = os.path.join(self.app_path, "fcrm", "doctype", doctype_name.lower(), api_name)
        
        if os.path.exists(api_file):
            frappe.msgprint(_("API endpoints for {0} already exist").format(doctype_name))
            return
            
        os.makedirs(os.path.dirname(api_file), exist_ok=True)
        
        api_template = f"""import frappe
from frappe import _
from frappe.utils import cstr
import json
from frappe.model.document import Document

@frappe.whitelist()
def get_{doctype_name.lower()}(name):
    \"\"\"Get {doctype_name} details\"\"\"
    doc = frappe.get_doc("{doctype_name}", name)
    doc.check_permission("read")
    
    doc = doc.as_dict()
    doc["fields_meta"] = get_fields_meta("{doctype_name}")
    doc["_form_script"] = get_form_script("{doctype_name}")
    doc["_assign"] = get_assigned_users("{doctype_name}", doc.name)
    return doc

@frappe.whitelist()
def create_{doctype_name.lower()}(doc):
    \"\"\"Create new {doctype_name}\"\"\"
    if not doc.get("name"):
        frappe.throw(_("Name is required"))
    
    doc = frappe._dict(json.loads(doc))
    doc.doctype = "{doctype_name}"
    
    try:
        new_doc = frappe.get_doc(doc)
        new_doc.insert()
        frappe.db.commit()
        return new_doc.as_dict()
    except Exception as e:
        frappe.db.rollback()
        frappe.throw(str(e))

@frappe.whitelist()
def update_{doctype_name.lower()}(name, field, value):
    \"\"\"Update {doctype_name} field\"\"\"
    doc = frappe.get_doc("{doctype_name}", name)
    doc.check_permission("write")
    
    try:
        doc.set(field, value)
        doc.save()
        frappe.db.commit()
        return doc.as_dict()
    except Exception as e:
        frappe.db.rollback()
        frappe.throw(str(e))

@frappe.whitelist()
def delete_{doctype_name.lower()}(name):
    \"\"\"Delete {doctype_name}\"\"\"
    doc = frappe.get_doc("{doctype_name}", name)
    doc.check_permission("delete")
    
    try:
        doc.delete()
        frappe.db.commit()
        return True
    except Exception as e:
        frappe.db.rollback()
        frappe.throw(str(e))

@frappe.whitelist()
def get_{doctype_name.lower()}_list(filters=None, fields=None, order_by=None, limit=None, start=None):
    \"\"\"Get list of {doctype_name}s\"\"\"
    if not filters:
        filters = {{}}
    if not fields:
        fields = ["name", "modified", "creation"]
    if not order_by:
        order_by = "modified desc"
        
    try:
        return frappe.get_list(
            "{doctype_name}",
            filters=filters,
            fields=fields,
            order_by=order_by,
            limit=limit,
            start=start
        )
    except Exception as e:
        frappe.throw(str(e))

def get_fields_meta(doctype):
    \"\"\"Get fields metadata for the doctype\"\"\"
    meta = frappe.get_meta(doctype)
    return meta.get("fields")

def get_form_script(doctype):
    \"\"\"Get form script for the doctype\"\"\"
    return frappe.get_doc("Form Script", doctype).script if frappe.db.exists("Form Script", doctype) else None

def get_assigned_users(doctype, name):
    \"\"\"Get users assigned to the document\"\"\"
    return frappe.get_all(
        "ToDo",
        filters={{
            "reference_type": doctype,
            "reference_name": name,
            "status": "Open"
        }},
        fields=["owner"]
    )
"""
        with open(api_file, "w") as f:
            f.write(api_template)
        print(f"Created API file at {api_file}")

    def create_field_layout(self, doctype_name):
        """Create field layout configuration for the doctype"""
        try:
            meta = frappe.get_meta(doctype_name)
            fields = meta.get("fields")
            
            # Create field layout document
            field_layout = frappe.get_doc({
              "doctype": "CRM Fields Layout",
              "doctype_name": doctype_name,
              "type": "Quick Entry",
              "tabs": [
                  {
                      "label": "Basic Information",
                      "sections": [
                          {
                              "columns": [
                                  {
                                      "fields": [
                                          {
                                              "fieldname": field.fieldname,
                                              "label": field.label,
                                              "fieldtype": field.fieldtype,
                                              "reqd": field.reqd,
                                              "options": field.options
                                          }
                                          for field in fields
                                          if not field.hidden and field.fieldtype not in ["Section Break", "Column Break", "Tab Break"]
                                      ]
                                  }
                              ]
                          }
                      ]
                  }
              ]
          })
            field_layout.insert(ignore_if_duplicate=True)
            frappe.db.commit()
            
        except Exception as e:
            frappe.log_error(f"Error creating field layout for {doctype_name}: {str(e)}")
            frappe.throw(str(e))

    def add_telemetry(self, doctype_name):
        """Add telemetry tracking for the doctype"""
        try:
            # Skip telemetry if CRM Telemetry Event doctype doesn't exist
            if not frappe.db.exists("DocType", "CRM Telemetry Event"):
                print(f"Skipping telemetry for {doctype_name} as CRM Telemetry Event doctype doesn't exist")
                return
                
            # Add telemetry events to tracking system
            events = [
                f"{doctype_name.lower()}_created",
                f"{doctype_name.lower()}_updated",
                f"{doctype_name.lower()}_deleted",
                f"{doctype_name.lower()}_viewed"
            ]
            
            for event in events:
                if not frappe.db.exists("CRM Telemetry Event", event):
                    try:
                        frappe.get_doc({
                            "doctype": "CRM Telemetry Event",
                            "event_name": event,
                            "description": f"Track {event.replace('_', ' ')}"
                        }).insert()
                    except Exception as e:
                        print(f"Warning: Could not create telemetry event {event}: {str(e)}")
                        continue
            
            frappe.db.commit()
            
        except Exception as e:
            print(f"Warning: Error adding telemetry for {doctype_name}: {str(e)}")
            # Don't throw error, just log warning and continue
            pass

    def create_tests(self, doctype_name):
        """Create test files for the doctype"""
        test_name = f"{doctype_name.lower()}.test.js"
        test_file = os.path.join(self.tests_path, test_name)
        
        if os.path.exists(test_file):
            frappe.msgprint(_("Tests for {0} already exist").format(doctype_name))
            return
            
        os.makedirs(os.path.dirname(test_file), exist_ok=True)
        
        test_template = f"""import {{ mount }} from '@vue/test-utils'
import {{ describe, it, expect, beforeEach, vi }} from 'vitest'
import {self.pascal_case(doctype_name)}s from '@/pages/{self.pascal_case(doctype_name)}s.vue'
import {{ use{self.pascal_case(doctype_name)}Store }} from '@/stores/{doctype_name.lower()}'

describe('{doctype_name} Component', () => {{
    let wrapper
    let store
    
    beforeEach(() => {{
        store = use{self.pascal_case(doctype_name)}Store()
        wrapper = mount({self.pascal_case(doctype_name)}s, {{
            global: {{
                plugins: [store],
                stubs: {{
                    'router-link': true,
                    'router-view': true
                }}
            }}
        }})
    }})
    
    it('renders properly', () => {{
        expect(wrapper.exists()).toBe(true)
    }})
    
    it('shows create button', () => {{
        const createButton = wrapper.find('button[aria-label="Create"]')
        expect(createButton.exists()).toBe(true)
    }})
    
    it('opens modal on create click', async () => {{
        const createButton = wrapper.find('button[aria-label="Create"]')
        await createButton.trigger('click')
        expect(wrapper.vm.show{self.pascal_case(doctype_name)}Modal).toBe(true)
    }})
    
    # Add more tests as needed
}})
"""
        with open(test_file, "w") as f:
            f.write(test_template)

    def create_page(self, doctype_name):
        """Create a page component for the doctype"""
        page_name = f"{self.pascal_case(doctype_name)}s.vue"
        page_file = os.path.join(self.pages_path, page_name)
        
        if os.path.exists(page_file):
            frappe.msgprint(_("List page for {0} already exists").format(doctype_name))
            return
        
        os.makedirs(os.path.dirname(page_file), exist_ok=True)
            
        icon_name = f"{self.pascal_case(doctype_name)}Icon"
        list_view_name = f"{self.pascal_case(doctype_name)}ListView"
        modal_name = f"{self.pascal_case(doctype_name)}Modal"
        
        page_template = f"""<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="{self.pascal_case(doctype_name)}s" />
    </template>
    <template #right-header>
      <Button variant="solid" :label="__('Create')" @click="show{self.pascal_case(doctype_name)}Modal = true">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </template>
  </LayoutHeader>
  <ViewControls
    ref="viewControls"
    v-model="{doctype_name.lower()}s"
    doctype="{doctype_name}"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
  />
  <{list_view_name}
    v-if="{doctype_name.lower()}s.data && rows.length"
    :rows="rows"
    :columns="{doctype_name.lower()}s.data.columns"
    :options="{{
      showTooltip: false,
      resizeColumn: true,
      rowCount: {doctype_name.lower()}s.data.row_count,
      totalCount: {doctype_name.lower()}s.data.total_count,
    }}"
    @loadMore="() => loadMore++"
    @columnWidthUpdated="() => triggerResize++"
    @updatePageCount="(count) => (updatedPageCount = count)"
    @applyFilter="(data) => viewControls.applyFilter(data)"
    @applyLikeFilter="(data) => viewControls.applyLikeFilter(data)"
    @likeDoc="(data) => viewControls.likeDoc(data)"
    @selectionsChanged="(selections) => viewControls.updateSelections(selections)"
  />
  <div v-else-if="{doctype_name.lower()}s.data" class="flex h-full items-center justify-center">
    <div class="flex flex-col items-center gap-3 text-xl font-medium text-ink-gray-4">
      <{icon_name} class="h-10 w-10" />
      <span>{{ __('No {{0}} Found', [__('{self.pascal_case(doctype_name)}s')]) }}</span>
      <Button :label="__('Create')" @click="show{self.pascal_case(doctype_name)}Modal = true">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </div>
  </div>
  <{modal_name} v-model="show{self.pascal_case(doctype_name)}Modal" :{doctype_name.lower()}="{{}}" doctype="{doctype_name}" />
  <QuickEntryModal v-if="showQuickEntryModal" v-model="showQuickEntryModal" doctype="{doctype_name}" />
</template>

<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import {icon_name} from '@/components/Icons/{icon_name}.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import {modal_name} from '@/components/Modals/{modal_name}.vue'
import QuickEntryModal from '@/components/Modals/QuickEntryModal.vue'
import {list_view_name} from '@/components/ListViews/{list_view_name}.vue'
import ViewControls from '@/components/ViewControls.vue'
import {{ Button }} from 'frappe-ui'
import {{ ref, computed }} from 'vue'

const show{self.pascal_case(doctype_name)}Modal = ref(false)
const showQuickEntryModal = ref(false)
const {doctype_name.lower()}s = ref({{}})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

const rows = computed(() => {{
  if (!{doctype_name.lower()}s.value?.data?.data || !['list', 'group_by'].includes({doctype_name.lower()}s.value.data.view_type)) return []
  return {doctype_name.lower()}s.value.data.data.map((item) => {{
    return {{ name: item.name, ...item }}
  }})
}})
</script>
"""
        with open(page_file, "w") as f:
            f.write(page_template)
            
    def create_detail_page(self, doctype_name):
        """Create a detail page component for the doctype"""
        detail_page_name = f"{self.pascal_case(doctype_name)}.vue"
        detail_page_file = os.path.join(self.pages_path, detail_page_name)
        
        if os.path.exists(detail_page_file):
            frappe.msgprint(_("Detail page for {0} already exists").format(doctype_name))
            return
            
        os.makedirs(os.path.dirname(detail_page_file), exist_ok=True)
        
        icon_name = f"{self.pascal_case(doctype_name)}Icon"
        
        detail_page_template = f"""<template>
  <div class="flex h-full flex-col">
    <LayoutHeader>
      <template #left-header>
        <div class="flex items-center gap-2">
          <Button
            variant="ghost"
            class="-ml-2"
            @click="router.back()"
          >
            <template #prefix>
              <FeatherIcon name="arrow-left" class="h-4" />
            </template>
          </Button>
          <h1 class="text-xl font-medium">
            {{ {self.camel_case(doctype_name)}.name || '' }}
          </h1>
      </div>
    </template>
      <template #right-header>
        <Button
          variant="ghost"
          @click="editDoc()"
        >
          <template #prefix>
            <FeatherIcon name="edit" class="h-4" />
          </template>
          {{ __('Edit') }}
        </Button>
      </template>
    </LayoutHeader>
    <div v-if="loading" class="flex h-full items-center justify-center">
      <LoadingIndicator />
    </div>
    <div v-else-if="{self.camel_case(doctype_name)}" class="flex-1 overflow-auto p-4">
      <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div v-for="field in fields" :key="field.fieldname" class="flex flex-col">
          <label class="text-sm font-medium text-gray-500">{{ __(field.label) }}</label>
          <div class="mt-1">
            <div v-if="field.fieldtype === 'Data' || field.fieldtype === 'Small Text'">
              {{ {self.camel_case(doctype_name)}[field.fieldname] || '-' }}
          </div>
            <div v-else-if="field.fieldtype === 'Text Editor' || field.fieldtype === 'Long Text'">
              <div v-html="{self.camel_case(doctype_name)}[field.fieldname] || '-'"></div>
        </div>
            <div v-else-if="field.fieldtype === 'Date'">
              {{ formatDate({self.camel_case(doctype_name)}[field.fieldname]) || '-' }}
          </div>
            <div v-else-if="field.fieldtype === 'Datetime'">
              {{ formatDateTime({self.camel_case(doctype_name)}[field.fieldname]) || '-' }}
        </div>
            <div v-else-if="field.fieldtype === 'Currency'">
              {{ formatCurrency({self.camel_case(doctype_name)}[field.fieldname]) || '-' }}
      </div>
            <div v-else-if="field.fieldtype === 'Check'">
              <input type="checkbox" :checked="{self.camel_case(doctype_name)}[field.fieldname]" disabled />
            </div>
            <div v-else>
              {{ {self.camel_case(doctype_name)}[field.fieldname] || '-' }}
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-else class="flex h-full items-center justify-center">
      <div class="text-center">
        <{icon_name} class="mx-auto h-12 w-12 text-gray-400" />
        <h3 class="mt-2 text-sm font-medium text-gray-900">{{ __('No {self.pascal_case(doctype_name)} Found') }}</h3>
        <p class="mt-1 text-sm text-gray-500">{{ __('The {self.pascal_case(doctype_name)} you are looking for does not exist.') }}</p>
        <div class="mt-6">
          <Button
            variant="solid"
            :label="__('Go Back')"
            @click="router.back()"
          >
            <template #prefix><FeatherIcon name="arrow-left" class="h-4" /></template>
          </Button>
        </div>
      </div>
    </div>
    <QuickEntryModal
      v-if="showEditModal"
      v-model="showEditModal"
      doctype="{doctype_name}"
      :doc="{self.camel_case(doctype_name)}"
      @save="fetchData"
    />
      </div>
</template>

<script setup>
import {{ ref, onMounted, computed }} from 'vue'
import {{ useRouter, useRoute }} from 'vue-router'
import LayoutHeader from '@/components/LayoutHeader.vue'
import QuickEntryModal from '@/components/Modals/QuickEntryModal.vue'
import {icon_name} from '@/components/Icons/{icon_name}.vue'
import {{ formatDate, formatDateTime, formatCurrency }} from '@/utils'
import {{ fetchDoc, getDoctype }} from '@/api/{self.kebab_case(doctype_name)}'

const router = useRouter()
const route = useRoute()
const {self.camel_case(doctype_name)} = ref(null)
const loading = ref(true)
const showEditModal = ref(false)
const fields = ref([])

onMounted(async () => {{
  await fetchData()
  await loadFields()
}})

async function fetchData() {{
  loading.value = true
  try {{
    const response = await fetchDoc(route.params.itemId)
    {self.camel_case(doctype_name)}.value = response
  }} catch (error) {{
    console.error('Error fetching {doctype_name}:', error)
  }} finally {{
    loading.value = false
  }}
}}

async function loadFields() {{
  try {{
    const doctype = await getDoctype()
    fields.value = doctype.fields.filter(
      (field) => !['Section Break', 'Column Break', 'Tab Break'].includes(field.fieldtype)
    )
  }} catch (error) {{
    console.error('Error loading fields:', error)
  }}
}}

function editDoc() {{
  showEditModal.value = true
}}
</script>
"""
        with open(detail_page_file, "w") as f:
            f.write(detail_page_template)

    def create_mobile_view(self, doctype_name):
        """Create a mobile view component for the doctype"""
        mobile_name = f"{self.pascal_case(doctype_name)}Mobile"
        mobile_file = os.path.join(self.pages_path, f"{mobile_name}.vue")
        
        if os.path.exists(mobile_file):
            frappe.msgprint(_("Mobile view for {0} already exists").format(doctype_name))
            return
            
        os.makedirs(os.path.dirname(mobile_file), exist_ok=True)
        
        mobile_template = f"""<template>
  <div class="flex h-full flex-col">
    <LayoutHeader>
      <template #left-header>
        <div class="flex items-center gap-2">
          <Button
            variant="ghost"
            class="-ml-2"
            @click="router.back()"
          >
            <template #prefix>
              <FeatherIcon name="arrow-left" class="h-4" />
            </template>
          </Button>
          <h1 class="text-xl font-medium">
            {{ {self.camel_case(doctype_name)}.name || '' }}
          </h1>
        </div>
      </template>
      <template #right-header>
        <Button
          variant="ghost"
          @click="editDoc()"
        >
          <template #prefix>
            <FeatherIcon name="edit" class="h-4" />
          </template>
          {{ __('Edit') }}
        </Button>
      </template>
    </LayoutHeader>
    <div v-if="loading" class="flex h-full items-center justify-center">
      <LoadingIndicator />
    </div>
    <div v-else-if="{self.camel_case(doctype_name)}" class="flex-1 overflow-auto p-4">
      <div class="space-y-4">
        <div v-for="field in fields" :key="field.fieldname" class="flex flex-col">
          <label class="text-sm font-medium text-gray-500">{{ __(field.label) }}</label>
          <div class="mt-1">
            <div v-if="field.fieldtype === 'Data' || field.fieldtype === 'Small Text'">
              {{ {self.camel_case(doctype_name)}[field.fieldname] || '-' }}
            </div>
            <div v-else-if="field.fieldtype === 'Text Editor' || field.fieldtype === 'Long Text'">
              <div v-html="{self.camel_case(doctype_name)}[field.fieldname] || '-'"></div>
            </div>
            <div v-else-if="field.fieldtype === 'Date'">
              {{ formatDate({self.camel_case(doctype_name)}[field.fieldname]) || '-' }}
            </div>
            <div v-else-if="field.fieldtype === 'Datetime'">
              {{ formatDateTime({self.camel_case(doctype_name)}[field.fieldname]) || '-' }}
            </div>
            <div v-else-if="field.fieldtype === 'Currency'">
              {{ formatCurrency({self.camel_case(doctype_name)}[field.fieldname]) || '-' }}
            </div>
            <div v-else-if="field.fieldtype === 'Check'">
              <input type="checkbox" :checked="{self.camel_case(doctype_name)}[field.fieldname]" disabled />
            </div>
            <div v-else>
              {{ {self.camel_case(doctype_name)}[field.fieldname] || '-' }}
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-else class="flex h-full items-center justify-center">
      <div class="text-center">
        <{self.pascal_case(doctype_name)}Icon class="mx-auto h-12 w-12 text-gray-400" />
        <h3 class="mt-2 text-sm font-medium text-gray-900">{{ __('No {self.pascal_case(doctype_name)} Found') }}</h3>
        <p class="mt-1 text-sm text-gray-500">{{ __('The {self.pascal_case(doctype_name)} you are looking for does not exist.') }}</p>
        <div class="mt-6">
          <Button
            variant="solid"
            :label="__('Go Back')"
            @click="router.back()"
          >
            <template #prefix><FeatherIcon name="arrow-left" class="h-4" /></template>
          </Button>
        </div>
      </div>
    </div>
    <QuickEntryModal
      v-if="showEditModal"
      v-model="showEditModal"
      doctype="{doctype_name}"
      :doc="{self.camel_case(doctype_name)}"
      @save="fetchData"
    />
  </div>
</template>

<script setup>
import {{ ref, onMounted }} from 'vue'
import {{ useRouter, useRoute }} from 'vue-router'
import LayoutHeader from '@/components/LayoutHeader.vue'
import QuickEntryModal from '@/components/Modals/QuickEntryModal.vue'
import {self.pascal_case(doctype_name)}Icon from '@/components/Icons/{self.pascal_case(doctype_name)}Icon.vue'
import {{ formatDate, formatDateTime, formatCurrency }} from '@/utils'
import {{ fetchDoc, getDoctype }} from '@/api/{self.kebab_case(doctype_name)}'

const router = useRouter()
const route = useRoute()
const {self.camel_case(doctype_name)} = ref(null)
const loading = ref(true)
const showEditModal = ref(false)
const fields = ref([])

onMounted(async () => {{
  await fetchData()
  await loadFields()
}})

async function fetchData() {{
  loading.value = true
  try {{
    const response = await fetchDoc(route.params.itemId)
    {self.camel_case(doctype_name)}.value = response
  }} catch (error) {{
    console.error('Error fetching {doctype_name}:', error)
  }} finally {{
    loading.value = false
  }}
}}

async function loadFields() {{
  try {{
    const doctype = await getDoctype()
    fields.value = doctype.fields.filter(
      (field) => !['Section Break', 'Column Break', 'Tab Break'].includes(field.fieldtype)
    )
  }} catch (error) {{
    console.error('Error loading fields:', error)
  }}
}}

function editDoc() {{
  showEditModal.value = true
}}
</script>
"""
        with open(mobile_file, "w") as f:
            f.write(mobile_template)

    def update_router(self, doctype_name):
        """Update the router.js file to include the new doctype"""
        router_file = os.path.join(self.src_path, "router.js")
        
        if not os.path.exists(router_file):
            frappe.msgprint(_("Router file not found at {0}").format(router_file))
            return False
            
        with open(router_file, "r") as f:
            content = f.read()
            
        pascal_doctype = self.pascal_case(doctype_name)
        kebab_doctype = self.kebab_case(doctype_name)
        
        possible_routes = [
            f"path: '/{kebab_doctype}s'",
            f"path: '/{kebab_doctype}'",
            f"alias: '/{kebab_doctype}s'",
            f"name: '{pascal_doctype}s'",
            f"name: '{pascal_doctype}'",
        ]
        
        for pattern in possible_routes:
            if pattern in content:
                print(f"DEBUG: Found existing route with pattern: {pattern}")
                frappe.msgprint(_("Route for {0} already exists").format(doctype_name))
                return False
                
        routes_start = content.find("const routes = [")
        if routes_start == -1:
            frappe.msgprint(_("Could not find routes array in router file"))
            return False
            
        routes_end = content.find("]", routes_start)
        if routes_end == -1:
            frappe.msgprint(_("Could not find end of routes array in router file"))
            return False
        
        new_routes = f"""  {{
    alias: '/{kebab_doctype}s',
    path: '/{kebab_doctype}s/view/:viewType?',
    name: '{pascal_doctype}s',
    component: () => import('@/pages/{pascal_doctype}s.vue'),
  }},
  {{
    path: '/{kebab_doctype}s/:itemId',
    name: '{pascal_doctype}',
    component: () => import(`@/pages/${{handleMobileView('{pascal_doctype}')}}.vue`),
    props: true,
  }},"""
        
        invalid_page_index = content.find("path: '/:invalidpath'", routes_start, routes_end)
        if invalid_page_index != -1:
            invalid_page_start = content.rfind("{", routes_start, invalid_page_index)
            updated_content = content[:invalid_page_start] + new_routes + "\n  " + content[invalid_page_start:]
            
            with open(router_file, "w") as f:
                f.write(updated_content)
                
        return True

    def update_sidebar(self, doctype_name):
        """Update the sidebar to include the new doctype"""
        sidebar_file = os.path.join(self.components_path, "Layouts", "AppSidebar.vue")
        
        if not os.path.exists(sidebar_file):
            frappe.msgprint(_("Sidebar file not found at {0}").format(sidebar_file))
            return False
            
        with open(sidebar_file, "r") as f:
            content = f.read()
            
        pascal_doctype = self.pascal_case(doctype_name)
        kebab_doctype = self.kebab_case(doctype_name)
        
        # Check if the doctype is already in the sidebar
        if f"label: '{pascal_doctype}s'" in content or f"label: '{doctype_name}s'" in content:
            print(f"DEBUG: Doctype {doctype_name} already exists in sidebar")
            return False
            
        # Add the icon import if it doesn't exist
        icon_import = f"import {pascal_doctype}Icon from '@/components/Icons/{pascal_doctype}Icon.vue'"
        if icon_import not in content:
            # Find the last import statement
            last_import = content.rfind("import ")
            if last_import != -1:
                # Find the end of that import line
                import_end = content.find("\n", last_import)
                if import_end != -1:
                    # Insert our import after the last import
                    content = content[:import_end+1] + icon_import + "\n" + content[import_end+1:]
        
        # Find the links array
        links_start = content.find("const links = [")
        if links_start == -1:
            print("DEBUG: Could not find links array in sidebar")
            return False
            
        # Add the new doctype link
        new_link = f"""  {{
    label: '{pascal_doctype}s',
    icon: {pascal_doctype}Icon,
    to: '{pascal_doctype}s',
    badge: () => useCounts('{doctype_name}'),
  }},"""
        
        # Find a good place to insert the new link - after Customers or Organizations
        insert_after = None
        for label in ["Customers", "Organizations"]:
            label_pos = content.find(f"label: '{label}'", links_start)
            if label_pos != -1:
                # Find the end of this item
                item_end = content.find("},", label_pos)
                if item_end != -1:
                    insert_after = item_end + 2
                    break
        
        if insert_after is None:
            # If we couldn't find a good place, insert at the end of the links array
            links_end = content.find("]", links_start)
            if links_end == -1:
                print("DEBUG: Could not find end of links array")
                return False
            insert_after = links_end
        
        # Insert the new link
        content = content[:insert_after] + "\n" + new_link + content[insert_after:]
        
        # Write the updated content back to the file
        with open(sidebar_file, "w") as f:
            f.write(content)
            
        print(f"DEBUG: Successfully added {doctype_name} to sidebar")
        return True

    def integrate_other_apps(self):
        """Integrate with other apps"""
        sidebar_file = os.path.join(self.components_path, "Layouts", "AppSidebar.vue")
        
        if not os.path.exists(sidebar_file):
            frappe.msgprint(_("Sidebar file not found at {0}").format(sidebar_file))
            return
            
        with open(sidebar_file, "r") as f:
            content = f.read()
            
        if "Integrations" in content:
            return

    
        all_views_start = content.find("const allViews = computed(() => {")
        all_views_end = content.find("return _views", all_views_start)
        
        integrations_view = """
    // Add integrations section
    _views.push({
      name: 'Integrations',
      opened: true,
      views: [
        {
          label: 'Helpdesk',
          icon: h('div', { class: 'size-auto' }, '🎧'),
          to: { path: '/app/helpdesk' },
        },
        {
          label: 'Gameplan',
          icon: h('div', { class: 'size-auto' }, '🎮'),
          to: { path: '/app/gameplan' },
        },
        {
          label: 'Wiki',
          icon: h('div', { class: 'size-auto' }, '📚'),
          to: { path: '/app/wiki' },
        },
      ],
    })
    """
        
        updated_content = content[:all_views_end] + integrations_view + content[all_views_end:]
        
        with open(sidebar_file, "w") as f:
            f.write(updated_content)

    def create_frontend_api(self, doctype_name):
        """Create frontend API file for the doctype"""
        api_name = f"{doctype_name.lower()}.js"
        api_file = os.path.join(self.api_path, api_name)
        
        if os.path.exists(api_file):
            frappe.msgprint(_("Frontend API for {0} already exists").format(doctype_name))
            return
            
        os.makedirs(os.path.dirname(api_file), exist_ok=True)
        
        api_template = f"""import {{ createResource }} from 'frappe-ui'

export function fetchDoc(name) {{
    return createResource({{
        url: 'crm.api.{doctype_name.lower()}.get_{doctype_name.lower()}',
        params: {{ name }},
        cache: ['{doctype_name.lower()}', name],
        auto: true
    }})
}}

export function fetchList(filters = {{}}, fields = null, orderBy = null, limit = null, start = null) {{
    return createResource({{
        url: 'crm.api.{doctype_name.lower()}.get_{doctype_name.lower()}_list',
        params: {{ filters, fields, order_by: orderBy, limit, start }},
        cache: ['{doctype_name.lower()}_list', filters, fields, orderBy, limit, start],
        auto: true
    }})
}}

export function createDoc(doc) {{
    return createResource({{
        url: 'crm.api.{doctype_name.lower()}.create_{doctype_name.lower()}',
        params: {{ doc: JSON.stringify(doc) }},
        cache: ['{doctype_name.lower()}_list'],
        auto: true
    }})
}}

export function updateDoc(name, field, value) {{
    return createResource({{
        url: 'crm.api.{doctype_name.lower()}.update_{doctype_name.lower()}',
        params: {{ name, field, value }},
        cache: ['{doctype_name.lower()}', name],
        auto: true
    }})
}}

export function deleteDoc(name) {{
    return createResource({{
        url: 'crm.api.{doctype_name.lower()}.delete_{doctype_name.lower()}',
        params: {{ name }},
        cache: ['{doctype_name.lower()}_list'],
        auto: true
    }})
}}

export function getDoctype() {{
    return createResource({{
        url: 'frappe.client.get',
        params: {{ doctype: '{doctype_name}' }},
        cache: ['doctype', '{doctype_name}'],
        auto: true
    }})
}}

export function getQuickEntryFields() {{
    return createResource({{
        url: 'crm.fcrm.doctype.{doctype_name.lower()}.{doctype_name.lower()}.get_quick_entry_fields',
        cache: ['quick_entry_fields', '{doctype_name}'],
        auto: true
    }})
}}

export function getRequiredFields() {{
    return createResource({{
        url: 'crm.fcrm.doctype.{doctype_name.lower()}.{doctype_name.lower()}.get_required_fields',
        cache: ['required_fields', '{doctype_name}'],
        auto: true
    }})
}}
"""
        with open(api_file, "w") as f:
            f.write(api_template)
        print(f"Created frontend API file at {api_file}")

@frappe.whitelist()
def integrate_other_apps():
    """Integrate with other apps"""
    generator = CRMUIGenerator()
    generator.integrate_other_apps()
