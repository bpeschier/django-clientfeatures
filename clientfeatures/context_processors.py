def client_features(request):
    """
    Exposes the features of the client in templates
    """
    return {'client_features': request.client_features}

