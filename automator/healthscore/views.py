import json
import logging
from django.utils import timezone
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.template import loader
from django.http import HttpResponse
from .forms import AddressForm, HealthscoreForm
from healthscore.services.tract_service import TractService
from healthscore.services.data_service import DataService
from healthscore.services.excel_service import ExcelService
from healthscore.services.healthscore_service import HealthscoreService

log = logging.getLogger('django')


def index(request):
    template = loader.get_template('healthscore/index.html')
    context = {}

    timezone.activate('America/New_York')

    return HttpResponse(template.render(context, request))


@login_required(login_url='/accounts/login')
def download_healthscore(request):

    if request.method == 'POST':
        form = HealthscoreForm(request.POST)
        if form.is_valid():

            included_tracts = request.POST.getlist('included_tracts')
            additional_tracts = request.POST.getlist('additional_tracts')

            # Compile housing data if it was submitted
            housing_data = None
            housing_unit_type = request.POST.getlist('housing_unit_type')
            housing_unit_count = request.POST.getlist('housing_unit_count')
            housing_rent = request.POST.getlist('housing_rent')

            if len(housing_unit_type) > 0:
                if len(housing_unit_type) != len(housing_unit_count) or len(housing_unit_type) != len(housing_rent):
                    data_details = {'status': 'failure',
                                    'message': 'Invalid form submission. Inconsistent housing data.'}
                    return HttpResponse(json.dumps(data_details))

                housing_data = []
                for i in range(0, len(housing_unit_type)):
                    housing_data.append({'unit_type': housing_unit_type[i],
                                         'unit_count': housing_unit_count[i],
                                         'starting_rent': housing_rent[i]})

            (title, address, state_fips, state_name,
             state_short_code, county_fips, county_name, school_district, community,
             primary_tract, all_tracts, block_group,
             buffer_radius, population_threshold, scenario) = form.get_clean_data(included_tracts, additional_tracts)

        else:
            return HttpResponse("Something is wrong with the submitted values.")
    else:
        healthscore_id = request.GET.get('id')
        service = HealthscoreService(request.user)
        healthscore = service.get_healthscore(healthscore_id)

        if healthscore.user != request.user:
            return HttpResponse("Forbidden. Requested scorecard owned by different user.")

        title = healthscore.title
        address = healthscore.address
        state_fips = healthscore.state.fips_code
        state_short_code = healthscore.state.short_code
        county_fips = healthscore.county_code
        county_name = healthscore.county_name
        primary_tract = healthscore.primary_tract.geoid[-6:]
        block_group = healthscore.block_group
        school_district = healthscore.school_district
        community = healthscore.community.name
        buffer_radius = healthscore.buffer_radius
        population_threshold = healthscore.population_threshold
        scenario = healthscore.scenario

        # Create all_tracts, housing lists based on healthscore related objects...
        all_tracts = []
        for hs in healthscore.all_tracts.all():
            all_tracts.append(hs.geoid[-6:])
        all_tracts.sort()

        # Primary tract goes first..
        all_tracts.insert(0, all_tracts.pop(all_tracts.index(primary_tract)))

        housing_data = []
        for unit in healthscore.housingunittype_set.all():
            housing_data.append({'unit_type': unit.unit_type,
                                 'unit_count': unit.unit_count,
                                 'starting_rent': unit.starting_rent})

    # Fetch any data we don't yet have
    data_service = DataService(request.user)
    vintages = data_service.vintages()

    data_service.load_acs(vintages['ACS'], state_short_code, county_fips, all_tracts)
    data_service.load_cdc(vintages['CDC'], state_short_code, county_fips, all_tracts)
    data_service.load_ejscreen(vintages['EJScreen'], state_short_code, county_fips, all_tracts)

    # Produce the spreadsheet using the appropriate data
    excel_service = ExcelService(request.user)
    user = request.user
    xlsx_data = excel_service.to_excel(user, address, state_fips, state_short_code, county_fips, county_name,
                                       all_tracts, primary_tract, block_group, school_district, community,
                                       housing_data, buffer_radius, population_threshold, scenario, True)
    response = HttpResponse(xlsx_data, content_type="application/vnd.ms-excel")
    response['Content-Disposition'] = f'attachment; filename="{title}-scorecard.xlsx"'
    return response

