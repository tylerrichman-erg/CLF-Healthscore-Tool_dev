from datetime import datetime
from django.db import models
from django.conf import settings


# Models a U.S. state
class State(models.Model):
    short_code = models.CharField(max_length=2)
    fips_code = models.CharField(max_length=2)
    name = models.CharField(max_length=32)


# Models communities of need, communities of opportunity, etc.
class Community(models.Model):
    name = models.CharField(max_length=32, unique=True)


valence_choices = (
    (1, "positive"),
    (-1, "negative")
)


# Models the manner in which various metrics affect scoring for
# different communities (i.e. "Disadvantaged" or "Advantaged")
# positive means as the metric increases, it scores more points, and
# negative means that as the metric decreases, it scores more points.
class MetricValence(models.Model):
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    metric = models.CharField(max_length=64)
    valence = models.IntegerField(default=1, null=False, choices=valence_choices)


class DataSource(models.Model):
    name = models.CharField(max_length=80)
    reference_url = models.URLField(max_length=128, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name'], name='unique name')
        ]


class Dataset(models.Model):
    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE)
    vintage = models.CharField(max_length=32)
    descriptor = models.CharField(max_length=128, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['data_source', 'vintage'], name='unique dataset')
        ]


# Models select LATCH metrics
class Latch(models.Model):
    tract_id = models.CharField(max_length=11, unique=True)
    urban_group = models.IntegerField(default=None, null=True)
    est_vmiles = models.FloatField(default=None, null=True)
    hh_cnt = models.IntegerField(default=None, null=True)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, null=True)


# Models LATCH metric est vehicle miles summarized at the state level
class NHTS(models.Model):
    fips_id = models.CharField(max_length=2, unique=True)
    est_vmiles_urban = models.FloatField(default=None, null=True)
    est_vmiles_suburban = models.FloatField(default=None, null=True)
    est_vmiles_rural = models.FloatField(default=None, null=True)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, null=True)


# Models life expectancy metric from USALEEP
class LifeExpectancy(models.Model):
    geoid = models.CharField(max_length=11, unique=True)
    value = models.FloatField(default=None, null=True)
    standard_error = models.FloatField(default=None, null=True)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, null=True)


# Models transit frequency data from EPA Smart Location
class SmartLocation(models.Model):
    block_group_id = models.CharField(max_length=12, default=None)
    D4c = models.FloatField(default=None, null=True)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, null=True)

    class Meta:
        indexes = [models.Index(fields=['dataset',])]
        constraints = [
            models.UniqueConstraint(fields=['dataset', 'block_group_id'], name='unique block group')
        ]

# Models state-level metrics for MA, CT, RI
class BRFSS(models.Model):
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    metric = models.CharField(max_length=64)
    value = models.FloatField(default=None, null=True)
    moe = models.FloatField(default=None, null=True)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, null=True)


# "New Market Tax Credit" eligibility
# see https://www.novoco.com/resource-centers/new-markets-tax-credits/data-tools/data-tables
class NMTC(models.Model):
    tract_id = models.CharField(max_length=16, null=False)
    eligible = models.BooleanField()
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, null=True)


# The classes below model state-specific education metrics
class EducationMA(models.Model):
    district = models.CharField(max_length=80)
    percentile = models.IntegerField(default=None, null=True)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, null=True)


class EducationCT(models.Model):
    district = models.CharField(max_length=80)
    percentile = models.FloatField(default=None, null=True)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, null=True)


class EducationRI(models.Model):
    district = models.CharField(max_length=80)
    group = models.CharField(max_length=80)
    star_rating = models.IntegerField(default=None, null=True)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, null=True)


class EducationMASubgroup(models.Model):
    district = models.CharField(max_length=80)
    school = models.CharField(max_length=80)
    group = models.CharField(max_length=80)
    percentile = models.IntegerField(default=None, null=True)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, null=True)


class EducationCTSubgroup(models.Model):
    district = models.CharField(max_length=80)
    subgroup = models.CharField(max_length=80)
    ela_performance_index = models.FloatField(default=None, null=True)
    math_performance_index = models.FloatField(default=None, null=True)
    science_performance_index = models.FloatField(default=None, null=True)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, null=True)


