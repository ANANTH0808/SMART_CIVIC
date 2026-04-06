from rest_framework import serializers
from . models import *

class ComplaintSerializer(serializers.ModelSerializer):
    class Meta:
        model=Complaint
        fields='__all__'