from tastypie.resources import ModelResource
from console.models import UserProfile


class UserResource(ModelResource):
    class Meta:
        queryset = UserProfile.objects.all()
        resource_name = 'user'