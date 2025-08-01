from rest_framework import serializers
from .models import VoiceChannel, VoiceChannelMember, Call
from users.serializers import UserMiniSerializer


class VoiceChannelMemberSerializer(serializers.ModelSerializer):
    """
    Сериализатор для участников голосового канала
    """
    user = UserMiniSerializer(read_only=True)
    
    class Meta:
        model = VoiceChannelMember
        fields = [
            'id', 'user', 'joined_at', 'mic_status', 'speaker_status'
        ]
        read_only_fields = ['id', 'joined_at']


class VoiceChannelSerializer(serializers.ModelSerializer):
    """
    Сериализатор для голосовых каналов
    """
    creator = UserMiniSerializer(read_only=True)
    members = VoiceChannelMemberSerializer(many=True, read_only=True)
    members_count = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = VoiceChannel
        fields = [
            'id', 'name', 'creator', 'created_at', 'is_active',
            'max_participants', 'members', 'members_count'
        ]
        read_only_fields = ['id', 'creator', 'created_at']
    
    def get_members_count(self, obj):
        return obj.members.count()


class CallSerializer(serializers.ModelSerializer):
    """
    Сериализатор для звонков
    """
    caller = UserMiniSerializer(read_only=True)
    receiver = UserMiniSerializer(read_only=True)
    duration = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Call
        fields = [
            'id', 'caller', 'receiver', 'started_at', 'ended_at',
            'status', 'call_type', 'duration'
        ]
        read_only_fields = ['id', 'caller', 'started_at']
    
    def get_duration(self, obj):
        return obj.duration
