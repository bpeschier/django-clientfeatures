django-clientfeatures
=====================

Detects client features from javascript and exposes the information in the
request/response cycle and templates contexts.

Installation
------------

To get started using ``django-clientfeatures`` simply install it with
``pip``::

    $ pip install git@github.com:bpeschier/django-clientfeatures.git


Configuration
-------------

Add ``"clientfeatures.apps.DeviceFeaturesAppConfig"`` to your project's
``INSTALLED_APPS`` setting (``"clientfeatures"`` on Django 1.6) and
``"clientfeatures.middleware.DetectFeaturesMiddleware"`` to your
``MIDDLEWARE_CLASSES`` setting for the default detection. For template 
context support, add ``"clientfeatures.context_processors.client_features"``
to the list of ``CONTEXT_PREPROCESSORS``.

How it works / rationale
------------------------

``clientfeatures`` is intended to identify what features are available on the
client which are not always directly identifiable from HTTP  headers: the
screen density, size and which method of input is used. For this, it detects
the features in javascript at the beginning of the session and stores it on
a cookie.

A cookie is set with the ``devicePixelRatio``, screen size and touch
capabilities reported by the browser. This data is converted into a dictionary
of features to be used within the request/response cycle.

The blatant downside is that all new sessions will have one extra (all be it
very small) request with the accompanying round-trip time, which can be
significant on mobile. The upside is that this overhead occurs only once and
the resulting cookie can be used for varying the cache of the different
responses. The served page is going to be the correct one for the device
requesting it with no additional overhead (assuming you load specific assets
for the client instead of general-purpose ones).

The detection page will distort normal referral information from the browser,
and the detection javascript will save the original referrer for you.

Detected features
-----------------

The ``DetectFeaturesMiddleware`` adds a ``client_features`` dictionary to all
`request` objects. By default it consists of the following items:

screen_density
    Either `default` or `retina`.

screen_size
    Either `default` or `mobile`.

input
    Either `pointer` or `touch`.

When the template context preprocessor is configured, it wil expose the same
dictionary as `client_features`.

Extending or overriding detection
---------------------------------

The ``DetectFeaturesMiddleware`` is set-up to allow developers to hook in at
any point of the detection, from naming the cookies and their expiration date
to the actual detection and features dictionary exposed.

In such, the middleware acts a mechanism to detect new clients and figure out
their capabilities so Django can adapt its response so it does not have to be
done in the browser. One can easily add detection of new features, like which
doctypes are supported, or adjust the screen size detection to have more 
fine-grained steps such as `mobile`, `tablet`, `small_screen`, `large_screen`
and `tv`.

The job of detecting features on the client is done by the
``features/detect_javascript.html`` template, while the conversion into usable
items is done by `extract_features_from_detection` in 
``DetectFeaturesMiddleware``.

Loading feature-specific static files
-------------------------------------

The ``feature_tags`` template tag library overrides the default ``static``
template tag and accepts string format parameters for features in the
``client_features`` dictionary, for example::

    {% static "css/screen-{input}.css" %}

This will result in `css/screen-pointer.css` for pointer-based devices like
desktop computers and `css/screen-touch.css` for touch-based devices like
tablets.

The ``feature_tags`` template tag library requires the context preprocessor 
to be added to your ``CONTEXT_PREPROCESSORS`` setting.

Crawlers and low-tech clients
-----------------------------

Devices without javascript will be diverted to the "default" setting, which is
a normal pointer-operated client. This is done with a meta-refresh.

Crawlers and other clients can be exempted from the entire detection based on
their User agent string. These clients will also be given the default profile, 
but will never see the detection page. These clients are defined in the
``featureless_agents`` property of the ``DetectFeaturesMiddleware``.