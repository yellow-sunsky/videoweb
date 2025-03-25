# videoweb/crawler/views.py
from django.http import JsonResponse
from .crawler import crawl_and_save

def start_crawling(request):
    url = request.GET.get('url')
    classification_id = request.GET.get('classification_id')
    if url and classification_id:
        try:
            crawl_and_save(url, classification_id)
            return JsonResponse({'status': 'success', 'message': '数据抓取并保存成功！'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    else:
        return JsonResponse({'status': 'error', 'message': '未提供有效的 URL 或 classification_id'})