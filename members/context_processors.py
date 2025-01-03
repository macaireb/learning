def user_group(request):
    """
    Adds the groups of the authenticated user to the template context.
    """
    if request.user.is_authenticated:
        groups = request.user.groups.values_list('name', flat=True)
        return {'user_groups': list(groups)}
    return {'user_groups': []}
