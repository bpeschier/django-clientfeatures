from copy import copy
from datetime import datetime, timedelta

from django.conf import settings
from django.shortcuts import render


class DetectFeaturesMiddleware:
    feature_cookie_name = '_df'
    feature_cookie_expires = timedelta(weeks=52)
    referrer_cookie_name = '_ref'
    detection_cookie_name = '_detect'
    override_parameter = 'df'
    default_features_query = '?default'

    default_screen_density = 1.0
    default_screen_size = (1024, 768)
    default_is_touch = False

    featureless_agents = (
        'Googlebot',
        'facebookexternalhit',
        'LinkedInBot',
        'TwitterBot',
    )
    ignored_path_prefixes = (
        settings.MEDIA_URL,
        settings.STATIC_URL,
        '/robots.txt',
    )
    template_name = 'features/detect.html'

    def process_request(self, request):
        request.client_features = None
        if not self.should_skip_detection(request):
            features = self.get_features(request)

            # Check override
            override = request.GET.get(self.get_override_parameter())
            if override is not None:
                features = self.override(override)

            if features is None and not self.should_skip_detection(request):
                return self.render_detect_page(request)
            else:
                features = features or self.get_default_features()
                request.client_features = features

    def process_response(self, request, response):
        if (self.get_feature_cookie_name() not in request.COOKIES and
                hasattr(request, 'client_features') and request.client_features is not None):
            self.set_features_cookie(request, response, features=request.client_features)

        return response

    def render_detect_page(self, request):
        return render(request, self.template_name, {
            'cookie_name': self.get_detection_cookie_name(),
            'referrer_cookie_name': self.get_referrer_cookie_name(),
            'default_path': self.get_default_path(request)
        })

    def get_features(self, request):
        detection_cookie = request.COOKIES.get(self.get_detection_cookie_name())
        features_cookie = request.COOKIES.get(self.get_feature_cookie_name())

        features = None
        if detection_cookie is not None:
            parameters = self.get_cookie_parameters(detection_cookie)
            features = self.extract_features_from_detection(parameters)
        elif features_cookie is not None:
            features = self.extract_features_from_cookie(features_cookie)

        return features

    def extract_features_from_detection(self, parameters):
        return {
            'screen_density': self.get_screen_density(parameters),
            'screen_size': self.get_screen_size(parameters),
            'input': self.get_input_device(parameters),
        }

    def get_screen_density(self, parameters):
        if 'density' not in parameters:
            density = self.default_screen_density
        else:
            density = float(parameters['density'])
        return 'retina' if density >= 2.0 else 'default'

    def get_screen_size(self, parameters):
        if 'screen' not in parameters:
            size = self.default_screen_size
        else:
            size = [int(p) for p in parameters['screen'].split('x')]
        return 'mobile' if size[0] <= 360 else 'default'

    def get_input_device(self, parameters):
        if 'touch' not in parameters:
            touch = self.default_is_touch
        else:
            touch = parameters['touch'] == 'true'
        return 'touch' if touch else 'pointer'

    def get_default_features(self):
        return self.extract_features_from_detection({})

    def extract_features_from_cookie(self, features_cookie):
        return self.get_cookie_parameters(features_cookie)

    def set_features_cookie(self, request, response, features):
        packed_features = ','.join([
            '{}:{}'.format(*item) for item in features.items()
        ])
        response.set_cookie(self.get_feature_cookie_name(), value=packed_features,
                            expires=self.get_feature_cookie_expiration(request))

    def override(self, override_parameter):
        if override_parameter == 'remove':
            return None
        elif override_parameter == self.default_features_query:
            return self.get_default_features()
        else:
            # TODO: determine override_parameter => feature mapping
            return override_parameter

    #
    # Settings
    #

    def get_featureless_agents(self):
        return self.featureless_agents

    def get_ignored_path_prefixes(self):
        return self.ignored_path_prefixes

    def get_feature_cookie_name(self):
        return self.feature_cookie_name

    def get_feature_cookie_expiration(self, request):
        return datetime.now() + self.feature_cookie_expires

    def get_referrer_cookie_name(self):
        return self.referrer_cookie_name

    def get_detection_cookie_name(self):
        return self.detection_cookie_name

    def get_override_parameter(self):
        return self.override_parameter

    def get_default_path(self, request):
        get = copy(request.GET)
        get[self.get_override_parameter()] = self.default_features_query
        return '{path}?{query}'.format(
            path=request.path,
            query=get.urlencode()
        )

    #
    #
    #

    @staticmethod
    def get_cookie_parameters(parameters):
        # Convert parameters from <key>:<value>,<key>:<value> to dict
        return dict([param.split(':') for param in parameters.split(',')])

    def is_featureless(self, request):
        return self.is_featureless_agent(request.META.get('HTTP_USER_AGENT'))

    def should_skip_detection(self, request):
        return self.is_ignored_path(request.get_full_path()) or self.is_featureless(request)

    def is_ignored_path(self, path):
        return any(
            path.startswith(prefix)
            for prefix in self.get_ignored_path_prefixes()
        )

    def is_featureless_agent(self, user_agent):
        if user_agent:
            return any(
                crawler in user_agent
                for crawler in self.get_featureless_agents()
            )
