import json

from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from amoid.settings import BASE_DIR

universe = set(json.loads("".join(open(BASE_DIR+'/resources/items.json').readlines())))


def index(request):
    return render(request, 'index.html')

def my_function(items):
    items = set(items)
    return list(universe - items)[:10]

@csrf_exempt
def get_item(request):
    if request.method == 'GET':
        items = request.GET.get('items', '')
        items = json.loads(items)

        new_items = my_function(items)

        response_data = {'items': new_items}
        return HttpResponse(json.dumps(response_data), content_type="application/json")
