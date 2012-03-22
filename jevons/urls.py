from django.conf.urls.defaults import patterns, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^show_asset', 'jevons.root.views.show_asset'),
    url(r'^update_asset', 'jevons.root.views.update_asset'),
    url(r'^add_asset', 'jevons.root.views.add_asset'),
    url(r'^delete_asset', 'jevons.root.views.delete_asset'),
    url(r'^csv_import', 'jevons.root.views.csv_import'),
    url(r'^$', 'jevons.root.views.home'),
    url(r'^add_advance', 'jevons.root.views.add_advance'),
    url(r'^show_advance', 'jevons.root.views.show_advance'),
    url(r'^update_advance', 'jevons.root.views.update_advance'),
    url(r'^update_importer', 'jevons.root.views.update_importer'),
    url(r'^delete_advance', 'jevons.root.views.delete_advance'),
    url(r'^add_importer', 'jevons.root.views.add_importer'),
    url(r'^show_importer', 'jevons.root.views.show_importer'),
    # Examples:
    # url(r'^$', 'jevons.views.home', name='home'),
    # url(r'^jevons/', include('jevons.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
