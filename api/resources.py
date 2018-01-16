from tastypie.resources import ModelResource
from console.models import UserProfile
from relay_manager.models import RelayNodes


class UserResource(ModelResource):
    class Meta:
        queryset = UserProfile.objects.all()
        resource_name = 'user'


class RelayNodeResource(ModelResource):
    class Meta:
        queryset = RelayNodes.objects.all()
        resource_name = 'relay_nodes'
