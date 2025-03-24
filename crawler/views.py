# videoweb/crawler/views.py
from django.http import JsonResponse
from .crawler import crawl_and_save

def start_crawling(request):
    try:
        crawl_and_save()
        return JsonResponse({'status': 'success', 'message': '数据抓取并保存成功！'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})