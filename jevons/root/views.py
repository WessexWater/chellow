from django.shortcuts import render_to_response, redirect, render
from django.core.context_processors import csrf
from root.models import Asset, Advance, Importer
import csv
import logging
import datetime
import importers
from root.monad import UserException


logger = logging.getLogger('jevons')

def home(request):
    root_asset = Asset.objects.get(parent__exact=None)
    return render_to_response('home.html', {'root_asset': root_asset, 'importers': Importer.objects.all()})


def show_asset(request):
    asset_id = request.GET['asset_id']
    asset = Asset.objects.get(id__exact=asset_id)
    sub_assets = Asset.objects.filter(parent=asset)
    
    return render_to_response('show_asset.html', {'asset': asset, 'sub_assets': sub_assets})


def update_asset(request):
    if request.method == "GET":
        asset_id = request.GET['asset_id']
        asset = Asset.objects.get(id__exact=asset_id)
        
        vals = {'asset': asset}
        vals.update(csrf(request))
        
        return render_to_response('update_asset.html', vals)

    elif request.method == "POST":
        asset_id = request.POST['asset_id']
        asset = Asset.objects.get(id__exact=asset_id)
        asset.name = request.POST['name']
        asset.code = request.POST['code']
        asset.properties = request.POST['properties']
        asset.save()

        return redirect('/show_asset?asset_id=' + asset_id)
    
def add_asset(request):
    if request.method == "GET":
        parent_asset_id = request.GET['parent_asset_id']
        parent_asset = Asset.objects.get(id__exact=parent_asset_id)
        
        vals = {'parent_asset': parent_asset}
        vals.update(csrf(request))
        
        return render_to_response('add_asset.html', vals)

    elif request.method == "POST":
        parent_asset_id = request.POST['parent_asset_id']
        parent_asset = Asset.objects.get(id__exact=parent_asset_id)
        name = request.POST['name']
        code = request.POST['code']
        properties = request.POST['properties']
        asset = Asset(parent=parent_asset, name=name, code=code, properties=properties)
        asset.save()
        
        return redirect('/show_asset?asset_id=' + str(asset.id))


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
        
        return redirect('/show_asset?asset_id=' + str(asset.parent.id))

    
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


def add_advance(request):
    if request.method == "GET":
        asset_id = request.GET['asset_id']
        asset = Asset.objects.get(id__exact=asset_id)
        
        vals = {'asset': asset, 'utc_now': datetime.datetime.utcnow(), 'months': list(range(1, 13)), 'days': list(range(1, 31)), 'hours': list(range(24)), 'minutes': list(range(60))}
        vals.update(csrf(request))
        
        return render(request, 'add_advance.html', vals)

    elif request.method == "POST":
        asset_id = request.POST['asset_id']
        asset = Asset.objects.get(id__exact=asset_id)
        start_date_year_str = request.POST['year']
        start_date_month_str = request.POST['month']
        start_date_day_str = request.POST['day']
        start_date_hour_str = request.POST['hour']
        start_date_minute_str = request.POST['minute']
        value_str = request.POST['value']
        advance = Advance(asset=asset, start_date=datetime.datetime(int(start_date_year_str), int(start_date_month_str), int(start_date_day_str), int(start_date_hour_str), int(start_date_minute_str)), value=float(value_str))
        advance.save()
        return redirect('/show_advance?advance_id=' + str(advance.id))
    

def show_advance(request):
    advance_id = request.GET['advance_id']
    advance = Advance.objects.get(id__exact=advance_id)
    
    return render(request, 'show_advance.html', {'advance': advance})


def get_integer(params, name):
    val_str = params[name]
    val_int = int(val_str)
    return val_int

def get_datetime(params, prefix):
    year = get_integer(params, prefix + '_year')
    month = get_integer(params, prefix + '_month')
    day = get_integer(params, prefix + '_day')
    hour = get_integer(params, prefix + '_hour')
    minute = get_integer(params, prefix + '_minute')
    return datetime.datetime(year, month, day, hour, minute)


