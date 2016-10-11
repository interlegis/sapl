from rest_framework import serializers


class ChoiceSerializer(serializers.Serializer):
    pk = serializers.IntegerField()
    display = serializers.SerializerMethodField()

    def get_display(self, obj):
        return str(obj)
