import logging
from django import forms

log = logging.getLogger('django')

class AddressForm(forms.Form):
    address = forms.CharField(label='Address', max_length=100)
    buffer_radius = forms.FloatField()
    population_threshold = forms.IntegerField()

    valid_choices = [('HNEF II', 'HNEF II'), ('NEF', 'NEF'), ('NNE HCIP', 'NNE HCIP')]
    scenario = forms.ChoiceField(choices=valid_choices, required=False)


class HealthscoreForm(forms.Form):
    title = forms.CharField(max_length=128)
    address = forms.CharField(max_length=128)
    state_fips = forms.CharField(max_length=2)
    state_name = forms.CharField(max_length=64)
    state_short_code = forms.CharField(max_length=2)
    county_fips = forms.CharField(max_length=4)
    county_name = forms.CharField(max_length=64)
    block_group = forms.CharField(max_length=4)
    school_district = forms.CharField(max_length=80, required=False)
    primary_tract = forms.CharField(max_length=16)

    valid_choices = [('HNEF II', 'HNEF II'), ('NEF', 'NEF'), ('NNE HCIP', 'NNE HCIP')]
    scenario = forms.ChoiceField(choices=valid_choices, required=False)

    # Note that these two fields are actually an arrays, but Django has limited support for array fields with forms.
    # The values will be overridden in the view logic...
    included_tracts = forms.CharField(max_length=128, required=False)
    additional_tracts = forms.CharField(max_length=128, required=False)

    community = forms.CharField(max_length=32)
    buffer_radius = forms.FloatField()
    population_threshold = forms.IntegerField()
    
    def get_clean_data(self, included_tracts, additional_tracts):
        title = self.cleaned_data['title']
        address = self.cleaned_data['address']
        state_fips = self.cleaned_data['state_fips']
        state_name = self.cleaned_data['state_name']
        state_short_code = self.cleaned_data['state_short_code']
        county_fips = self.cleaned_data['county_fips']
        county_name = self.cleaned_data['county_name']
        school_district = self.cleaned_data['school_district']
        community = self.cleaned_data['community']
        primary_tract = self.cleaned_data['primary_tract']
        block_group = self.cleaned_data['block_group']
        buffer_radius = self.cleaned_data['buffer_radius']
        population_threshold = self.cleaned_data['population_threshold']
        scenario = self.cleaned_data['scenario']
    
        # Construct the 'all_tracts' list. This is done by concatenating the primary tract to any other included
        # or additional tracts that were selected, removing duplicates, and sorting. Note that since these are
        # array values (not well supported by Django forms...) we are stepping outside the bounds of the form
        # 'clean data' paradigm and doing some reasonable manual validation of values.
        all_tracts = [primary_tract]
    
        # Other included tracts, if any
        if len(included_tracts) > 0:
            all_tracts.extend(included_tracts)
    
        # Additional tracts, if any (get rid of spurious blank value if present...)
        if '' in additional_tracts:
            additional_tracts.pop(additional_tracts.index(''))
        if len(additional_tracts) > 0:
            all_tracts.extend(additional_tracts)
    
        # Remove any values that don't look like valid census tracts
        for tract in all_tracts:
            if len(tract) != 6 or not tract.isnumeric():
                all_tracts.pop(all_tracts.index(tract))
                log.warning("Removed invalid census tract: " + tract)
    
        # Remove duplicates and sort (primary will be moved to beginning)
        all_tracts = list(set(all_tracts))
        all_tracts.sort()
        all_tracts.insert(0, all_tracts.pop(all_tracts.index(primary_tract)))

        return (title, address, state_fips, state_name, state_short_code, county_fips, county_name, school_district,
                community, primary_tract, all_tracts, block_group, buffer_radius, population_threshold, scenario)
