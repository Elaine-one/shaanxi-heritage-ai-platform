from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from .models import Heritage, UserHistory
from .serializers import HeritageSerializer, UserHistorySerializer
from django.utils import timezone

class UserHistoryViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserHistorySerializer
    
    def get_queryset(self):
        # 用户只能访问自己的浏览历史
        return UserHistory.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def add(self, request):
        """添加浏览历史记录"""
        heritage_id = request.data.get('heritage_id')
        
        if not heritage_id:
            return Response({'error': '缺少heritage_id参数'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            heritage = Heritage.objects.get(id=heritage_id)
        except Heritage.DoesNotExist:
            return Response({'error': '非遗项目不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        # 获取或创建历史记录，如果已存在则更新访问时间
        history_record, created = UserHistory.objects.get_or_create(
            user=request.user,
            heritage=heritage,
            defaults={'visit_time': timezone.now()}
        )
        
        if not created:
            # 如果记录已存在，更新访问时间
            history_record.visit_time = timezone.now()
            history_record.save()
        
        return Response({
            'message': '浏览历史已添加',
            'heritage_id': heritage_id,
            'created': created
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def list_history(self, request):
        """获取用户浏览历史列表"""
        history_records = self.get_queryset().select_related('heritage')
        
        history_data = []
        for record in history_records:
            heritage_data = HeritageSerializer(record.heritage, context={'request': request}).data
            heritage_data['visit_time'] = record.visit_time
            history_data.append(heritage_data)
        
        return Response(history_data)
    
    @action(detail=False, methods=['delete'])
    def clear(self, request):
        """清除用户所有浏览历史"""
        deleted_count = self.get_queryset().delete()[0]
        return Response({
            'message': f'已清除 {deleted_count} 条浏览历史记录'
        })
    
    @action(detail=True, methods=['delete'])
    def remove(self, request, pk=None):
        """删除特定的浏览历史记录"""
        try:
            history_record = self.get_queryset().get(heritage_id=pk)
            history_record.delete()
            return Response({'message': '浏览历史记录已删除'})
        except UserHistory.DoesNotExist:
            return Response({'error': '浏览历史记录不存在'}, status=status.HTTP_404_NOT_FOUND)