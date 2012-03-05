from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^asset', 'jevons.root.views.asset'),
    url(r'^stream', 'jevons.root.views.stream'),
    url(r'^edit_asset', 'jevons.root.views.edit_asset'),
    url(r'^bglobal_importer', 'jevons.root.views.bglobal_importer'),
    url(r'^3', 'jevons.root.views.add_sub_asset'),
    url(r'^add_stream', 'jevons.root.views.add_stream'),
    url(r'^4', 'jevons.root.views.delete_asset'),
    url(r'^csv_import', 'jevons.root.views.csv_import'),
    url(r'^$', 'jevons.root.views.home'),
    url(r'^add_advance', 'jevons.root.views.add_advance'),
    # Examples:
    # url(r'^$', 'jevons.views.home', name='home'),
    # url(r'^jevons/', include('jevons.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