def update_advance(request):
    if request.method == "GET":
        advance_id = request.GET['advance_id']
        advance = Advance.objects.get(id__exact=advance_id)
        
        vals = {'advance': advance, 'months': list(range(1, 13)), 'days': list(range(1, 31)), 'hours': list(range(24)), 'minutes': list(range(60))}
        vals.update(csrf(request))
        
        return render_to_response('update_advance.html', vals)

    elif request.method == "POST":
        advance_id = request.POST['advance_id']
        advance = Advance.objects.get(id__exact=advance_id)
        advance.start_date = get_datetime(request.POST, 'start_date')
        
        advance.value = request.POST['value']
        advance.save()
        
        return redirect('/show_advance?advance_id=' + advance_id)


def delete_advance(request):
    if request.method == "GET":
        advance_id = request.GET['advance_id']
        advance = Advance.objects.get(id__exact=advance_id)
        
        vals = {'advance': advance}
        vals.update(csrf(request))
        
        return render_to_response('delete_advance.html', vals)

    elif request.method == "POST":
        advance_id = request.POST['advance_id']
        advance = Advance.objects.get(id__exact=advance_id)
        stream = advance.stream
        advance.delete()
        
        return redirect('/show_stream?stream_id=' + str(stream.id))


def show_importer(request, message=None, status=200):
    if request.method == "GET":
        importer_id = request.GET['importer_id']
        importer = importers.get_importer(importer_id)
        if importer is None:
            importer = Importer.objects.get(id__exact=importer_id)
            is_importer_loaded = False
        else:
            is_importer_loaded = True
            
        vals = {'importer': importer, 'is_importer_loaded': is_importer_loaded, 'message': message}
        vals.update(csrf(request))
        return render(request, 'show_importer.html', vals, status=status)
    
    elif request.method == "POST":
        importer_id = request.POST['importer_id']

        try:
            if 'load' in request.POST:
                importers.load_importer(importer_id)
                return redirect('/show_importer?importer_id=' + importer_id) 
            elif 'unload' in request.POST:
                importers.unload_importer(importer_id)
                return redirect('/show_importer?importer_id=' + importer_id)
            else:
                raise UserException("Action not recognized.")
            '''
            if 'start' in request.POST:
                pass
                #contract_f(hh_importer_contract, 'start_hh_importer_task')(ctx, contract)
                #inv.sendSeeOther(get_uri())
            #elif inv.hasParameter('now'):
                #Thread(hh_importer, "Import Now: " + str(contract.getId())).start()
                #inv.sendSeeOther(get_uri())
            '''
        except UserException, message:
            return redirect('jevons.root.views.show_importer', message=message, status=400)


def add_importer(request):
    if request.method == "GET":
        
        vals = {}
        vals.update(csrf(request))
        
        return render_to_response('add_importer.html', vals)

    elif request.method == "POST":
        name = request.POST['name']
        properties = request.POST['properties']
        importer = Importer(name=name, properties=properties)
        try:
            importer.validate()
            importer.save()
            return redirect('/show_importer?importer_id=' + str(importer.id))
        except UserException, detail:
            vals = {'message': detail}
            vals.update(csrf(request))
            return render(request, 'add_importer.html', vals)
        '''
        except:
            e_info = sys.exc_info()
            tb = e_info[2]
            sys.stderr.write("Outer problem " + str(e_info[0]) + str(e_info[1]) + str(tb) + " line number " + str(tb.tb_lineno))
            return render(request, 'add_importer.html', {})
         '''

def update_importer(request):
    if request.method == "GET":
        importer_id = request.GET['importer_id']
        importer = Importer.objects.get(id__exact=importer_id)
        
        vals = {'importer': importer}
        vals.update(csrf(request))
        
        return render_to_response('update_importer.html', vals)

    elif request.method == "POST":
        if 'update' in request.POST:
            importer_id = request.POST['importer_id']
            importer = Importer.objects.get(id__exact=importer_id)
            importer.name = request.POST['name']
            importer.properties = request.POST['properties']

            try:
                importer.validate()
                importer.save()
                return redirect('/show_importer?importer_id=' + importer_id)
            except UserException, detail:
                vals = {'importer': importer, 'message': detail}
                vals.update(csrf(request))
                return render(request, 'update_importer.html', vals)
        else:
            importer_id = request.POST['importer_id']
            importer = Importer.objects.get(id__exact=importer_id)
            importer.state = request.POST['state']

            try:
                importer.validate()
                importer.save()
                return redirect('/show_importer?importer_id=' + importer_id)
            except UserException, detail:
                vals = {'importer': importer, 'message': detail}
                vals.update(csrf(request))
                return render(request, 'update_importer.html', vals)
            