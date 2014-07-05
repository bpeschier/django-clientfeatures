def device_features(request):
    """
    Exposes the features of the device in templates
    """
    return {'device_features': request.device_features}

