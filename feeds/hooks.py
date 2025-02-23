from . import __version__ as app_version

app_name = "feeds"
app_title = "Feeds"
app_publisher = "254 ERP"
app_description = "Frappe App for Animal Feeds"
app_email = "254businessservices@gmail.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/feeds/css/feeds.css"
# app_include_js = "/assets/feeds/js/feeds.js"

# include js, css files in header of web template
# web_include_css = "/assets/feeds/css/feeds.css"
# web_include_js = "/assets/feeds/js/feeds.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "feeds/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
page_js = {
    # "page" : "public/js/file.js",
    "point-of-sale": "public/js/point_of_sale.js",
    # "point-of-sale": "feeds/public/js/point_of_sale.js",
}

# include js in doctype views
doctype_js = {
    "Sales Invoice" : "public/js/sales_invoice.js",
    "Sales Order" : "public/js/sales_order.js",
    "Payment Entry": "public/js/payment_entry.js",
    "BOM": "public/js/bom.js"
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
#	"methods": "feeds.utils.jinja_methods",
#	"filters": "feeds.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "feeds.install.before_install"
# after_install = "feeds.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "feeds.uninstall.before_uninstall"
# after_uninstall = "feeds.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "feeds.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
#	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Product Bundle": {
        "before_save": "feeds.custom_methods.product_bundle.before_save_func"
    },
    "Item": {
        "before_save": "feeds.custom_methods.item.before_save"
    },
    "BOM": {
        "before_save": "feeds.custom_methods.bom.before_save"
    },
    "Sales Invoice": {
        "before_save": "feeds.custom_methods.sales_invoice.before_save"
    },
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
#	"all": [
#		"feeds.tasks.all"
#	],
#	"daily": [
#		"feeds.tasks.daily"
#	],
#	"hourly": [
#		"feeds.tasks.hourly"
#	],
#	"weekly": [
#		"feeds.tasks.weekly"
#	],
#	"monthly": [
#		"feeds.tasks.monthly"
#	],
# }

# Testing
# -------

# before_tests = "feeds.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "feeds.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "feeds.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]


# User Data Protection
# --------------------

# user_data_fields = [
#	{
#		"doctype": "{doctype_1}",
#		"filter_by": "{filter_by}",
#		"redact_fields": ["{field_1}", "{field_2}"],
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_2}",
#		"filter_by": "{filter_by}",
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_3}",
#		"strict": False,
#	},
#	{
#		"doctype": "{doctype_4}"
#	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"feeds.auth.validate"
# ]