@login_required(login_url='/accounts/login')
def save_healthscore(request):

    if request.method == 'POST':
        form = HealthscoreForm(request.POST)
        if form.is_valid():

            healthscore_id = None
            if 'healthscore_id' in request.POST:
                healthscore_id = request.POST.get('healthscore_id')

            included_tracts = request.POST.getlist('included_tracts')
            additional_tracts = request.POST.getlist('additional_tracts')

            # Compile housing data if it was submitted
            housing_data = None
            housing_unit_type = request.POST.getlist('housing_unit_type')
            housing_unit_count = request.POST.getlist('housing_unit_count')
            housing_rent = request.POST.getlist('housing_rent')

            if len(housing_unit_type) > 0:
                if len(housing_unit_type) != len(housing_unit_count) or len(housing_unit_type) != len(housing_rent):
                    data_details = {'status': 'failure',
                                    'message': 'Invalid form submission. Inconsistent housing data.'}
                    return HttpResponse(json.dumps(data_details))

                housing_data = []
                for i in range(0, len(housing_unit_type)):
                    housing_data.append({'unit_type': housing_unit_type[i],
                                         'unit_count': housing_unit_count[i],
                                         'rent': housing_rent[i]})

            (title, address, state_fips, state_name,
             state_short_code, county_fips, county_name, school_district, community,
             primary_tract, all_tracts, block_group,
             buffer_radius, population_threshold, scenario) = form.get_clean_data(included_tracts, additional_tracts)

            service = HealthscoreService(request.user)

            if healthscore_id is None:
                healthscore = service.create_healthscore(request.user, title, address, state_fips, state_name,
                                                             state_short_code, county_fips, county_name, block_group,
                                                             primary_tract, all_tracts, school_district, community,
                                                             housing_data, buffer_radius, population_threshold,
                                                             scenario)
            else:
                healthscore = service.update_healthscore(healthscore_id, request.user, title, address, state_fips, state_name,
                                                          state_short_code, county_fips, county_name, block_group,
                                                          primary_tract, all_tracts, school_district, community,
                                                          housing_data, buffer_radius, population_threshold, scenario)

            data_details = {'status': 'success', 'id': healthscore.id}
            return HttpResponse(json.dumps(data_details))

        else:
            data_details = {'status': 'failure'}
            return HttpResponse(json.dumps(data_details))

@login_required(login_url='/accounts/login')
def save_healthscore_title(request):

    if request.method == 'POST':

            healthscore_id = None
            if 'healthscore_id' in request.POST:
                healthscore_id = request.POST.get('healthscore_id')

            title = request.POST.get('title')

            service = HealthscoreService(request.user)
            healthscore = service.update_healthscore_title(healthscore_id, title)

            data_details = {'status': 'success', 'id': healthscore.id}
            return HttpResponse(json.dumps(data_details))

    else:
        data_details = {'status': 'failure'}
        return HttpResponse(json.dumps(data_details))

@login_required(login_url='/accounts/login')
def tracts(request):
    template = loader.get_template('healthscore/tracts.html')
    tract_service = TractService(request.user)
    show_scenario = has_access(request.user)

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = AddressForm(request.POST)
        # check whether it's valid:
        if form.is_valid():

            posted_address = form.cleaned_data['address']

            # These are the user-friendly values that get submitted to the form
            buffer_radius_miles = form.cleaned_data['buffer_radius']
            pop_threshold_int = form.cleaned_data['population_threshold']
            scenario = form.cleaned_data['scenario']

            # ...these are the converted values that get used in the tract selection algorithm
            buffer_radius = tract_service.miles_to_meters(buffer_radius_miles)
            pop_threshold = pop_threshold_int / 100

            try:
                (iframe_content, state_fips, state_name, state_short_code, county_fips, county_code_alt, county_name,
                 primary, block_group, unique_tracts) = tract_service.select_tracts(
                    posted_address, buffer_radius, pop_threshold)
            except BaseException as e:
                template = loader.get_template('healthscore/error.html')
                return HttpResponse(template.render({}, request))

            school_district = ''
            if state_short_code in ['MA', 'CT', 'RI']:
                vintage = DataService.vintages()['SchoolDistrict']
                school_district = tract_service.get_school_district(state_fips, county_fips, primary, vintage)

                if school_district == '' and state_short_code == 'CT':
                    school_district = tract_service.get_school_district(state_fips, county_code_alt, primary, vintage)

            healthscore_id = None
            community = 'Disadvantaged'
            title = 'Untitled'

            # If we got here because the user edited settings for an existing scorecard, let's keep these values...
            if 'healthscore_id' in request.POST:
                healthscore_id = request.POST.get('healthscore_id')
            if 'community' in request.POST:
                community = request.POST.get('community')
            if 'title' in request.POST:
                title = request.POST.get('title')

            context = {
                'map_content': iframe_content, 
                'state_fips': state_fips, 
                'state_name': state_name,
                'state_short_code': state_short_code, 
                'county_fips': county_fips, 
                'county_name': county_name,
                'primary_tract': primary, 
                'block_group': block_group, 
                'school_district': school_district,
                'all_tracts': unique_tracts, 
                'address': posted_address,
                'buffer_radius': buffer_radius_miles,
                'population_threshold': pop_threshold_int,
                'community': community,
                'title': title,
                'healthscore_id': healthscore_id,
                'show_scenario': show_scenario,
                'scenario': scenario
            }

            return HttpResponse(template.render(context, request))

        else:
            raise Exception("Invalid form submission")

    # if a GET, we'll assume it's an existing scorecard that is being loaded
    else:
        healthscore_id = request.GET.get('id')
        service = HealthscoreService(request.user)
        healthscore = service.get_healthscore(healthscore_id)

        if healthscore.user != request.user:
            return HttpResponse("Forbidden. Requested scorecard owned by different user.")

        buffer_radius = tract_service.miles_to_meters(healthscore.buffer_radius)
        pop_threshold = healthscore.population_threshold / 100
        scenario = healthscore.scenario

        (iframe_content, state_fips, state_name, state_short_code, county_fips, county_code_alt, county_name,
         primary, block_group, unique_tracts) = tract_service.select_tracts(
            healthscore.address, buffer_radius, pop_threshold)

        # Create all_tracts, housing lists based on healthscore related objects...
        all_tracts = []
        for hs in healthscore.all_tracts.all():
            all_tracts.append(hs.geoid[-6:])
        all_tracts.sort()

        housing = []
        for unit in healthscore.housingunittype_set.all():
            housing.append(unit)

        context = {
            'healthscore_id': healthscore_id,
            'title': healthscore.title,
            'map_content': iframe_content,
            'state_fips': state_fips,
            'state_name': state_name,
            'state_short_code': state_short_code,
            'county_fips': county_fips,
            'county_name': county_name,
            'primary_tract': primary,
            'block_group': block_group,
            'school_district': healthscore.school_district,
            'all_tracts': all_tracts,
            'housing': housing,
            'address': healthscore.address,
            'buffer_radius': healthscore.buffer_radius,
            'buffer_radius_miles': healthscore.buffer_radius,
            'population_threshold': healthscore.population_threshold,
            'community': healthscore.community.name,
            'show_scenario': show_scenario,
            'scenario': scenario
        }

    return HttpResponse(template.render(context, request))


