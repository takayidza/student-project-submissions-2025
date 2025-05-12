from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def firmware_update(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print("✅ Received device status:", data)

            # You can process or save this status info here
            # Example: log to database or display on dashboard

            return JsonResponse({'message': 'Status received successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)
