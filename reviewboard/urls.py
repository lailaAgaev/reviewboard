from django.conf import settings
from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin

from reviewboard.reviews.feeds import RssReviewsFeed, AtomReviewsFeed, \
                                      RssSubmitterReviewsFeed, \
                                      AtomSubmitterReviewsFeed, \
                                      RssGroupReviewsFeed, \
                                      AtomGroupReviewsFeed
from reviewboard import initialize


initialize()

# Load in all the models for the admin UI.
if not admin.site._registry:
    admin.autodiscover()


# URLs global to all modes
urlpatterns = patterns('',
    (r'^admin/', include('reviewboard.admin.urls')),
)

# Add static media if running in DEBUG mode
if settings.DEBUG or getattr(settings, 'RUNNING_TEST', False):
    urlpatterns += patterns('django.views.static',
        (r'^media/(?P<path>.*)$', 'serve', {
            'show_indexes': True,
            'document_root': settings.MEDIA_ROOT,
            'insecure': True,
            }),
    )

rss_feeds = {
    'r': RssReviewsFeed,
    'users': RssSubmitterReviewsFeed,
    'groups': RssGroupReviewsFeed,
}


atom_feeds = {
    'r': AtomReviewsFeed,
    'users': AtomSubmitterReviewsFeed,
    'groups': AtomGroupReviewsFeed,
}


# Main includes
urlpatterns += patterns('',
    (r'^account/', include('reviewboard.accounts.urls')),
    (r'^(s/(?P<local_site_name>[A-Za-z0-9\-_.]+)/)?api/',
     include('reviewboard.webapi.urls')),
    (r'^(s/(?P<local_site_name>[A-Za-z0-9\-_.]+)/)?r/',
     include('reviewboard.reviews.urls')),
    (r'^reports/', include('reviewboard.reports.urls')),
)


# reviewboard.reviews.views
urlpatterns += patterns('reviewboard.reviews.views',
    # Review request browsing
    url(r'^(s/(?P<local_site_name>[A-Za-z0-9\-_.]+)/)?dashboard/$',
        'dashboard', name="dashboard"),

    # Users
    url(r'^(s/(?P<local_site_name>[A-Za-z0-9\-_.]+)/)?users/$',
        'submitter_list', name="all-users"),
    url(r'^(s/(?P<local_site_name>[A-Za-z0-9\-_.]+)/)?users/(?P<username>[A-Za-z0-9@_\-\.]+)/$',
        'submitter', name="user"),

    # Groups
    url(r'^(s/(?P<local_site_name>[A-Za-z0-9\-_.]+)/)?groups/$',
        'group_list', name="all-groups"),
    url(r'^(s/(?P<local_site_name>[A-Za-z0-9\-_.]+)/)?groups/(?P<name>[A-Za-z0-9_-]+)/$',
        'group', name="group"),
    url(r'^(s/(?P<local_site_name>[A-Za-z0-9\-_.]+)/)?groups/(?P<name>[A-Za-z0-9_-]+)/members/$',
        'group_members', name="group_members"),
)


# django.contrib
urlpatterns += patterns('django.contrib',
   # Feeds
    url(r'^feeds/rss/(?P<url>.*)/$', 'syndication.views.feed',
        {'feed_dict': rss_feeds}, name="rss-feed"),
    url(r'^feeds/atom/(?P<url>.*)/$', 'syndication.views.feed',
        {'feed_dict': atom_feeds}, name="atom-feed"),
    url(r'^account/logout/$', 'auth.views.logout',
        {'next_page': settings.LOGIN_URL}, name="logout")
)


# And the rest ...
urlpatterns += patterns('',
    url(r'^$', 'django.views.generic.simple.redirect_to',
        {'url': 'dashboard/'}, name="root"),

    # This must be last.
    url(r'^iphone/', include('reviewboard.iphone.urls', namespace='iphone')),
)
