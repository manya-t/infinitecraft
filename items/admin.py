from django.contrib import admin
from .models import Item, ItemPair, Transformation

class ItemAdmin(admin.ModelAdmin):
    autocomplete_fields = ['simplestWayToMake']
    search_fields = ['name']

class ItemPairAdmin(admin.ModelAdmin):
    autocomplete_fields = ['first_input', 'second_input','from_AB_C']
    search_fields = ['first_input__name', 'second_input__name']

class TransformationAdmin(admin.ModelAdmin):
    autocomplete_fields = ['input_pair', 'output']
    search_fields = ['input_pair__first_input__name', 'input_pair__second_input__name', 'output__name']


# Register your models here.
admin.site.register(Item, ItemAdmin)
admin.site.register(ItemPair, ItemPairAdmin)
admin.site.register(Transformation, TransformationAdmin)