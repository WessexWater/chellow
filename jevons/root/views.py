from django.shortcuts import render_to_response, redirect, render
from django.core.context_processors import csrf
from root.models import Asset, Stream, Advance
import csv
import logging
import datetime


logger = logging.getLogger('jevons')

def home(request):
    root_asset = Asset.objects.get(parent__exact=None)
    return render_to_response('home.html', {'root_asset': root_asset})


def show_asset(request):
    asset_id = request.GET['asset_id']
    asset = Asset.objects.get(id__exact=asset_id)
    sub_assets = Asset.objects.filter(parent=asset)
    
    return render_to_response('asset.html', {'asset': ast, 'sub_assets': sub_assets})

def show_stream(request):
    stream_id = request.GET['stream_id']
    stream = Stream.objects.get(id__exact=stream_id)
    
    return render(request, 'stream.html', {'stream': stream})

def edit_asset(request):
    if request.method == "GET":
        asset_id = request.GET['asset_id']
        asset = Asset.objects.get(id__exact=asset_id)
        
        vals = {'asset': asset}
        vals.update(csrf(request))
        
        return render_to_response('edit_asset.html', vals)

    elif request.method == "POST":
        asset_id = request.POST['asset_id']
        asset = Asset.objects.get(id__exact=asset_id)
        asset.name = request.POST['name']
        asset.code = request.POST['code']
        asset.save()
        
        vals = {'asset': asset}
        vals.update(csrf(request))
        return render_to_response('edit_asset.html', vals)
    
def add_sub_asset(request):
    if request.method == "GET":
        asset_id = request.GET['asset_id']
        asset = Asset.objects.get(id__exact=asset_id)
        
        vals = {'asset': asset}
        vals.update(csrf(request))
        
        return render_to_response('add_sub_asset.html', vals)

    elif request.method == "POST":
        asset_id = request.POST['asset_id']
        asset = Asset.objects.get(id__exact=asset_id)
        name = request.POST['name']
        code = request.POST['code']
        sub_asset = Asset(name=name, code=code, parent=ast)
        sub_asset.save()
        
        return redirect('/asset?asset_id=' + asset_id)


def delete_asset(request):
    if request.method == "GET":
        asset_id = request.GET['asset_id']
        asset = Asset.objects.get(id__exact=asset_id)
        
        vals = {'asset': asset}
        vals.update(csrf(request))
        
        return render_to_response('delete_asset.html', vals)

    elif request.method == "POST":
        asset_id = request.POST['asset_id']
        asset = Asset.objects.get(id__exact=asset_id)
        if asset.parent is None:
            vals = {'asset': asset, 'message': "I'm afraid you can't delete the root asset."}
            vals.update(csrf(request))
            return render('delete_asset.html', vals, status=400)
        asset.delete()
        
        return redirect('/asset?asset_id=' + str(asset.parent.id))

    
def csv_import(request):
    if request.method == "GET":
        return render_to_response('csv_import.html', csrf(request))
    elif request.method == "POST":
        csv_file = request.FILES['csv_file']
        rdr = csv.reader(csv_file)
        for row in rdr:
            action = row[0]
            i_type = row[1]
            
            if action == 'insert':
                if i_type == 'asset':
                    parent = Asset.objects.get(code__exact=row[2])
                    
                    ast = Asset(parent=parent, name=row[3], code=row[4])
                    ast.save()
        vals = {'message': "File imported successfully."}
        vals.update(csrf(request))
        return render_to_response('csv_import.html', vals)


def add_stream(request):
    if request.method == "GET":
        asset_id = request.GET['asset_id']
        asset = Asset.objects.get(id__exact=asset_id)
        
        vals = {'asset': asset}
        vals.update(csrf(request))
        
        return render_to_response('add_stream.html', vals)

    elif request.method == "POST":
        asset_id = request.POST['asset_id']
        asset = Asset.objects.get(id__exact=asset_id)
        name = request.POST['name']
        code = request.POST['code']
        properties = request.POST['properties']
        stream = Stream(asset=asset, code=code, name=name, properties=properties)
        stream.save()
        return redirect('/asset?asset_id=' + asset_id)
    
    
def bglobal_importer(request):
    pass


def add_advance(request):
    if request.method == "GET":
        stream_id = request.GET['stream_id']
        stream = Stream.objects.get(id__exact=stream_id)
        
        vals = {'stream': stream, 'utc_now': datetime.datetime.utcnow(), 'months': list(range(1, 13)), 'days': list(range(1, 31)), 'hours': list(range(24)), 'minutes': list(range(60))}
        vals.update(csrf(request))
        
        return render(request, 'add_advance.html', vals)

    elif request.method == "POST":
        stream_id = request.POST['stream_id']
        stream = Stream.objects.get(id__exact=stream_id)
        start_date_year_str = request.POST['year']
        start_date_month_str = request.POST['month']
        start_date_day_str = request.POST['day']
        start_date_hour_str = request.POST['hour']
        start_date_minute_str = request.POST['minute']
        value_str = request.POST['value']
        advance = Advance(stream=stream, start_date=datetime.datetime(int(start_date_year_str), int(start_date_month_str), int(start_date_day_str), int(start_date_hour_str), int(start_date_minute_str)), name=name, properties=properties)
        stream.save()
        return redirect('/asset?asset_id=' + asset_id)