class SchoolDistrict(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, null=True)
    tract_id = models.CharField(max_length=16)
    district_name = models.CharField(max_length=80)


class OpportunityZone(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, null=True)
    geoid = models.CharField(max_length=16, unique=True)

    class Meta:
        indexes = [models.Index(fields=['geoid',])]


class Metric(models.Model):
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    geoid = models.CharField(max_length=16)
    name = models.CharField(max_length=64)
    code = models.CharField(max_length=32)
    value = models.FloatField(default=None, null=True)

    # "moe" --> margin of error
    moe = models.FloatField(default=None, null=True)

    class Meta:
        indexes = [models.Index(fields=['dataset',])]
        constraints = [
            models.UniqueConstraint(fields=['dataset', 'state', 'geoid', 'name'], name='unique metric')
        ]


class CensusTract(models.Model):
    geoid = models.CharField(max_length=16, unique=True)


class Healthscore(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date_created = models.DateTimeField(default=datetime.now)
    title = models.CharField(max_length=100, default='New score')

    address = models.CharField(max_length=80)
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    community = models.ForeignKey(Community, on_delete=models.CASCADE)
    county_code = models.CharField(max_length=4)
    county_name = models.CharField(max_length=80)
    primary_tract = models.ForeignKey(CensusTract, on_delete=models.CASCADE)
    all_tracts = models.ManyToManyField(CensusTract, related_name='healthscores')
    block_group = models.CharField(max_length=1)
    school_district = models.CharField(max_length=80)
    buffer_radius = models.FloatField(default=0.5)
    population_threshold = models.IntegerField(default=50)
    scenario = models.CharField(max_length=32, default="HNEF II")


class HousingUnitType(models.Model):
    healthscore = models.ForeignKey(Healthscore, on_delete=models.CASCADE)
    unit_type = models.CharField(max_length=128, null=False)
    unit_count = models.IntegerField(null=False)
    starting_rent = models.IntegerField(null=False)


class ChildMortality(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    state_fips = models.CharField(max_length=2, null=True)
    county_fips = models.CharField(max_length=5, null=True)
    value = models.FloatField(default=None, null=True)
    moe = models.FloatField(default=None, null=True)

    class Meta:
        indexes = [models.Index(fields=['dataset',])]
        constraints = [
            models.UniqueConstraint(fields=['dataset', 'county_fips'], name='unique mortality record')
        ]


class PersonalHealthCare(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    state_fips = models.CharField(max_length=2, null=True)
    value = models.IntegerField(default=None, null=True)


class ChildHealth(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    state_fips = models.CharField(max_length=2, null=True)
    obesity_value = models.FloatField(default=None, null=True)
    obesity_moe = models.FloatField(default=None, null=True)
    asthma_value = models.FloatField(default=None, null=True)
    asthma_moe = models.FloatField(default=None, null=True)


class ERVisits(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    state_fips = models.CharField(max_length=2, null=True)
    state_local_value = models.IntegerField(default=None, null=True)
    non_profit_value = models.IntegerField(default=None, null=True)
    for_profit_value = models.IntegerField(default=None, null=True)


class MaternityCare(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    county_fips = models.CharField(max_length=5)
    county_name = models.CharField(max_length=80)
    care_level = models.CharField(max_length=32)


class MentalHealthCare(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    state_fips = models.CharField(max_length=2, null=True)
    rank = models.IntegerField(null=False, default=0)


class HouseholdBurden(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    geoid = models.CharField(max_length=16)
    transportation_value = models.FloatField(default=None, null=True)
    energy_value = models.FloatField(default=None, null=True)
    transportation_burden = models.CharField(max_length=6, null=True)
    energy_burden = models.CharField(max_length=6, null=True)


class Homelessness(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    state_fips = models.CharField(max_length=2, null=True)
    homeless = models.IntegerField(null=False, default=0)
    population = models.IntegerField(null=False, default=0)