@login_required(login_url='/accounts/login')
def my_scorecards(request):
    template = loader.get_template('healthscore/saved.html')

    service = HealthscoreService(request.user)
    all_scorecards = service.get_my_healthscores()
    show_scenario = has_access(request.user)

    context = {"scorecards": all_scorecards,
               "show_scenario": show_scenario}

    return HttpResponse(template.render(context, request))


@login_required(login_url='/accounts/login')
def delete_healthscore(request):
    service = HealthscoreService(request.user)

    if 'id' in request.GET:
        healthscore_id = request.GET.get('id')
        service.delete_healthscore(healthscore_id)
        return redirect('/saved')
    else:
        return HttpResponse('No scorecard  id given.')


@login_required(login_url='/accounts/login')
def settings(request):
    template = loader.get_template('healthscore/settings.html')

    data_service = DataService(request.user)
    arguments = ['2020', 'MA', '009', ['215102', '215101', '216100']]

    acs_records = data_service.load_acs(*arguments)
    cdc_records = data_service.load_cdc('2020', 'MA', '009', ['215102', '215101', '216100'])
    ej_records = data_service.load_ejscreen(*arguments)

    context = {"acs_data": acs_records, "cdc_data": cdc_records, "ej_data": ej_records}

    return HttpResponse(template.render(context, request))


@login_required(login_url='/accounts/login')
# Example of how to handle and respond to an AJAX request
def select_tracts(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = AddressForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            tract_service = TractService(request.user)
            posted_address = form.cleaned_data['address']
            buffer_radius = form.cleaned_data['buffer_radius']
            pop_threshold = form.cleaned_data['population_threshold']

            (iframe_content, state_fips, state_name, state_short_code, county_fips, county_code_alt, county_name,
             primary, block_group, unique_tracts) = tract_service.select_tracts(
                posted_address, buffer_radius, pop_threshold)

            school_district = ''
            if state_short_code in ['MA', 'CT', 'RI']:
                vintage = DataService.vintages()['SchoolDistrict']
                school_district = tract_service.get_school_district(state_fips, county_fips, primary, vintage)

                if school_district == '' and state_short_code == 'CT':
                    school_district = tract_service.get_school_district(state_fips, county_code_alt, primary, vintage)

            data_details = {'map_content': iframe_content, 'state_fips': state_fips, 'state_name': state_name,
                            'state_short_code': state_short_code, 'county_fips': county_fips, 'county_name': county_name,
                            'primary_tract': primary, 'block_group': block_group, 'school_district': school_district,
                            'all_tracts': unique_tracts}
            return HttpResponse(json.dumps(data_details))

    # if a GET (or any other method) we'll create a blank form
    else:
        return HttpResponse("Something went wrong trying to geocode the submitted address.")

def about(request):
    template = loader.get_template('healthscore/about.html')
    context = {}

    return HttpResponse(template.render(context, request))


def has_access(user):
    return user.groups.filter(name='Admin').exists()